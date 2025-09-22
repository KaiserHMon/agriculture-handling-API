# Agriculture Handling API

Comprehensive API for agricultural campaign management, plots, events, and technical advisories. Automates processes, integrates notifications, and visualizes key metrics for producers, advisors, and administrators.


## Main Features

- Producers can register campaigns and plots.
- Create events (e.g., fertilization, sowing) and trigger webhooks (Google Calendar, Mock API).
- Automatic notifications via WebSocket and database.
- Advisors can leave recommendations on plots and campaigns.
- Admin dashboard for costs and yields.


## Architecture & Tech Stack

- **Backend:** FastAPI
- **ORM:** SQLAlchemy + Alembic
- **Database:** MySQL
- **Containerization:** Docker & Docker Compose
- **Authentication:** Auth0 + JWT (refresh token rotation)
- **Notifications:** WebSockets
- **Async Processing:** Celery + Redis
- **Observability:** Loguru
- **Testing:** Pytest
- **DevOps:** Pre-commit hooks (Ruff, Pyright, Black)


## Quick Installation

### Requirements
- Docker & Docker Compose
- Python 3.11+

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

- `src/` Main source code
  - `api/` Endpoints and routes
  - `core/` Configuration and utilities
  - `db/` DB connection
  - `models/`, DB tables definitions
  - `schema/` Data definitions
  - `services/`, `tasks/`, `utils/` Business logic and utilities
  - `exceptions/` Custom exceptions
  - `alembic/` DB migrations
- `tests/` Unit and integration tests
- `docs/` Technical and architecture documentation


## Testing & Best Practices

- Run tests with:
  ```bash
  pytest
  ```
- Using pre-commit config to ensure code quality (Ruff, Pyright, Black).



## Integrations & Extensions

- Webhooks for calendar and external API integration (grain prices).
- Export reports in Excel/PDF


## Contact & Credits

Developed by the Agriculture Handling team. For questions, suggestions, or collaboration, contact [your-email@domain.com].

---
This project is open source and under active development. Contributions are welcome!

Github Actions for CI/CD (even if only for test + lint).

Optional: ELK/Grafana for observability practice.
