import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from datetime import datetime, timedelta, UTC
import jwt
from fastapi import HTTPException
from app.core.settings import get_settings
from app.core.auth_utils import create_access_token, decode_access_token

def test_create_access_token():
    email = "test.user@uvu.edu"
    name = "Test User"
    token = create_access_token(email=email, display_name=name)
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify payload
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["email"] == email
    assert payload["name"] == name
    assert "exp" in payload

def test_decode_valid_token():
    email = "another.user@uvu.edu"
    token = create_access_token(email=email, display_name="Another User")
    payload = decode_access_token(token)
    assert payload["email"] == email
    assert payload["name"] == "Another User"

def test_decode_invalid_signature():
    email = "user@uvu.edu"
    token = create_access_token(email=email)
    
    # Tamper with the token
    tampered_token = token + "corrupted"
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(tampered_token)
    assert exc_info.value.status_code == 401
    assert "Invalid authentication token" in exc_info.value.detail

def test_decode_expired_token():
    settings = get_settings()
    # Manually create an expired token payload
    expire = datetime.now(UTC) - timedelta(hours=1)
    payload = {
        "email": "expired.user@uvu.edu",
        "name": "Expired User",
        "exp": expire
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "Session has expired" in exc_info.value.detail

def test_decode_missing_email():
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(hours=1)
    payload = {
        "name": "No Email User",
        "exp": expire
    }
    bad_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(bad_token)
    assert exc_info.value.status_code == 401
    assert "missing user email" in exc_info.value.detail

def test_decode_non_uvu_email():
    email = "hacker@gmail.com"
    token = create_access_token(email=email, display_name="Hacker")
    
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.status_code == 401
    assert "restricted to @uvu.edu domains" in exc_info.value.detail
