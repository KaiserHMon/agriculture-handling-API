from datetime import datetime

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..models.user_model import User, UserRole
from .config import get_settings

settings = get_settings()

# Auth0 configuration
AUTH0_DOMAIN = settings.AUTH0_DOMAIN
AUTH0_AUDIENCE = settings.AUTH0_AUDIENCE
AUTH0_ALGORITHMS = ["RS256"]

# Security scheme for FastAPI
security = HTTPBearer()


class Auth0Manager:
    """Handles Auth0 authentication and user management."""

    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.audience = AUTH0_AUDIENCE
        self.algorithms = AUTH0_ALGORITHMS
        self._jwks = None

    async def get_jwks(self) -> dict:
        """Fetch JSON Web Key Set from Auth0."""
        if self._jwks is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://{self.domain}/.well-known/jwks.json")
                self._jwks = response.json()
        return self._jwks

    async def verify_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Verify JWT token and return payload."""
        try:
            token = credentials.credentials
            jwks = await self.get_jwks()
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}

            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {"kty": key["kty"], "kid": key["kid"], "n": key["n"], "e": key["e"]}

            if rsa_key:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=self.algorithms,
                    audience=self.audience,
                    issuer=f"https://{self.domain}/",
                )
                return payload

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
            )

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            ) from e

    async def get_user_profile(self, access_token: str) -> dict:
        """Fetch user profile from Auth0."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.domain}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
            return response.json()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
    auth0: Auth0Manager = Depends(Auth0Manager),
) -> User:
    """Get current authenticated user."""
    payload = await auth0.verify_token(token)

    # Get or create user
    auth0_id = payload["sub"]
    query = select(User).where(User.auth0_id == auth0_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        # Fetch user profile from Auth0
        profile = await auth0.get_user_profile(token.credentials)

        # Create new user
        user = User(
            auth0_id=auth0_id,
            email=profile["email"],
            email_verified=profile.get("email_verified", False),
            full_name=profile.get("name", ""),
            picture=profile.get("picture"),
            locale=profile.get("locale"),
            role=UserRole.FARMER,
            auth0_metadata=profile,
        )
        session.add(user)
        await session.commit()

    # Update last login
    user.last_login = datetime.utcnow()
    await session.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def check_role(allowed_roles: list[UserRole]):
    """Role-based access control decorator."""

    async def role_checker(user: User = Depends(get_current_active_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted"
            )
        return user

    return role_checker
