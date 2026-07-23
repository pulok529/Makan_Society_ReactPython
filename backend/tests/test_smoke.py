from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal

client = TestClient(app)

def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_details():
    response = client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "up"

from sqlalchemy import text

def test_database_connection():
    # Attempt to open a database session and execute a simple query
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        db.close()
