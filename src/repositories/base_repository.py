from typing import Generic, TypeVar

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.base_model import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> T | None:
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {str(e)}")
            raise

    async def get_all(self) -> list[T]:
        try:
            query = select(self.model)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}s: {str(e)}")
            raise

    async def create(self, obj_data: dict) -> T:
        try:
            obj = self.model(**obj_data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise

    async def update(self, id: int, obj_data: dict) -> T | None:
        try:
            obj = await self.get(id)
            if not obj:
                return None

            for key, value in obj_data.items():
                setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} with id {id}: {str(e)}")
            raise

    async def delete(self, id: int) -> bool:
        try:
            obj = await self.get(id)
            if not obj:
                return False

            await self.db.delete(obj)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {str(e)}")
            raise
