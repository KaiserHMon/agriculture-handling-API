# Tasks: Test Suite Implementation

## Review Workload Forecast
- **Expected Change Size**: ~500 lines of test code and fixtures.
- **Review Complexity**: Low to Medium. Focus is on authentication overrides and dependency isolation.
- **Critical Verification Areas**: Verify database rollback reliability across concurrent async tests, and check that Auth0 bypass mocks prevent all real HTTP traffic.

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

## Tasks

### Phase 1: Foundation
- [x] Configure development dependencies (`pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`) in `pyproject.toml`.
- [x] Create [tests/conftest.py](file:///C:/Proyectos/Api-AgricultureHandling/tests/conftest.py) to initialize an in-memory SQLite (`sqlite+aiosqlite:///:memory:`) engine and run migrations.
- [x] Implement database session fixtures using transactional rollbacks for clean state isolation.
- [x] Create FastAPI dependency overrides for `get_db` and authentication services (`get_current_user`/`get_current_active_user`).
- [x] Implement unit mocks for `GoogleCalendarClient` and weather services to intercept all external HTTP traffic.

### Phase 2: Core Endpoint Tests
- [x] Create [tests/test_auth.py](file:///C:/Proyectos/Api-AgricultureHandling/tests/test_auth.py) to assert correct mock role mapping (Farmer, Advisor, Admin) and verify unauthorized access blocks.
- [x] Create [tests/test_plots.py](file:///C:/Proyectos/Api-AgricultureHandling/tests/test_plots.py) to validate CRUD endpoints and enforce that Farmers can only access their owned plots.
- [x] Create [tests/test_campaigns.py](file:///C:/Proyectos/Api-AgricultureHandling/tests/test_campaigns.py) to assert CRUD permissions and prevent unauthorized data cross-access.

### Phase 3: Secondary Endpoint Tests
- [x] Create [tests/test_recommendations.py](file:///C:/Proyectos/Api-AgricultureHandling/tests/test_recommendations.py) to verify that Advisors can write recommendations and Farmers can view their own recommendations.
- [x] Create [tests/test_events.py](file:///C:/Proyectos/Api-AgricultureHandling/tests/test_events.py) to assert successful event creation and verify calendar sync calls.
- [x] Verify weather forecast mock triggering within notification workflows.

### Phase 4: Verification and Coverage
- [x] Execute the full test suite with `uv run pytest`.
- [x] Run statement coverage analysis targeting a minimum of 80% coverage (`uv run pytest --cov=src --cov-report=term-missing`).
- [x] Confirm zero database leakages or side-effects on the local environment.
