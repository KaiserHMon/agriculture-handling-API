# GEMINI.md - Agriculture Handling API Agent Guidelines & Context

This document combines project architecture, coding standards, and operational guidelines for any AI agent working on the Agriculture Handling API.

---

## 1. Project Overview & Tech Stack
The **Agriculture Handling API** is a FastAPI-based backend designed to manage agricultural campaigns, land plots, agricultural events (e.g., sowing, fertilizing), technical recommendations from advisors, and notifications.

### Core Technology Stack:
* **Framework**: FastAPI (async/await paradigm)
* **ORM**: SQLAlchemy 2.0 (asynchronous execution using `aiomysql` / `aiosqlite` and mapped properties)
* **Migrations**: Alembic
* **Validation**: Pydantic v2
* **Authentication**: Auth0 (OAuth2 bearer token verification + local user provisioning)
* **Logging**: Loguru + standard logging intercept (via `core/logging.py`)

---

## 2. Project Architecture & Conventions

The project follows a layered architecture with clear responsibilities and transaction management:

```
[FastAPI Routers] (src/api/v1)
       |
       v
[Services Layer] (src/services)     <-- Coordinates operations & controls Transaction Boundaries (commit/rollback)
       |
       v
[Repositories Layer] (src/repositories) <-- Maps queries & executes commands. Performs flush(), NEVER commit/rollback
       |
       v
[ORM Models & DB] (src/models, src/db)
```

### Transaction Boundary Rules:
1. **Repositories do not commit**: Methods in [base_repository.py](file:///C:/Proyectos/Api-AgricultureHandling/src/repositories/base_repository.py) or child repository classes must use `await self.db.flush()` rather than `commit()`. This allows multi-repository operations inside services to remain atomic.
2. **Services control transactions**: Write methods in [base_service.py](file:///C:/Proyectos/Api-AgricultureHandling/src/services/base_service.py) or child services must wrap operations in `try/except` blocks, executing `await self.db.commit()` on success, `await self.db.rollback()` on failure, and `await self.db.refresh(item)` to load generated DB values.

### Additional Architectural Conventions:
* **Pydantic `@field_validator` rules**: In Pydantic v2, validators must be `@classmethod`s taking `cls` as their first parameter. Do not place imports inside Pydantic class bodies, as it registers the imported class as an un-annotated field and raises a `PydanticUserError`.
* **Imports**: Absolute imports should follow the root configuration of the `src_paths` in `pyproject.toml` (e.g. `from core.config import ...`, `from services.user_service import ...`). Relative imports must be used consistently where package structure relies on them.
* **Database CHECK Constraints**: Avoid constraints using non-deterministic database expressions (like `CURRENT_TIMESTAMP` or `NOW()`) in check constraints as they prevent table creations and break retroactive logging features.

---

## 3. Directory Structure Mapping

Respect the existing FastAPI project structure. New files must use `snake_case` naming and be placed in the correct module/folder:

* **[src/api/v1/](file:///C:/Proyectos/Api-AgricultureHandling/src/api/v1/)**: Individual router modules registered to the unified `v1_router` in `src/api/v1/__init__.py`. Use `APIRouter` for organizing endpoints.
* **[src/core/](file:///C:/Proyectos/Api-AgricultureHandling/src/core/)**: Config definitions, log handlers, and authentication. Auth0 verification is decoupled from DB operations; provisioning tasks are delegated to `UserService`.
* **[src/db/](file:///C:/Proyectos/Api-AgricultureHandling/src/db/)**: Contains [database.py](file:///C:/Proyectos/Api-AgricultureHandling/src/db/database.py) with session management helpers. Dependencies like `get_db` only yield sessions and do not auto-commit.
* **[src/models/](file:///C:/Proyectos/Api-AgricultureHandling/src/models/)**: Declarative SQLAlchemy models.
* **[src/schema/](file:///C:/Proyectos/Api-AgricultureHandling/src/schema/)**: Pydantic models for validation and serialization. Validate all input using these models.
* **[src/repositories/](file:///C:/Proyectos/Api-AgricultureHandling/src/repositories/)**: SQL interaction layer.
* **[src/services/](file:///C:/Proyectos/Api-AgricultureHandling/src/services/)**: Business logic and transactional orchestration.
* **[src/exceptions/](file:///C:/Proyectos/Api-AgricultureHandling/src/exceptions/)**: Custom errors (`DatabaseError`, `NotFoundError`, etc.) mapped to HTTP exceptions at router level.

---

## 4. Coding Style & Rules

- **Strict Adherence**: Do only what is explicitly requested. Do not delete or change anything unless instructed. If instructions are ambiguous, ask for clarification before acting.
- **Python Style**: Follow PEP8. Use type hints for all function parameters and return values.
- **FastAPI Best Practices**:
  - Separate schemas (Pydantic) from models (SQLAlchemy).
  - Use `async/await` consistently in endpoints and database calls.
  - Handle errors with the exceptions folder and proper status codes.
  - Log using `Loguru` via `core/logging.py`.
  - Use dependency injection (`Depends`) for database sessions, authentication, etc.
- **Restrictions**:
  - Do not remove or rename existing routes, models, or services unless instructed.
  - Do not introduce new dependencies without approval.
  - Do not hardcode secrets, tokens, or credentials. Use configuration/environment variables.

---

## 5. Testing

- Add unit and integration tests (using `pytest`) for all new features.
- Update existing tests if code changes require it.
- Ensure all tests pass before completing work.
- Write descriptive test names (e.g., `test_create_user_success`).

---

## 6. Key Commands

Run the following commands from the project root:

| Command | Action |
| :--- | :--- |
| `uv run dev` | Runs the FastAPI development server locally |
| `.venv\Scripts\python -m uvicorn src.main:app --port 8000` | Manual uvicorn execution |
| `.venv\Scripts\ruff check src` | Runs the code linter (auto-fixes syntax errors) |
| `.venv\Scripts\pytest` | Runs unit and integration test suite |

---

## 7. Pre-Delivery Checklist

Before submitting your work, verify that:
- [ ] Code follows PEP8 and project conventions.
- [ ] Changes implement exactly what was requested.
- [ ] No code was deleted or altered outside of scope.
- [ ] All new features have tests.
- [ ] All tests pass (`pytest`).
- [ ] Endpoints include proper validation, error handling, logging, and responses.
- [ ] Documentation or comments were added if needed.
