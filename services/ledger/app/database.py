"""
Database configuration and utilities for Ledger service
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "POSTGRES_URL", "postgresql://cortx:cortx_dev_password@localhost:5432/cortx"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database schema"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a new database session (for dependency injection)"""
    return SessionLocal()
