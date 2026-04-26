"""
JWT authentication module.
Validates access tokens issued by Keycloak and extracts user identity.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx
import logging

from config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks_cache = None


async def get_jwks() -> dict:
    """Fetch JWKS (JSON Web Key Set) from Keycloak for JWT signature verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    jwks_url = (
        f"{settings.keycloak_url}/realms/"
        f"{settings.keycloak_realm}/protocol/openid-connect/certs"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate JWT token and return user claims.
    The user_id is extracted from the 'sub' claim.
    This ensures that a user can only access their own data.
    """
    token = credentials.credentials

    try:
        jwks = await get_jwks()

        # Get the signing key from JWKS
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if rsa_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key",
            )

        issuer_base = settings.keycloak_issuer_url or settings.keycloak_url
        issuer = f"{issuer_base}/realms/{settings.keycloak_realm}"

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience="account",
            issuer=issuer,
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user identity (sub)",
            )

        return {
            "user_id": user_id,
            "username": payload.get("preferred_username", ""),
            "email": payload.get("email", ""),
            "roles": payload.get("realm_access", {}).get("roles", []),
        }

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
