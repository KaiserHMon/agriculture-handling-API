from typing import Generic, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from repositories.base_repository import BaseRepository

T = TypeVar("T")


class BaseService(Generic[T]):
    def __init__(self, repository: BaseRepository, db: AsyncSession):
        self.repository = repository
        self.db = db

    async def get(self, id: int) -> T:
        """
        Get an item by its ID.

        Raises:
            NotFoundError: If the item doesn't exist
            HTTPException: For database errors
        """
        try:
            item = await self.repository.get(id)
            if not item:
                raise NotFoundError(f"Item with id {id} not found")
            return item
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_all(self) -> list[T]:
        """
        Get all items.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_all()
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def create(self, data: dict) -> T:
        """
        Create a new item.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.create(data)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def update(self, id: int, data: dict) -> T:
        """
        Update an item.

        Raises:
            NotFoundError: If the item doesn't exist
            HTTPException: For database errors
        """
        try:
            item = await self.repository.update(id, data)
            if not item:
                raise NotFoundError(f"Item with id {id} not found")
            return item
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def delete(self, id: int) -> bool:
        """
        Delete an item.

        Raises:
            NotFoundError: If the item doesn't exist
            HTTPException: For database errors
        """
        try:
            if not await self.repository.delete(id):
                raise NotFoundError(f"Item with id {id} not found")
            return True
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
