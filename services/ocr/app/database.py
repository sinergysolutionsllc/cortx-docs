"""
Database configuration and session management
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "POSTGRES_URL", "postgresql://cortx:cortx_dev_password@localhost:5432/cortx"
)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """Get database session for FastAPI dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
