import os
os.environ["DATABASE_URL"] = "sqlite:///./asistia_test.db"
os.environ["SEED_DEMO_DATA"] = "true"
os.environ["AI_PROVIDER"] = "mock"
os.environ["DEV_ADMIN_EMAIL"] = "admin@asistia.example.com"
os.environ["DEV_ADMIN_PASSWORD"] = "AsistIA-demo-2026"
from fastapi.testclient import TestClient
import pytest
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
