"""T047: Authentication middleware tests.

Spec Reference: AR-001 to AR-005
Validates: Auth enforcement (SC-003, SC-004)
"""

import pytest
from jose import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.middleware.auth import verify_token, verify_user_access, TokenPayload
from fastapi import HTTPException


class TestVerifyToken:
    """Test JWT token verification."""

    def test_valid_token(self):
        """Test verification of a valid JWT token."""
        secret = "test-secret"
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.BETTER_AUTH_SECRET = secret
            result = verify_token(token)

        assert result.user_id == "user-123"
        assert result.email == "test@example.com"

    def test_expired_token(self):
        """Test rejection of expired token."""
        secret = "test-secret"
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.BETTER_AUTH_SECRET = secret
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    def test_invalid_signature(self):
        """Test rejection of token with invalid signature."""
        secret = "test-secret"
        wrong_secret = "wrong-secret"
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.BETTER_AUTH_SECRET = secret
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)

        assert exc_info.value.status_code == 401

    def test_missing_sub_claim(self):
        """Test rejection of token without sub claim."""
        secret = "test-secret"
        payload = {
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.BETTER_AUTH_SECRET = secret
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"


class TestVerifyUserAccess:
    """Test user access verification."""

    def test_matching_user_ids(self):
        """Test that matching user IDs pass verification."""
        # Should not raise
        verify_user_access("user-123", "user-123")

    def test_mismatched_user_ids(self):
        """T040: Test 403 for mismatched user IDs."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access("user-123", "user-456")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Forbidden"


class TestTokenPayload:
    """Test TokenPayload data class."""

    def test_token_payload_with_email(self):
        """Test TokenPayload with all fields."""
        payload = TokenPayload(user_id="user-123", email="test@example.com")
        assert payload.user_id == "user-123"
        assert payload.email == "test@example.com"

    def test_token_payload_without_email(self):
        """Test TokenPayload with only user_id."""
        payload = TokenPayload(user_id="user-123")
        assert payload.user_id == "user-123"
        assert payload.email is None
