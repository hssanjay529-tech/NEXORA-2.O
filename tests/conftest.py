import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.models  # load all models first
from app.main import app as fastapi_app
from app.database import Base, get_db

# In-memory SQLite engine for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def override_db():
    db = TestingSessionLocal()
    fastapi_app.dependency_overrides[get_db] = lambda: db
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client():
    return TestClient(fastapi_app)
