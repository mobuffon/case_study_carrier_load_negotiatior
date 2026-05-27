import os

import pytest
from fastapi.testclient import TestClient

os.environ["API_KEY"] = "test-key-123"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["LOADS_CSV_PATH"] = "app/data/loads.csv"

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-key-123"}
