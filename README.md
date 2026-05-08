# Makan Society

Modern rebuild of the legacy Makan Society system.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy + Alembic
- Database: Microsoft SQL Server
- Cache/Jobs: Redis
- Local orchestration: Docker Compose

## Project Layout

```text
society-modern/
  frontend/
  backend/
  infra/
  docs/
```

## Local Services

- `frontend`: React development server
- `api`: FastAPI application
- `worker`: background worker placeholder
- `mssql`: SQL Server 2022
- `redis`: Redis

## BulkSMSBD SMS

BulkSMSBD credentials must stay server-side. React calls only the internal FastAPI routes under `/api/sms`.

Required environment variables:

```env
BULKSMSBD_API_KEY=
BULKSMSBD_SENDER_ID=
BULKSMSBD_BASE_URL=https://bulksmsbd.net/api/
BULKSMSBD_TIMEOUT_SECONDS=15
BULKSMSBD_ENABLED=false
BULKSMSBD_DRY_RUN=true
```

Keep local development safe with `BULKSMSBD_ENABLED=false` or `BULKSMSBD_DRY_RUN=true`; requests will be logged and returned as successful dry runs without spending credits. For production sending, set `BULKSMSBD_ENABLED=true`, `BULKSMSBD_DRY_RUN=false`, and provide an approved sender ID with sufficient BulkSMSBD balance.

Example backend request:

```http
POST /api/sms/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "number": "017XXXXXXXX",
  "message": "Your message"
}
```

Balance check is available at `GET /api/sms/balance`.

## Next Milestones

1. Define normalized MSSQL schema
2. Add SQLAlchemy models and Alembic migrations
3. Build auth and user management
4. Build members, packages, and billing flows
