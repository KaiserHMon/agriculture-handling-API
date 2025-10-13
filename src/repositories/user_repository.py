from datetime import datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import User, UserRole
from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_auth0_id(self, auth0_id: str) -> User | None:
        try:
            query = select(self.model).where(self.model.auth0_id == auth0_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting User with auth0_id {auth0_id}: {str(e)}")
            raise

    async def get_by_email(self, email: str) -> User | None:
        try:
            query = select(self.model).where(self.model.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting User with email {email}: {str(e)}")
            raise

    async def get_active_users(self) -> list[User]:
        try:
            query = select(self.model).where(self.model.is_active)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting active Users: {str(e)}")
            raise

    async def deactivate_user(self, auth0_id: str) -> User | None:
        try:
            user = await self.get_by_auth0_id(auth0_id)
            if not user:
                return None

            user.is_active = False
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deactivating User with auth0_id {auth0_id}: {str(e)}")
            raise

    async def activate_user(self, auth0_id: str) -> User | None:
        try:
            user = await self.get_by_auth0_id(auth0_id)
            if not user:
                return None

            user.is_active = True
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error activating User with auth0_id {auth0_id}: {str(e)}")
            raise

    async def update_auth0_metadata(self, auth0_id: str, metadata: dict) -> User | None:
        try:
            user = await self.get_by_auth0_id(auth0_id)
            if not user:
                return None

            user.auth0_metadata = metadata
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(
                f"Error updating auth0_metadata for User with auth0_id {auth0_id}: {str(e)}"
            )
            raise

    async def verify_email(self, auth0_id: str) -> User | None:
        try:
            user = await self.get_by_auth0_id(auth0_id)
            if not user:
                return None

            user.email_verified = True
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error verifying email for User with auth0_id {auth0_id}: {str(e)}")
            raise

    async def set_last_login(self, auth0_id: str, last_login: datetime) -> User | None:
        try:
            user = await self.get_by_auth0_id(auth0_id)
            if not user:
                return None

            user.last_login = last_login
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error setting last_login for User with auth0_id {auth0_id}: {str(e)}")
            raise

    async def update_role(self, auth0_id: str, new_role: UserRole) -> User | None:
        try:
            user = await self.get_by_auth0_id(auth0_id)
            if not user:
                return None

            user.role = new_role
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating role for User with auth0_id {auth0_id}: {str(e)}")
            raise

    async def count_users_by_role(self) -> dict[str, int]:
        """Get count of users by role."""
        try:
            query = select(self.model.role, func.count()).group_by(self.model.role)
            result = await self.db.execute(query)
            return {str(role): int(count) for role, count in result.all()}
        except SQLAlchemyError as e:
            logger.error(f"Error counting users by role: {str(e)}")
            raise


class FarmerRepository(UserRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_farmers(self) -> list[User]:
        try:
            query = select(self.model).where(self.model.role == UserRole.FARMER)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting farmers: {str(e)}")
            raise


class AdvisorRepository(UserRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_advisors(self) -> list[User]:
        try:
            query = select(self.model).where(self.model.role == UserRole.ADVISOR)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting advisors: {str(e)}")
            raise
