import socket
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

settings = get_settings()


# Default database configuration for development with SQLite fallback
def get_database_url() -> str:
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT or 3306
    has_params = all(
        [
            settings.DB_USER,
            settings.DB_PASSWORD,
            settings.DB_HOST,
            settings.DB_PORT,
            settings.DB_NAME,
        ]
    )

    mysql_available = False
    if db_host:
        try:
            with socket.create_connection((db_host, db_port), timeout=1.0):
                mysql_available = True
        except OSError:
            pass

    if has_params and mysql_available and settings.database_url is not None:
        return settings.database_url

    print(
        "WARNING: MySQL database is not running or not configured. Falling back to SQLite local database.",
        file=sys.stderr,
    )
    return "sqlite+aiosqlite:///./agriculture_handling.db"


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
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
