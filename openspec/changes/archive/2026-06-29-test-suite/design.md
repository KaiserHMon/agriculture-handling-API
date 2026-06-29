# Technical Design: Test Suite Implementation

## 1. Technical Approach
Establish a local, automated test suite utilizing `pytest`, `pytest-asyncio`, and `httpx`. The suite will mock external integration points and execute against an isolated database to ensure fast, deterministic feedback without production side effects.

## 2. Key Decisions
- **SQLite In-Memory Engine**: Use an isolated `sqlite+aiosqlite:///:memory:` connection for all database transactions during test runs. This guarantees a clean environment, bypasses disk I/O, and avoids conflicts with development databases.
- **FastAPI Dependency Overrides**:
  - `get_db`: Overridden with a transaction-rolled database session fixture.
  - `get_current_user` / `get_current_active_user`: Overridden to bypass live Auth0 JWT validation. Instead, the dependency intercepts requests containing predefined mock header tokens (e.g., `farmer-token`, `advisor-token`, `admin-token`) and injects matching database-persisted user models with appropriate roles (`farmer`, `advisor`, `admin`).
- **External Integration Mocking**:
  - `GoogleCalendarClient`: Mocked at the unit level using `unittest.mock` to verify that sync/create requests pass correct event parameters.
  - **Weather Notifications**: Mocked at the unit level to intercept external weather forecast queries and verify correct notification dispatch logic based on mock forecast payloads.

## 3. Data Flow
1. **Initialization**: Pytest loads session → executes database creation hooks (`Base.metadata.create_all`) on the in-memory SQLite engine.
2. **Request Dispatch**:
   - The test client sends an asynchronous HTTP request using `httpx.AsyncClient` with a mock bearer token.
   - The API router processes the request. The overridden `get_current_user` dependency maps the token to a mock database user.
   - The overridden `get_db` dependency provides an active, transaction-managed session.
3. **External Sync Trigger**: If the route triggers Google Calendar syncing or weather checks, the call is intercepted by unit mocks to assert execution arguments.
4. **Teardown**: The transaction is rolled back, restoring the in-memory database to its initial state.

## 4. File Changes
- **New Files**:
  - `tests/conftest.py`: Declares db engines, session fixtures, client initialization, dependency overrides, and mocks.
  - `tests/test_auth.py`: Tests user authentication routes and role boundaries.
  - `tests/test_campaigns.py`: Asserts campaign CRUD permissions.
  - `tests/test_plots.py`: Asserts plot ownership checks and resource access.
  - `tests/test_recommendations.py`: Asserts recommendation CRUD and advisor roles.
  - `tests/test_events.py`: Verifies event creation and Google Calendar / Weather mock dispatching.
  - `openspec/changes/test-suite/design.md`: The technical design document.

## 5. Interfaces & Mocks
- **Authentication Bypass**:
  ```python
  async def mock_get_current_user(token: str, db: AsyncSession) -> User:
      # Maps token to farmer/advisor/admin roles and upserts test user
  ```
- **External Mocks**:
  - `mock_google_calendar_client`: Replaces `GoogleCalendarClient` to assert `sync_event()` is called with appropriate payload parameters.
  - `mock_weather_service`: Simulates temperature/precipitation forecasts to assert correct triggers in notification systems.

## 6. Testing Strategy
- **Isolation**: Each test function runs within a database transaction that rolls back on completion.
- **Access Control Matrix**: Write explicit test cases verifying:
  - Farmers only manage owned resources (plots, campaigns).
  - Advisors can only issue recommendations.
  - Admins can query any resource.
- **Coverage**: Target minimum 80% statement coverage using pytest-cov. Run tests with:
  ```bash
  uv run pytest --cov=src --cov-report=term-missing
  ```

## 7. Migration & Rollback
- **Migration**: None. Since tests run against an in-memory SQLite database, no schema updates affect the live database.
- **Rollback**: Delete the `tests/` directory and revert local changes.
