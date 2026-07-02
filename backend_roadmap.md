# 🚜 Backend Roadmap: Api-AgricultureHandling

This document serves as the roadmap for finishing the backend of the **Agriculture Handling API** to make it fully operational, tested, and ready for integration with a frontend.

---

## 🗺️ Current vs. Target Architecture

The project has models, schemas, repositories, and services defined, but the orchestrating layers (routers, background workers, event triggers, real-time channels) are not wired together.

```mermaid
graph TD
    A[FastAPI Entrypoint (main.py)] --> B[API Routers (v1)]
    B --> C[Service Layer]
    C --> D[Repository Layer]
    D --> E[MySQL DB (SQLAlchemy)]
    C -.-> F[WebSocket Manager (Real-time)]
    C -.-> G[Celery Workers (Async Tasks)]
    G -.-> H[Redis Broker]
```

---

## 📋 Phase 1: API Router Registration & Database Configuration

**Goal:** Wire up all existing route controllers into the FastAPI application and ensure the DB migrations run smoothly.

- [ ] **1.1 Register Routers in [main.py](file:///C:/Proyectos/Api-AgricultureHandling/src/main.py)**
  - Register routers for:
    *   `/users` -> `user_api.py`
    *   `/campaigns` -> `campaign_api.py`
    *   `/plots` -> `plot_api.py`
    *   `/events` -> `event_api.py`
    *   `/recommendations` -> `recommendation_api.py`
    *   `/notifications` -> `notification_api.py`
  - Mount prefix `/api/v1` and ensure Swagger docs (`/docs`) can render all routers.
- [ ] **1.2 Verify database connections and Alembic**
  - Run initial Alembic migrations (`uv run alembic upgrade head`) and resolve any module resolution errors.
  - Verify tables are created properly in the MySQL container/local database.

---

## 🔑 Phase 2: Auth0 Integration & Configuration

**Goal:** Ensure the Auth0 authentication pipeline is robust, validated, and handles user roles correctly.

- [ ] **2.1 Verify Environment Configuration**
  - Ensure all required parameters (`AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`) are correctly validated inside `src/core/config.py`.
- [ ] **2.2 Map Auth0 Roles to Database Roles**
  - Implement a mechanism to sync or parse user roles (Farmer, Advisor, Admin) from Auth0 ID/Access Tokens or metadata.
  - Update `get_current_user` in `src/core/auth.py` to correctly extract and assign permissions based on Auth0 profile metadata.
- [ ] **2.3 Create a DB Seed Script for Roles**
  - Write a script to seed test users with specific roles in the local database to support development and testing.

---

## ⚡ Phase 3: SSE Real-Time Notifications

**Goal:** Complete the Server-Sent Events (SSE) infrastructure to send real-time alerts to farmers when advisors make recommendations.

- [ ] **3.1 Create SSE Manager**
  - Create an SSE connection manager (`src/core/sse.py`) to keep track of active connections associated with specific `user_id`s.
- [ ] **3.2 Implement SSE Route**
  - Expose `/sse/notifications` route inside `notification_api.py`.
  - Handle connection and authenticated handshakes (via HTTP headers).
- [ ] **3.3 Hook into Recommendation Events**
  - Trigger SSE push notifications when an advisor posts a recommendation (`recommendation_api.py`) or updates an event (`event_api.py`).

---

## ⏳ Phase 4: Celery Background Tasks

**Goal:** Setup Celery to handle async tasks such as Google Calendar syncing and fetching weather data.

- [ ] **4.1 Configure Celery & Redis**
  - Create a Celery client setup inside `src/core/celery_app.py`.
  - Define Celery tasks in the currently empty `src/tasks/` directory:
    *   `sync_google_calendar`: Mock call or actual API webhook sync for plot events.
    *   `fetch_weather_alerts`: Periodically poll mock weather services to notify farmers of severe weather on their plots.
- [ ] **4.2 Integrate Celery triggers into events**
  - Schedule calendar sync tasks asynchronously whenever a new campaign event (e.g., seeding, fertilizing) is created or deleted.

---

## 🧪 Phase 5: Testing Suite (100% Backend Coverage)

**Goal:** Setup pytest and write unit/integration tests for every endpoint.

- [ ] **5.1 Setup Test Harness**
  - Create `tests/conftest.py` with database session fixtures using SQLite in async mode (`aiosqlite`) to avoid polluting the MySQL development database.
  - Setup authentication headers helper for testing roles (Farmer, Advisor, Admin).
- [ ] **5.2 Write Endpoint Tests**
  - `test_auth.py`: Validate token generation, local auth bypass, and roles access control.
  - `test_campaigns.py`: Verify campaign creation rules (e.g. farmers cannot create campaigns for others).
  - `test_plots.py` & `test_recommendations.py`: Assert advisors can create recommendations, and farmers can view recommendations for their plots.

---

## 📄 Phase 6: External APIs Integration & Logging

**Goal:** Add final production-grade details.

- [ ] **6.1 Google Calendar and Weather Mock Utils**
  - Implement client wrappers in `src/utils/` to safely make external network calls, defaulting to mocks when APIs are unconfigured.
- [ ] **6.2 Production Logging & Validation**
  - Ensure all database rollbacks are properly logged using `loguru`.
  - Refine exceptions handling to never expose raw SQLAlchemy tracebacks.
