import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import tempfile

os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("RESEND_API_KEY", "test")
os.environ.setdefault("NEWS_API_KEY", "test")
os.environ.setdefault("MLFLOW_TRACKING_URL", "http://localhost:5000")

from backend.app.main import app
from backend.app.core.database import Base, get_db

# Use a fresh test database by default so local dev data never leaks into tests.
fd, default_test_db = tempfile.mkstemp(suffix=".db")
os.close(fd)
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{default_test_db}")

connect_args = {"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_details():
    response = client.get("/health/details")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "database" in payload
    assert "feed" in payload
    assert "rag" in payload
    assert "scheduler" in payload


def test_subscribe_new_email():
    response = client.post("/subscribe", json={"email": "pytest_test@example.com"})
    assert response.status_code == 200
    assert "subscribed" in response.json()["message"].lower()


def test_subscribe_duplicate_email():
    client.post("/subscribe", json={"email": "duplicate@example.com"})
    response = client.post("/subscribe", json={"email": "duplicate@example.com"})
    assert response.status_code == 400


def test_subscribe_invalid_email():
    response = client.post("/subscribe", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_unsubscribe():
    client.post("/subscribe", json={"email": "unsub@example.com"})
    response = client.delete("/unsubscribe?email=unsub@example.com")
    assert response.status_code == 200


def test_unsubscribe_nonexistent():
    response = client.delete("/unsubscribe?email=ghost@example.com")
    assert response.status_code == 404
