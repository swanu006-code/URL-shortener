import os

# Must be set BEFORE importing the app, so tests never touch your real PostgreSQL data
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


@pytest.fixture(autouse=True)
def clean_db():
    """Give every test a fresh, empty database."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)