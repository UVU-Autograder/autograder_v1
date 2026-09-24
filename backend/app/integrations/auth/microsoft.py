from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
import jwt
from jwt import PyJWKClient, PyJWKClientError

from app.core.settings import get_settings


@dataclass(frozen=True)
class MicrosoftClaims:
    email: str
    display_name: str | None
    azure_oid: str | None
    tenant_id: str | None


@lru_cache(maxsize=16)
def get_jwk_client(jwks_url: str) -> PyJWKClient:
    """Retrieve or create a cached PyJWKClient for a given JWKS endpoint."""
    return PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)


def verify_microsoft_id_token(
    id_token: str,
    jwks_url: str | None = None,
    client_id: str | None = None,
    tenant_id: str | None = None,
    jwk_client: PyJWKClient | None = None,
) -> MicrosoftClaims:
    """Cryptographically verify a Microsoft Entra ID (Azure AD) ID token.

    Validates:
      1. RS256 signature against Microsoft's public JWKS.
      2. Token expiration (`exp`).
      3. Audience (`aud`) against configured client ID (fails closed if unconfigured).
      4. Tenant ID (`tid`) against configured UVU tenant ID if specified.
      5. Email domain suffix ends with `@uvu.edu`.
    """
    settings = get_settings()
    expected_client_id = client_id or settings.azure_ad_client_id
    if not expected_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: AZURE_AD_CLIENT_ID is not configured for Microsoft authentication.",
        )

    effective_tenant_id = tenant_id or settings.azure_ad_tenant_id or "common"
    effective_jwks_url = (
        jwks_url or f"https://login.microsoftonline.com/{effective_tenant_id}/discovery/v2.0/keys"
    )

    client = jwk_client or get_jwk_client(effective_jwks_url)

    try:
        signing_key = client.get_signing_key_from_jwt(id_token)
    except PyJWKClientError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to retrieve Microsoft signing key: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Microsoft token header: {str(e)}",
        )

    decode_kwargs: dict[str, Any] = {
        "algorithms": ["RS256"],
        "options": {"verify_exp": True},
        "audience": expected_client_id,
    }

    try:
        claims = jwt.decode(id_token, signing_key.key, **decode_kwargs)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft ID token has expired. Please sign in again.",
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft ID token audience does not match configured client ID.",
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft ID token issuer is invalid.",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Microsoft token: {str(e)}",
        )

    token_tid = claims.get("tid")
    expected_tenant = tenant_id or settings.azure_ad_tenant_id
    if expected_tenant and expected_tenant not in ("common", "organizations"):
        if not token_tid or token_tid != expected_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Microsoft account does not belong to authorized UVU tenant.",
            )

    email = (
        claims.get("email")
        or claims.get("preferred_username")
        or claims.get("upn")
        or ""
    ).strip().lower()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Microsoft token missing email claim.",
        )

    if not email.endswith("@uvu.edu"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only @uvu.edu Microsoft accounts are authorized.",
        )

    return MicrosoftClaims(
        email=email,
        display_name=claims.get("name"),
        azure_oid=claims.get("oid"),
        tenant_id=token_tid,
    )
