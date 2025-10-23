from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient
from jose import JWTError

from ...core.auth import (
    Auth0Manager,
    get_current_active_user,
)
from ...core.config import get_settings
from ...models.user_model import User
from ...schema.auth_schema import TokenResponse, UserProfile

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth0 = Auth0Manager()


@router.get("/login")
async def login_redirect():
    """Redirect to Auth0 login page."""
    return {
        "url": f"https://{auth0.domain}/authorize",
        "params": {
            "response_type": "code",
            "client_id": settings.AUTH0_CLIENT_ID,
            "redirect_uri": "your-redirect-uri",
            "scope": "openid profile email",
            "audience": auth0.audience,
        },
    }


@router.get("/callback")
async def auth_callback(code: str) -> TokenResponse:
    """Handle Auth0 callback and return tokens."""
    try:
        # Exchange code for token
        async with AsyncClient() as client:
            response = await client.post(
                f"https://{auth0.domain}/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.AUTH0_CLIENT_ID,
                    "client_secret": settings.AUTH0_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": "your-redirect-uri",
                },
            )

            if response.status_code != 200:
                error_detail = response.json().get(
                    "error_description", "Could not validate credentials"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_detail,
                ) from None

            tokens = response.json()
            return TokenResponse(**tokens)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing the authentication",
        ) from e


@router.get("/profile", response_model=UserProfile)
async def get_profile(user: User = Depends(get_current_active_user)) -> UserProfile:
    """Get current user profile."""
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        picture=user.picture,
        email_verified=user.email_verified,
        locale=user.locale,
        last_login=user.last_login,
    )


@router.get("/verify")
async def verify_token(user: User = Depends(get_current_active_user)):
    """Verify if the current token is valid."""
    return {"valid": True, "user_id": user.id}
