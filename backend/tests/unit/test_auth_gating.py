from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.db.base import Base
from app.domains.auth.models import Role, StaffAccess, User
from app.integrations.auth.microsoft import MicrosoftClaims
from main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    try:
        # Seed standard roles
        admin_role = Role(name="admin")
        instructor_role = Role(name="instructor")
        session.add_all([admin_role, instructor_role])
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_microsoft_login_unprovisioned_user_rejected(client):
    fake_claims = MicrosoftClaims(
        email="new.staff@uvu.edu",
        display_name="New Staff",
        azure_oid="oid-new",
        tenant_id="uvu-tenant",
    )
    with patch("app.domains.auth.router.verify_microsoft_id_token", return_value=fake_claims):
        response = client.post("/auth/microsoft-login", json={"id_token": "valid.token.here"})
        assert response.status_code == 403
        assert "pending staff authorization" in response.json()["detail"].lower()


def test_microsoft_login_inactive_user_rejected(client, db_session):
    user = User(email="inactive.staff@uvu.edu", display_name="Inactive", is_active=False)
    db_session.add(user)
    db_session.commit()

    fake_claims = MicrosoftClaims(
        email="inactive.staff@uvu.edu",
        display_name="Inactive",
        azure_oid="oid-inactive",
        tenant_id="uvu-tenant",
    )
    with patch("app.domains.auth.router.verify_microsoft_id_token", return_value=fake_claims):
        response = client.post("/auth/microsoft-login", json={"id_token": "valid.token.here"})
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()


def test_microsoft_login_user_without_roles_rejected(client, db_session):
    user = User(email="noroles.staff@uvu.edu", display_name="No Roles", is_active=True)
    db_session.add(user)
    db_session.commit()

    fake_claims = MicrosoftClaims(
        email="noroles.staff@uvu.edu",
        display_name="No Roles",
        azure_oid="oid-noroles",
        tenant_id="uvu-tenant",
    )
    with patch("app.domains.auth.router.verify_microsoft_id_token", return_value=fake_claims):
        response = client.post("/auth/microsoft-login", json={"id_token": "valid.token.here"})
        assert response.status_code == 403
        assert "no active staff roles" in response.json()["detail"].lower()


def test_microsoft_login_active_staff_success(client, db_session):
    role = db_session.query(Role).filter_by(name="instructor").first()
    user = User(email="prof.smith@uvu.edu", display_name="Prof Smith", is_active=True)
    db_session.add(user)
    db_session.flush()

    access = StaffAccess(user_id=user.id, role_id=role.id, is_active=True)
    db_session.add(access)
    db_session.commit()

    fake_claims = MicrosoftClaims(
        email="prof.smith@uvu.edu",
        display_name="Prof Smith",
        azure_oid="oid-prof-smith",
        tenant_id="uvu-tenant",
    )
    with patch("app.domains.auth.router.verify_microsoft_id_token", return_value=fake_claims):
        response = client.post("/auth/microsoft-login", json={"id_token": "valid.token.here"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "prof.smith@uvu.edu"
        assert "instructor" in data["roles"]

        # Confirm azure_oid was persisted
        db_session.refresh(user)
        assert user.azure_oid == "oid-prof-smith"


def test_mock_login_disabled_when_auth_provider_microsoft(client):
    with patch("app.core.settings.Settings.mock_login_enabled", False):
        response = client.post(
            "/auth/mock-login",
            json={"email": "dev.staff@uvu.edu", "display_name": "Dev Staff"},
        )
        assert response.status_code == 403
        assert "mock login is disabled" in response.json()["detail"].lower()


def test_mock_login_works_when_enabled(client, db_session):
    with patch("app.core.settings.Settings.mock_login_enabled", True):
        response = client.post(
            "/auth/mock-login",
            json={"email": "local.dev@uvu.edu", "display_name": "Local Dev"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


def test_microsoft_login_azure_oid_mismatch_rejected(client, db_session):
    role = db_session.query(Role).filter_by(name="instructor").first()
    user = User(
        email="prof.jones@uvu.edu",
        display_name="Prof Jones",
        azure_oid="bound-oid-original",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    access = StaffAccess(user_id=user.id, role_id=role.id, is_active=True)
    db_session.add(access)
    db_session.commit()

    fake_claims = MicrosoftClaims(
        email="prof.jones@uvu.edu",
        display_name="Prof Jones",
        azure_oid="conflicting-oid-attacker",
        tenant_id="uvu-tenant",
    )
    with patch("app.domains.auth.router.verify_microsoft_id_token", return_value=fake_claims):
        response = client.post("/auth/microsoft-login", json={"id_token": "valid.token.here"})
        assert response.status_code == 403
        assert "identity mismatch" in response.json()["detail"].lower()


def test_validate_production_security():
    from app.core.settings import Settings

    # Default secret in production mode must fail
    prod_bad_secret = Settings(
        environment="production",
        jwt_secret="dev_fallback_secret_longer_than_32_characters_for_security_compliance",
        azure_ad_client_id="some-client-id",
    )
    with pytest.raises(ValueError, match="Production mode requires an explicit"):
        prod_bad_secret.validate_production_security()

    # Missing azure_ad_client_id when auth_provider is microsoft must fail
    ms_missing_client = Settings(
        auth_provider="microsoft",
        jwt_secret="explicit_custom_production_secret_32_chars_long",
        azure_ad_client_id=None,
    )
    with pytest.raises(ValueError, match="AZURE_AD_CLIENT_ID"):
        ms_missing_client.validate_production_security()

    # Valid settings pass
    valid_settings = Settings(
        environment="production",
        auth_provider="microsoft",
        jwt_secret="explicit_custom_production_secret_32_chars_long",
        azure_ad_client_id="some-client-id",
    )
    valid_settings.validate_production_security()

