from sqlalchemy import text

from app.db.session import SessionLocal, engine


def test_sqlite_engine_connects():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_session_dependency_usable():
    session = SessionLocal()
    try:
        assert session.execute(text("SELECT 1")).scalar() == 1
    finally:
        session.close()
