from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...exceptions.api_exceptions import DatabaseError, NotFoundError
from ...models.user_model import User, UserRole
from ...schema.user_schema import (
    UserLoginUpdate,
    UserResponse,
    UserRoleUpdate,
)
from ...services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    """Get current authenticated user."""
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "picture": (
            current_user.picture
            if current_user.picture and current_user.picture.startswith(("http://", "https://"))
            else None
        ),
        "locale": current_user.locale,
        "email_verified": current_user.email_verified,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login,
        "auth0_id": current_user.auth0_id,
        "auth0_metadata": current_user.auth0_metadata,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }
    return UserResponse(**user_data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get user by ID. Only advisors can view other users.
    Farmers can only view themselves.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this resource",
        )

    service = UserService(db)
    try:
        return await service.get(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    """List all users. Only available to advisors."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to list all users",
        )

    service = UserService(db)
    try:
        return await service.get_active_users()
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Update a user's role. Only available to advisors.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update user roles",
        )

    service = UserService(db)
    try:
        # Get user to get auth0_id
        user = await service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return await service.update_role(user.auth0_id, role_update.role)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Deactivate a user. Only available to advisors.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate users",
        )

    service = UserService(db)
    try:
        # Get user to get auth0_id
        user = await service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return await service.deactivate_user(user.auth0_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Activate a user. Only available to advisors.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate users",
        )

    service = UserService(db)
    try:
        # Get user to get auth0_id
        user = await service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return await service.activate_user(user.auth0_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats/roles", response_model=dict[str, int])
async def get_role_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """
    Get statistics about user roles. Only available to advisors.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.ADVISOR, UserRole.FARMER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view role statistics",
        )

    service = UserService(db)
    try:
        return await service.get_role_statistics()
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{user_id}/last-login", response_model=UserResponse)
async def update_last_login(
    user_id: int,
    login_update: UserLoginUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Update user's last login time. Users can only update their own login time.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own login time",
        )

    service = UserService(db)
    try:
        return await service.set_last_login(current_user.auth0_id, login_update.last_login)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
