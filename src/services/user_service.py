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
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except DatabaseError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            await self.db.rollback()
            raise e

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
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except DatabaseError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            await self.db.rollback()
            raise e

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
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except DatabaseError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            await self.db.rollback()
            raise e

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
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except DatabaseError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            await self.db.rollback()
            raise e

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
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except DatabaseError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            await self.db.rollback()
            raise e

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
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except DatabaseError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            await self.db.rollback()
            raise e

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

    def _map_roles(self, roles: list[str]) -> UserRole:
        if not roles:
            return UserRole.FARMER
        roles_lower = [r.lower() for r in roles]
        if any("admin" in r for r in roles_lower):
            return UserRole.ADMIN
        if any("advisor" in r or "asesor" in r for r in roles_lower):
            return UserRole.ADVISOR
        if any("farmer" in r or "productor" in r for r in roles_lower):
            return UserRole.FARMER
        return UserRole.FARMER

    async def get_or_create_from_auth0(
        self, auth0_id: str, profile_loader_fn, roles: list[str] | None = None
    ) -> User:
        """
        Get an existing user or create a one using the profile loaded from Auth0,
        map roles and update roles for returning users if changed, and update their last login.
        """
        if roles is None:
            roles = []

        mapped_role = self._map_roles(roles)

        try:
            try:
                user = await self.repository.get_by_auth0_id(auth0_id)
            except Exception:
                user = None

            if not user:
                profile = await profile_loader_fn()

                user_data = {
                    "auth0_id": auth0_id,
                    "email": profile["email"],
                    "email_verified": profile.get("email_verified", False),
                    "full_name": profile.get("name", ""),
                    "picture": profile.get("picture"),
                    "locale": profile.get("locale"),
                    "role": mapped_role,
                    "auth0_metadata": profile,
                }
                user = await self.repository.create(user_data)
            else:
                # Update role for returning users if changed
                if user.role != mapped_role:
                    user.role = mapped_role

            user.last_login = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
