import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database.session import check_database_connection, get_engine
from backend.app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def postgres_available() -> bool:
    return check_database_connection()


@pytest.fixture
def db_session(postgres_available: bool) -> Session:
    if not postgres_available:
        pytest.skip("PostgreSQL is not available (start with: docker compose up -d db)")

    connection = get_engine().connect()
    transaction = connection.begin()
    session = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
