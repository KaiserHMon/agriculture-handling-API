from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from models.user_model import User, UserRole
from repositories.user_repository import UserRepository
from services.base_service import BaseService


class UserService(BaseService[User]):
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        super().__init__(self.repository, db)

    async def get_by_auth0_id(self, auth0_id: str) -> User:
        """
        Get a user by their Auth0 ID.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.get_by_auth0_id(auth0_id)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_by_email(self, email: str) -> User:
        """
        Get a user by their email.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.get_by_email(email)
            if not user:
                raise NotFoundError(f"User with email {email} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_active_users(self) -> list[User]:
        """
        Get all active users.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_active_users()
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def deactivate_user(self, auth0_id: str) -> User:
        """
        Deactivate a user.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.deactivate_user(auth0_id)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def activate_user(self, auth0_id: str) -> User:
        """
        Activate a user.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.activate_user(auth0_id)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def update_auth0_metadata(self, auth0_id: str, metadata: dict) -> User:
        """
        Update Auth0 metadata for a user.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.update_auth0_metadata(auth0_id, metadata)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def verify_email(self, auth0_id: str) -> User:
        """
        Mark a user's email as verified.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.verify_email(auth0_id)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def set_last_login(self, auth0_id: str, last_login: datetime) -> User:
        """
        Update user's last login timestamp.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors
        """
        try:
            user = await self.repository.set_last_login(auth0_id, last_login)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def update_role(self, auth0_id: str, new_role: UserRole) -> User:
        """
        Update user's role.

        Raises:
            NotFoundError: If the user doesn't exist
            HTTPException: For database errors or invalid role
        """
        try:
            user = await self.repository.update_role(auth0_id, new_role)
            if not user:
                raise NotFoundError(f"User with auth0_id {auth0_id} not found")
            return user
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_role_statistics(self) -> dict[str, int]:
        """
        Get statistics about user roles.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.count_users_by_role()
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
