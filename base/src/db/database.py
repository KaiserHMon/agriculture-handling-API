from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.core.config import get_settings

settings = get_settings()


# Default database configuration for development
def get_database_url() -> str:
    if settings.database_url is not None:
        return settings.database_url

    try:
        default_config = {
            "DB_USER": "root",
            "DB_PASSWORD": SecretStr(""),  # empty password for development
            "DB_HOST": "localhost",
            "DB_PORT": 3306,
            "DB_NAME": "agriculture_dev",
        }
        return f"mysql+aiomysql://{default_config['DB_USER']}:{default_config['DB_PASSWORD'].get_secret_value()}@{default_config['DB_HOST']}:{default_config['DB_PORT']}/{default_config['DB_NAME']}"
    except Exception as e:
        raise ConnectionError(
            "Database configuration is missing and default configuration failed."
        ) from e


# Get database URL
database_url = get_database_url()

# Create async engine based on settings
engine = create_async_engine(
    database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting database sessions.

    Useful for scripts and background tasks where FastAPI dependency injection
    is not available.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
