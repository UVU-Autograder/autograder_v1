"""Authentication integrations (Microsoft Entra ID / OAuth)."""
from app.integrations.auth.microsoft import MicrosoftClaims, verify_microsoft_id_token

__all__ = ["MicrosoftClaims", "verify_microsoft_id_token"]
