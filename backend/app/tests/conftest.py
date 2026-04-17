import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.models.project import Project, File, CodeNode, CodeEdge
from app.database import get_session as db_gs

_test_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(_test_engine)


def _get_test_session():
    with Session(_test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture():
    from app.main import app

    app.dependency_overrides[db_gs] = _get_test_session
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()
