# Exploration Report: Test Suite Setup

This report outlines the codebase analysis and the plan for setting up the testing environment for the Agriculture Handling API. The goal is to establish a robust, isolated, and fast test suite using `pytest`, `pytest-asyncio`, and `httpx`.

---

## 1. Codebase Analysis

### FastAPI Application Routers (`src/api/v1/`)
The FastAPI application's routing structure is located under [src/api/v1/](file:///C:/Proyectos/Api-AgricultureHandling/src/api/v1/). Key routers include:
- `plot_api.py`
- `campaign_api.py`
- `auth_api.py`
- `user_api.py`

These routers consistently use FastAPI's dependency injection system (`Depends`) to acquire:
1. **Database Sessions**: `db: AsyncSession = Depends(get_db)`
2. **Current Authenticated Users**: `current_user: User = Depends(get_current_active_user)`
3. **Role Checks**: `check_role([UserRole.ADMIN, ...])`

### Database Connections (`src/db/database.py`)
- The main database engine is created asynchronously using `create_async_engine`.
- The database connection string is built dynamically via `get_database_url()`. If MySQL settings (e.g. `DB_HOST`) are not active, it defaults to `sqlite+aiosqlite:///./agriculture_handling.db`.
- The session factory is `async_sessionmaker(class_=AsyncSession, expire_on_commit=False)`.
- The `get_db` dependency yields an `AsyncSession` context-managed block:
  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with async_session_maker() as session:
          try:
              yield session
          except Exception:
              await session.rollback()
              raise
          finally:
              await session.close()
  ```

### Models (`src/models/`)
Models inherit from a shared `Base` class (inheriting from `DeclarativeBase`) defined in `src/models/base_model.py`.
- **User Role Representation**: The `UserRole` enum class (`src/models/user_model.py`) contains three main roles:
  - `farmer` (UserRole.FARMER)
  - `advisor` (UserRole.ADVISOR)
  - `admin` (UserRole.ADMIN)
- **Relationships**: A `User` has campaigns, plots, notifications, and recommendations. Relationships use SQLAlchemy's modern `Mapped[...]` types and are fully resolved during database queries.

### Authentication Helpers (`src/core/auth.py`)
- Auth0 is used for authentication. The class `Auth0Manager` verifies credentials against the Auth0 JWKS endpoint (`https://{domain}/.well-known/jwks.json`).
- `get_current_user` extracts the JWT bearer token, verifies it via `Auth0Manager.verify_token`, loads the profile (if new), maps roles via `UserService.get_or_create_from_auth0`, and returns a database `User` object.
- `get_current_active_user` asserts the user is active (`is_active` check).
- `check_role` accepts a list of roles and checks if `user.role` matches.

---

## 2. Test Suite Infrastructure Plan (`tests/conftest.py`)

To ensure test isolation and prevent modifications to the production or development databases, we will use a temporary in-memory database and override authentication.

### SQLite Async Database Integration
We will configure `pytest` to spin up an in-memory SQLite database utilizing `aiosqlite` for all tests.

1. **Session-Scoped Engine**: Set up the SQLAlchemy async engine once per test session.
2. **Schema Initialization**: Automatically create all tables on the SQLite database when the test session starts.
3. **Transaction Rollbacks**: To isolate individual tests, we will run each test in a transaction that is rolled back upon test completion, preventing state leaks.
4. **Dependency Overrides**: Override `get_db` in the FastAPI `app` object using `app.dependency_overrides`.

#### Proposed Database Fixture Strategy:
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.models.base_model import Base
from src.db.database import get_db
from src.main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def db_engine():
    # Setup test engine
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    # Function-scoped database session
    async_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()
```

---

## 3. Authentication Mocking Strategy

When executing route tests, they require an authenticated user context. Connecting to Auth0 during unit or integration testing is unacceptable due to latency, network dependencies, and security limits. We propose two approaches:

### Trade-offs: Authentication Override Options

| Mocking Option | Description | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Option 1: Direct `get_current_user` Override** | Replace FastAPI's dependency with a mock helper that parses headers or a token and maps it to a database user. | • Simplest implementation.<br>• Directly controls which `User` object is injected into the route.<br>• Bypasses `Auth0Manager` overhead. | • Bypasses internal validation inside `get_current_user` (though role checks are still executed). |
| **Option 2: Mocking `Auth0Manager`** | Override the `Auth0Manager` dependency, returning mock JWT payload and mock Auth0 profiles. | • Tests more of the authenticating code (`get_current_user`). | • Requires deeper mock integration.<br>• Fragile if Auth0 interface properties change. |

### Recommendation
**Option 1** is recommended. By reading mock token credentials from HTTP Headers (e.g. `Bearer farmer-token`, `Bearer admin-token`), we can fetch/create a user in our SQLite database matching that role, returning the actual SQLAlchemy `User` instance. This preserves the role check logic of `check_role()` and ensures database queries involving `current_user` succeed.

#### Proposed Mock implementation in `conftest.py`:
```python
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from src.core.auth import get_current_user
from src.models.user_model import User, UserRole
from src.services.user_service import UserService

async def mock_get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
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
    else:
        raise HTTPException(status_code=401, detail="Invalid mock credentials")

    try:
        user = await user_service.get_by_auth0_id(auth0_id)
    except Exception:
        # Create user in isolated test database
        user_data = {
            "auth0_id": auth0_id,
            "email": email,
            "email_verified": True,
            "full_name": f"Test {role.value.capitalize()}",
            "picture": None,
            "locale": "en",
            "role": role,
            "auth0_metadata": {},
        }
        user = await user_service.repository.create(user_data)
        await session.commit()
        await session.refresh(user)

    return user
```

This dependency override will be registered per test execution inside an `AsyncClient` client fixture:
```python
from httpx import AsyncClient

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

---

## 4. Summary & Verification Plan

### Test Command
To verify the test suite:
```bash
uv run pytest
```

### Next Implementation Steps
1. Create `tests/conftest.py` with the described SQLite setup and dependency overrides.
2. Draft basic health and role validation test files (e.g. `tests/test_auth.py`, `tests/test_plots.py`) to confirm the mocked authentication works.
