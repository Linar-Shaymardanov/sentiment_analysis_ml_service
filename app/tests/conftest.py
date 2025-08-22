import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

# импорт приложения и зависимости из твоего проекта
from app.api import app  # <- поправь если путь другой: у тебя раньше было app.api:app
from app.database.database import get_session

@pytest.fixture(name="session")
def session_fixture():
    # in-memory SQLite для тестов
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    # если у тебя есть аутентификация, можно переопределить её на фиктивную:
    # from app.auth.authenticate import authenticate
    # app.dependency_overrides[authenticate] = lambda: "demo@local.test"

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
