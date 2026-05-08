from datetime import datetime, timezone

from fastapi import APIRouter

from app.db.session import database_health

router = APIRouter(tags=["system"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/details")
def health_details() -> dict[str, object]:
    database_is_up = database_health()
    return {
        "status": "ok" if database_is_up else "degraded",
        "database": "up" if database_is_up else "down",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
