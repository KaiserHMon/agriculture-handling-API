# Agriculture Handling API

> Comprehensive API for agricultural campaign management, plots, events, and technical advisories.
> Automates processes, integrates notifications, and visualizes key metrics for producers, advisors, and administrators.

## Main Features

* Producers can register campaigns and plots.
* Create events (e.g., fertilization, sowing) and trigger webhooks (Google Calendar).
* Automatic notifications via WebSocket and database.
* Advisors can leave recommendations on plots and campaigns.
* Admin dashboard for costs and yields.


| Layer                | Technology                              |
| -------------------- | --------------------------------------- |
| **Backend**          | FastAPI                                 |
| **ORM**              | SQLAlchemy + Alembic                    |
| **Database**         | MySQL                                   |
| **Containerization** | Docker & Docker Compose                 |
| **Authentication**   | Auth0 + JWT (refresh token rotation)    |
| **Notifications**    | WebSockets                              |
| **Async Processing** | Celery + Redis                          |
| **Observability**    | Loguru                                  |
| **Testing**          | Pytest                                  |
| **DevOps**           | Pre-commit hooks (Ruff, Pyright, Black) |



## Quick Installation

### Requirements
* Docker & Docker Compose
* Python 3.11+

### Run with Docker

```bash
docker-compose up --build
```
The API will be available at [http://localhost:8000](http://localhost:8000)

### Run Locally

```bash
uv run dev
```


## Project Structure
| Folder                                      | Description                                                            |
| ------------------------------------------- | ---------------------------------------------------------------------- |
| **`src/`**                                  | Main source code of the application.                                   |
| **`routers/`**                              | API endpoints and route definitions (FastAPI routers).                 |
| **`core/`**                                 | Project configuration (settings, security, logging, middleware, etc.). |
| **`db/`**                                   | Database connection and initialization.                                |
| **`models/`**                               | ORM model definitions (database tables).                               |
| **`schemas/`**                              | Pydantic schemas for data validation and serialization (input/output). |
| **`repositories/`**                         | Data access layer (CRUD operations and persistence logic).             |
| **`services/`**, **`tasks/`**, **`utils/`** | Business logic, background tasks, and utility functions.               |
| **`exceptions/`**                           | Custom exception definitions.                                          |
| **`alembic/`**                              | Database migrations managed by Alembic.                                |
| **`tests/`**                                | Unit and integration tests.                                            |
| **`docs/`**                                 | Technical and architecture documentation.                              |


## Testing & Best Practices

### Run tests with:
  ```bash
  pytest
  ```

### Code quality is enforced with pre-commit hooks using:

* Ruff – Linting

* Pyright – Type checking

* Black – Code formatting


## Integrations & Extensions

* Webhooks for calendar and external API integration (grain prices).
* Export reports in Excel/PDF


## Contact & Credits

*Developed by Juan Segundo Hardoy. For questions, suggestions, or collaboration, contact [secondhardoy@gmail.com].*

---
