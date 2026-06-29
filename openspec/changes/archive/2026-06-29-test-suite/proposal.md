# Proposal: Test Suite Implementation

## Intent
Establish a robust, automated test suite to validate backend functionality, secure access controls, and assert correct external integration behaviors.

## Scope
- **In Scope**:
  - `pytest` testing infrastructure setup with an isolated in-memory SQLite database.
  - Authentication overrides mapping static tokens to database-persisted roles (`Farmer`, `Advisor`, `Admin`).
  - Access control validation: ensure Farmers only manage/view owned resources, while Advisors can create recommendations.
  - Unit mocks for Google Calendar and Weather APIs to verify correct integration and trigger logic.
- **Out of Scope**:
  - Live API testing for Auth0, Google Calendar, or Weather APIs.
  - End-to-end frontend testing.

## Capabilities
- **New**: `testing-suite`
- **Modified**: None

## Approach
1. **Infrastructure**: Implement a session-scoped async SQLite engine and transaction-rolled db session fixtures in `tests/conftest.py`.
2. **Auth Mocking**: Override FastAPI's auth dependency to return mocked user entities based on simple header values (`admin-token`, `advisor-token`, `farmer-token`).
3. **Access Control Verification**: Write test cases asserting role-based route access and ownership boundaries (e.g., access to campaigns, plots, and recommendations).
4. **Integration Mocking**: Mock Weather and Calendar service methods to assert they are invoked with expected parameters when lifecycle events trigger them.

## Affected Areas
- `tests/` directory (created).
- `tests/conftest.py` (configuration and fixtures).
- Integration points with external endpoints in API routers or services.

## Risks
- **Test Interference**: Tests modifying database state might leak across runs if transaction rollbacks are not isolated correctly.
- **Mock Drift**: Mocks might diverge from real API responses over time.

## Rollback Plan
Since the changes only introduce code within the `tests/` directory and non-production configuration, a rollback involves deleting the `tests/` directory and reverting the test dependencies in project files, causing zero production impact.

## Dependencies
- `pytest`, `pytest-asyncio`, `pytest-cov`, and `httpx` (development dependencies).

## Success Criteria
- Test coverage for main endpoints (`campaigns`, `plots`, `recommendations`, `events`).
- Mock role permissions correctly enforce and reject access rules.
- External API mocks trigger successfully during event execution.
- `uv run pytest` runs cleanly with zero failures.
