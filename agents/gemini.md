# Gemini Agent Project Context

This document provides essential information about the project's design, architecture, stack, commands, and key patterns for any AI agent working on the codebase.

---

## 1. Project Overview
The **Agriculture Handling API** is a FastAPI-based backend designed to manage agricultural campaigns, land plots, agricultural events (e.g., sowing, fertilizing), technical recommendations from advisors, and notifications.

### Core Technology Stack:
* **Framework**: FastAPI (async/await paradigm)
* **ORM**: SQLAlchemy 2.0 (asynchronous execution using `aiomysql` / `aiosqlite` and mapped properties)
* **Migrations**: Alembic
* **Validation**: Pydantic v2
* **Authentication**: Auth0 (OAuth2 bearer token verification + local user provisioning)
* **Logging**: Loguru + standard logging intercept

---

## 2. Project Architecture
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

---

## 3. Directory Structure Mapping

* **[src/api/v1/](file:///C:/Proyectos/Api-AgricultureHandling/src/api/v1/)**: Individual router modules (`auth_api.py`, `plot_api.py`, etc.) registered to the unified `v1_router` in `src/api/v1/__init__.py`.
* **[src/core/](file:///C:/Proyectos/Api-AgricultureHandling/src/core/)**: Config definitions, log handlers, and authentication. Auth0 verification is decoupled from DB operations; provisioning tasks are delegated to `UserService`.
* **[src/db/](file:///C:/Proyectos/Api-AgricultureHandling/src/db/)**: Contains [database.py](file:///C:/Proyectos/Api-AgricultureHandling/src/db/database.py) with session management helpers. Dependencies like `get_db` only yield sessions and do not auto-commit.
* **[src/models/](file:///C:/Proyectos/Api-AgricultureHandling/src/models/)**: Declarative SQLAlchemy models.
* **[src/schema/](file:///C:/Proyectos/Api-AgricultureHandling/src/schema/)**: Pydantic models for validation and serialization.
* **[src/repositories/](file:///C:/Proyectos/Api-AgricultureHandling/src/repositories/)**: SQL interaction layer.
* **[src/services/](file:///C:/Proyectos/Api-AgricultureHandling/src/services/)**: Business logic and transactional orchestration.
* **[src/exceptions/](file:///C:/Proyectos/Api-AgricultureHandling/src/exceptions/)**: Custom errors (`DatabaseError`, `NotFoundError`, etc.) mapped to HTTP exceptions at router level.

---

## 4. Key Commands

Run the following commands from the project root:

| Command | Action |
| :--- | :--- |
| `uv run dev` | Runs the FastAPI development server locally |
| `.venv\Scripts\python -m uvicorn src.main:app --port 8000` | Manual uvicorn execution |
| `.venv\Scripts\ruff check src` | Runs the code linter (auto-fixes syntax errors) |
| `.venv\Scripts\pytest` | Runs unit and integration test suite |

---

## 5. Architectural Conventions to Keep In Mind

* **Pydantic `@field_validator` rules**: In Pydantic v2, validators must be `@classmethod`s taking `cls` as their first parameter. Do not place imports inside Pydantic class bodies, as it registers the imported class as an un-annotated field and raises a `PydanticUserError`.
* **Imports**: Absolute imports should follow the root configuration of the `src_paths` in `pyproject.toml` (e.g. `from core.config import ...`, `from services.user_service import ...`). Relative imports must be used consistently where package structure relies on them.
* **Database CHECK Constraints**: Avoid constraints using non-deterministic database expressions (like `CURRENT_TIMESTAMP` or `NOW()`) in check constraints as they prevent table creations and break retroactive logging features.
