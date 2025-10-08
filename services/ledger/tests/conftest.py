"""
Pytest configuration and fixtures for Ledger service tests
"""

import os
import uuid
from datetime import datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test database URL before imports
os.environ["POSTGRES_URL"] = "sqlite:///:memory:"

from app.database import get_db
from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
from app.main import app
from app.models import Base, LedgerEvent


@pytest.fixture(scope="session")
def db_engine():
    """
    Create test database engine using in-memory SQLite.

    Using SQLite for testing to avoid external dependencies.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a new database session for each test.

    Automatically rolls back after each test to ensure isolation.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    Create FastAPI test client with dependency overrides.

    Overrides the get_db dependency to use the test database.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def tenant_id() -> str:
    """Generate a test tenant ID"""
    return "test-tenant-001"


@pytest.fixture
def user_id() -> str:
    """Generate a test user ID"""
    return "test-user-001"


@pytest.fixture
def correlation_id() -> str:
    """Generate a test correlation ID"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_event_data() -> dict:
    """Sample event data for testing"""
    return {
        "action": "document_uploaded",
        "document_id": "doc-123",
        "file_name": "test.pdf",
        "file_size": 1024,
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_event_request(tenant_id, user_id, correlation_id, sample_event_data) -> dict:
    """Sample event request payload"""
    return {
        "tenant_id": tenant_id,
        "event_type": "upload",
        "event_data": sample_event_data,
        "user_id": user_id,
        "correlation_id": correlation_id,
        "description": "Test document upload event",
    }


@pytest.fixture
def ledger_event(db_session, tenant_id, sample_event_data) -> LedgerEvent:
    """
    Create a single ledger event in the database.

    This is the genesis event for testing.
    """
    content_hash = compute_content_hash(sample_event_data)
    chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

    event = LedgerEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        event_type="test_event",
        event_data=sample_event_data,
        content_hash=content_hash,
        previous_hash=GENESIS_HASH,
        chain_hash=chain_hash,
        user_id="test-user",
        correlation_id="test-correlation",
        description="Test event",
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    return event


@pytest.fixture
def ledger_chain(db_session, tenant_id) -> list[LedgerEvent]:
    """
    Create a chain of 5 ledger events for testing chain verification.

    Returns a list of events in chronological order.
    """
    events = []
    previous_hash = GENESIS_HASH

    for i in range(5):
        event_data = {
            "sequence": i,
            "action": f"action_{i}",
            "data": f"test_data_{i}",
        }

        content_hash = compute_content_hash(event_data)
        chain_hash = compute_chain_hash(content_hash, previous_hash)

        event = LedgerEvent(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            event_type=f"event_type_{i}",
            event_data=event_data,
            content_hash=content_hash,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
            user_id=f"user_{i}",
            correlation_id=f"corr_{i}",
            description=f"Event {i}",
        )

        db_session.add(event)
        events.append(event)
        previous_hash = chain_hash

    db_session.commit()

    # Refresh all events
    for event in events:
        db_session.refresh(event)

    return events


@pytest.fixture
def multi_tenant_events(db_session) -> dict[str, list[LedgerEvent]]:
    """
    Create events for multiple tenants for testing tenant isolation.

    Returns a dictionary mapping tenant_id to list of events.
    """
    tenants = {
        "tenant-a": 3,
        "tenant-b": 2,
        "tenant-c": 4,
    }

    result = {}

    for tenant_id, count in tenants.items():
        events = []
        previous_hash = GENESIS_HASH

        for i in range(count):
            event_data = {
                "tenant": tenant_id,
                "sequence": i,
                "data": f"data_{i}",
            }

            content_hash = compute_content_hash(event_data)
            chain_hash = compute_chain_hash(content_hash, previous_hash)

            event = LedgerEvent(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                event_type="test_event",
                event_data=event_data,
                content_hash=content_hash,
                previous_hash=previous_hash,
                chain_hash=chain_hash,
            )

            db_session.add(event)
            events.append(event)
            previous_hash = chain_hash

        result[tenant_id] = events

    db_session.commit()

    # Refresh all events
    for events in result.values():
        for event in events:
            db_session.refresh(event)

    return result


@pytest.fixture
def tampered_event(db_session, ledger_chain) -> LedgerEvent:
    """
    Create a tampered event by modifying event_data without updating hashes.

    This simulates data tampering for testing detection.
    """
    # Take the third event in the chain
    event = ledger_chain[2]

    # Tamper with the event data
    event.event_data["tampered"] = True

    db_session.commit()
    db_session.refresh(event)

    return event
