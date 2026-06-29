from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.auth import get_current_user, security
from src.db.database import get_db
from src.main import app
from src.models.base_model import Base
from src.models.user_model import User, UserRole
from src.services.user_service import UserService

try:
    from src.exceptions.api_exceptions import NotFoundError as SrcNotFoundError
except ImportError:

    class SrcNotFoundError(Exception):
        pass


try:
    from exceptions.api_exceptions import NotFoundError as DirectNotFoundError
except ImportError:

    class DirectNotFoundError(Exception):
        pass


# Stub/Mock External Clients
import sys
import types


class MockGoogleCalendarClient:
    def __init__(self):
        self.sync_event = AsyncMock(return_value=True)


class MockWeatherService:
    def __init__(self):
        self.get_forecast = AsyncMock(
            return_value={"temperature": 22.5, "precipitation": 5.0, "conditions": "rainy"}
        )


# Setup mock objects so tests can inspect call history if needed
google_calendar_mock = MockGoogleCalendarClient()
weather_service_mock = MockWeatherService()

# Intercept modules in sys.modules so imports are redirected to the mocks
weather_module = types.ModuleType("utils.weather")
weather_module.WeatherService = lambda: weather_service_mock
sys.modules["utils.weather"] = weather_module

calendar_module = types.ModuleType("utils.calendar")
calendar_module.GoogleCalendarClient = lambda: google_calendar_mock
sys.modules["utils.calendar"] = calendar_module


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine():
    # Use SQLite in-memory for isolated test DB
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    # Create all tables in the database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    # Set up connection with a transaction block
    connection = await db_engine.connect()
    transaction = await connection.begin()

    # Create session bound to connection
    async_session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session

    await transaction.rollback()
    await connection.close()


async def mock_get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security), session: AsyncSession = Depends(get_db)
) -> User:
    token_str = token.credentials
    user_service = UserService(session)

    if token_str == "admin-token":
        auth0_id = "auth0|test-admin"
        email = "admin@example.com"
        role = UserRole.ADMIN
    elif token_str == "advisor-token":
        auth0_id = "auth0|test-advisor"
        email = "advisor@example.com"
        role = UserRole.ADVISOR
    elif token_str == "farmer-token":
        auth0_id = "auth0|test-farmer"
        email = "farmer@example.com"
        role = UserRole.FARMER
    elif token_str == "farmer-token-2":
        auth0_id = "auth0|test-farmer-2"
        email = "farmer2@example.com"
        role = UserRole.FARMER
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid mock credentials"
        )

    try:
        user = await user_service.get_by_auth0_id(auth0_id)
    except (SrcNotFoundError, DirectNotFoundError):
        user_data = {
            "auth0_id": auth0_id,
            "email": email,
            "email_verified": True,
            "full_name": f"Test {role.value.capitalize()}",
            "picture": None,
            "locale": "en",
            "role": role,
            "auth0_metadata": {},
            "is_active": True,
        }
        user = await user_service.repository.create(user_data)
        await session.commit()
        await session.refresh(user)

    return user


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    async def override_get_current_user(
        token: HTTPAuthorizationCredentials = Depends(security),
        session: AsyncSession = Depends(override_get_db),
    ) -> User:
        return await mock_get_current_user(token, session)

    # Register FastAPI overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_calendar():
    google_calendar_mock.sync_event.reset_mock()
    return google_calendar_mock


@pytest.fixture
def mock_weather():
    weather_service_mock.get_forecast.reset_mock()
    return weather_service_mock
