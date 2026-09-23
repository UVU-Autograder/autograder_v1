from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
import jwt
import pytest

from app.integrations.auth.microsoft import verify_microsoft_id_token


@pytest.fixture(scope="module")
def rsa_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def mock_jwk_client(rsa_keypair):
    _, public_key = rsa_keypair
    mock_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
    return mock_client


def _generate_token(
    private_key,
    email="test.instructor@uvu.edu",
    name="Test Instructor",
    oid="azure-oid-12345",
    tid="uvu-tenant-id",
    aud="uvu-client-id",
    exp_minutes=60,
    headers=None,
):
    headers = headers or {"kid": "test-key-id"}
    now = datetime.now(UTC)
    payload = {
        "email": email,
        "name": name,
        "oid": oid,
        "tid": tid,
        "aud": aud,
        "iss": f"https://login.microsoftonline.com/{tid}/v2.0",
        "exp": now + timedelta(minutes=exp_minutes),
        "iat": now,
        "nbf": now,
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)


def test_verify_valid_microsoft_id_token(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    token = _generate_token(private_key)

    claims = verify_microsoft_id_token(
        token,
        jwk_client=mock_jwk_client,
        client_id="uvu-client-id",
        tenant_id="uvu-tenant-id",
    )

    assert claims.email == "test.instructor@uvu.edu"
    assert claims.display_name == "Test Instructor"
    assert claims.azure_oid == "azure-oid-12345"
    assert claims.tenant_id == "uvu-tenant-id"


def test_verify_token_expired(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    token = _generate_token(private_key, exp_minutes=-10)

    with pytest.raises(HTTPException) as exc_info:
        verify_microsoft_id_token(
            token,
            jwk_client=mock_jwk_client,
            client_id="uvu-client-id",
            tenant_id="uvu-tenant-id",
        )
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_verify_token_audience_mismatch(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    token = _generate_token(private_key, aud="wrong-client-id")

    with pytest.raises(HTTPException) as exc_info:
        verify_microsoft_id_token(
            token,
            jwk_client=mock_jwk_client,
            client_id="uvu-client-id",
            tenant_id="uvu-tenant-id",
        )
    assert exc_info.value.status_code == 401
    assert "audience" in exc_info.value.detail.lower()


def test_verify_token_tenant_mismatch(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    token = _generate_token(private_key, tid="foreign-tenant-id")

    with pytest.raises(HTTPException) as exc_info:
        verify_microsoft_id_token(
            token,
            jwk_client=mock_jwk_client,
            client_id="uvu-client-id",
            tenant_id="uvu-tenant-id",
        )
    assert exc_info.value.status_code == 403
    assert "tenant" in exc_info.value.detail.lower()


def test_verify_non_uvu_email_rejected(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    token = _generate_token(private_key, email="intruder@gmail.com")

    with pytest.raises(HTTPException) as exc_info:
        verify_microsoft_id_token(
            token,
            jwk_client=mock_jwk_client,
            client_id="uvu-client-id",
            tenant_id="uvu-tenant-id",
        )
    assert exc_info.value.status_code == 403
    assert "@uvu.edu" in exc_info.value.detail


def test_verify_fallback_preferred_username(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    now = datetime.now(UTC)
    payload = {
        "preferred_username": "faculty@uvu.edu",
        "name": "Faculty Member",
        "oid": "faculty-oid-999",
        "tid": "uvu-tenant-id",
        "aud": "uvu-client-id",
        "exp": now + timedelta(minutes=30),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "key-1"})

    claims = verify_microsoft_id_token(
        token,
        jwk_client=mock_jwk_client,
        client_id="uvu-client-id",
        tenant_id="uvu-tenant-id",
    )
    assert claims.email == "faculty@uvu.edu"


def test_verify_unconfigured_client_id_fails_closed(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    token = _generate_token(private_key)

    with pytest.raises(HTTPException) as exc_info:
        verify_microsoft_id_token(
            token,
            jwk_client=mock_jwk_client,
            client_id=None,
            tenant_id="uvu-tenant-id",
        )
    assert exc_info.value.status_code == 500
    assert "AZURE_AD_CLIENT_ID" in exc_info.value.detail


def test_verify_missing_tid_rejected_when_tenant_expected(rsa_keypair, mock_jwk_client):
    private_key, _ = rsa_keypair
    now = datetime.now(UTC)
    payload = {
        "email": "faculty@uvu.edu",
        "name": "Faculty Member",
        "oid": "faculty-oid-999",
        "aud": "uvu-client-id",
        "exp": now + timedelta(minutes=30),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "key-1"})

    with pytest.raises(HTTPException) as exc_info:
        verify_microsoft_id_token(
            token,
            jwk_client=mock_jwk_client,
            client_id="uvu-client-id",
            tenant_id="uvu-tenant-id",
        )
    assert exc_info.value.status_code == 403
    assert "tenant" in exc_info.value.detail.lower()

