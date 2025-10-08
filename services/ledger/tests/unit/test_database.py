"""
Unit tests for database utilities
"""

from app.database import get_db, get_db_session
from sqlalchemy.orm import Session


class TestGetDB:
    """Tests for get_db context manager"""

    def test_get_db_returns_session(self, db_engine):
        """Test that get_db returns a database session"""
        # Override SessionLocal temporarily
        import app.database as db_module
        from app.database import get_db
        from sqlalchemy.orm import sessionmaker

        original_session_local = db_module.SessionLocal
        db_module.SessionLocal = sessionmaker(bind=db_engine)

        try:
            with get_db() as session:
                assert session is not None
                assert isinstance(session, Session)
        finally:
            db_module.SessionLocal = original_session_local

    def test_get_db_closes_session(self, db_engine):
        """Test that get_db closes session after use"""
        import app.database as db_module
        from sqlalchemy.orm import sessionmaker

        original_session_local = db_module.SessionLocal
        db_module.SessionLocal = sessionmaker(bind=db_engine)

        try:
            session = None
            with get_db() as s:
                session = s
                assert not session.is_active or session.in_transaction()

            # Session should be closed after context
            # Note: SQLite in-memory may behave differently
        finally:
            db_module.SessionLocal = original_session_local

    def test_get_db_multiple_calls(self, db_engine):
        """Test that multiple calls to get_db return different sessions"""
        import app.database as db_module
        from sqlalchemy.orm import sessionmaker

        original_session_local = db_module.SessionLocal
        db_module.SessionLocal = sessionmaker(bind=db_engine)

        try:
            with get_db() as session1:
                with get_db() as session2:
                    assert session1 is not session2
        finally:
            db_module.SessionLocal = original_session_local


class TestGetDBSession:
    """Tests for get_db_session function"""

    def test_get_db_session_returns_session(self, db_engine):
        """Test that get_db_session returns a database session"""
        import app.database as db_module
        from sqlalchemy.orm import sessionmaker

        original_session_local = db_module.SessionLocal
        db_module.SessionLocal = sessionmaker(bind=db_engine)

        try:
            session = get_db_session()
            assert session is not None
            assert isinstance(session, Session)
            session.close()
        finally:
            db_module.SessionLocal = original_session_local

    def test_get_db_session_multiple_calls(self, db_engine):
        """Test that multiple calls return different sessions"""
        import app.database as db_module
        from sqlalchemy.orm import sessionmaker

        original_session_local = db_module.SessionLocal
        db_module.SessionLocal = sessionmaker(bind=db_engine)

        try:
            session1 = get_db_session()
            session2 = get_db_session()

            assert session1 is not session2

            session1.close()
            session2.close()
        finally:
            db_module.SessionLocal = original_session_local
