import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.db_service import VerificationService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    db.execute(
        text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            age INTEGER
        )
    """)
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()


def test_can_apply_valid_sql(db_session):
    service = VerificationService(db_session)

    ok, error = service.can_apply_to_db("INSERT INTO users (id, age) VALUES (1, 30)")

    assert ok is True
    assert error is None

    result = db_session.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
    assert result == 0  # proves rollback worked


def test_can_apply_invalid_sql(db_session):
    service = VerificationService(db_session)

    ok, error = service.can_apply_to_db("INSERT INTO missing_table (id) VALUES (1)")

    assert ok is False
    assert error is not None
