"""
Database connection and session management for RAG service.
"""

import os
from typing import Generator

from app.models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv(
    "POSTGRES_URL", "postgresql://cortx:cortx_dev_password@127.0.0.1:5432/cortx"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    echo=False,  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database schema.

    Creates:
    - 'rag' schema
    - All tables defined in models.py
    - pgvector extension
    - Required indexes
    """
    with engine.begin() as conn:
        # Create pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create pg_trgm extension for fuzzy text search
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

        # Create rag schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS rag"))

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ Database schema initialized successfully")


def drop_db() -> None:
    """
    Drop all tables (DANGEROUS - use only in development).
    """
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS rag CASCADE"))

    print("⚠️  Database schema dropped")


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
