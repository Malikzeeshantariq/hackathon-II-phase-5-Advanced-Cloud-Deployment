"""T011: JWT verification middleware.

Spec Reference: AR-001, AR-002 - Authentication Requirements
Spec Reference: research.md - JWT Implementation Details

Uses JWKS (JSON Web Key Set) to verify JWT tokens from Better Auth.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient, PyJWKClientError
from jwt.exceptions import InvalidTokenError

from app.config import get_settings

settings = get_settings()
security = HTTPBearer()

# PyJWT JWKS client - handles key fetching and caching
_jwks_client: Optional[PyJWKClient] = None


class TokenPayload:
    """Decoded JWT token payload.

    Attributes:
        user_id: User ID from JWT 'sub' claim
        email: User email from JWT 'email' claim (optional)
    """

    def __init__(self, user_id: str, email: Optional[str] = None):
        self.user_id = user_id
        self.email = email


def get_jwks_client() -> PyJWKClient:
    """Get or create the JWKS client.

    Returns:
        PyJWKClient: Client for fetching and caching JWKS keys
    """
    global _jwks_client

    if _jwks_client is None:
        jwks_url = f"{settings.BETTER_AUTH_URL}/api/auth/jwks"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)

    return _jwks_client


def verify_token(token: str) -> TokenPayload:
    """Verify JWT token and extract payload.

    Args:
        token: JWT token string

    Returns:
        TokenPayload: Decoded token payload with user_id

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        jwks_client = get_jwks_client()

        # Get the signing key from JWKS based on token's kid header
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify the token
        # PyJWT automatically handles EdDSA (Ed25519) with the crypto extra
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA", "ES256", "RS256"],  # Support multiple algorithms
            options={
                "verify_aud": False,  # Better Auth may not set audience
                "verify_iss": False,  # Better Auth may not set issuer
            }
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenPayload(
            user_id=user_id,
            email=payload.get("email")
        )
    except PyJWKClientError as e:
        print(f"JWKS client error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        print(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """Dependency to get the current authenticated user.

    Spec Reference: AR-001 - Protected routes require JWT

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        TokenPayload: Decoded token with user information

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    return verify_token(credentials.credentials)


def verify_user_access(token_user_id: str, url_user_id: str) -> None:
    """Verify that the JWT user matches the URL user_id.

    Spec Reference: AR-005 - URL user_id must match JWT user
    Spec Reference: data-model.md - Security Considerations

    Args:
        token_user_id: User ID from JWT token
        url_user_id: User ID from URL path parameter

    Raises:
        HTTPException: 403 if user IDs don't match
    """
    if token_user_id != url_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
