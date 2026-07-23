# Society Management Software - Tech Stack

This document tracks the explicit technologies and their versions used in the modern React/Python rebuild of the Society application.

## Infrastructure
| Component | Technology | Version | Notes |
|---|---|---|---|
| **Database** | Microsoft SQL Server | `2022-latest` | Developer Edition container. `mcr.microsoft.com/mssql/server` |
| **Cache / Queue** | Redis | `7-alpine` | Lightweight alpine image |
| **Containerization** | Docker / Compose | v2+ | Separated dev (`docker-compose.yml`) and prod (`docker-compose.deploy.yml`) |
| **CI/CD** | Jenkins | LTS | Custom Jenkinsfile pipeline pulling from GitHub |
| **Source Control** | Git / GitHub | - | Repository hosted at `pulok529/Makan_Society_ReactPython` |

## Backend (Python)
Dependencies managed via `pyproject.toml`.

| Component | Package / Tech | Version | Purpose |
|---|---|---|---|
| **Language** | Python | `>=3.12` | Core backend runtime |
| **Framework** | FastAPI | `>=0.116.0` | API framework |
| **Server** | Uvicorn | `>=0.35.0` | ASGI server |
| **ORM** | SQLAlchemy | `>=2.0.43` | Database ORM |
| **Migrations** | Alembic | `>=1.16.0` | Database schema migrations |
| **DB Driver** | pyodbc | `>=5.2.0` | Microsoft ODBC Driver 18 for SQL Server |
| **Auth** | PyJWT | `>=2.10.1` | JSON Web Token encoding/decoding |
| **Config** | pydantic-settings | `>=2.10.0` | Environment variable parsing |
| **Caching** | redis | `>=6.4.0` | Python client for Redis |
| **HTTP Client**| httpx | `>=0.28.1` | Making external API calls (e.g. BulkSMSBD) |
| **Templating** | jinja2 | `>=3.1.6` | Generating HTML reports/exports |
| **Excel Export**| openpyxl | `>=3.1.5` | Generating XLSX reports |
| **Dev Tools** | pytest, ruff | `>=8.4.0, >=0.12.0`| Testing and linting/formatting |

## Frontend (React)
Dependencies managed via `package.json` and `npm`.

| Component | Package / Tech | Version | Purpose |
|---|---|---|---|
| **Language** | TypeScript | `^5.9.2` | Static typing |
| **Framework** | React | `^19.1.1` | UI Library |
| **Build Tool** | Vite | `^7.1.3` | Bundler and dev server |
| **State/Cache**| @tanstack/react-query | `^5.101.0` | API data fetching and caching |
| **CSS Framework**| Bootstrap | `^5.3.8` | Core CSS styling and grid |
| **CSS Preprocessor**| SASS | `^1.99.0` | Advanced CSS compilation |
| **Alerts/Modals**| sweetalert2 | `^11.26.25` | Popups and confirmation dialogues |
| **Testing** | vitest, @testing-library | `^3.x.x` | Unit testing and component rendering (to be implemented) |
