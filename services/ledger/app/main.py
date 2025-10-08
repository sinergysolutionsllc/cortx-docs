"""
CORTX Ledger Service - Append-only Event Log with Hash Chaining

Provides immutable audit trail with SHA-256 hash chain verification.
"""

import csv
import io
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc

from .database import check_db_connection, get_db, init_db
from .hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
from .models import LedgerEvent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class AppendEventRequest(BaseModel):
    """Request to append an event to the ledger"""

    tenant_id: str = Field(..., description="Tenant identifier")
    event_type: str = Field(..., description="Type of event (e.g., 'query', 'upload')")
    event_data: dict = Field(..., description="Event data (JSON)")
    user_id: Optional[str] = Field(None, description="User who triggered the event")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    description: Optional[str] = Field(None, description="Human-readable description")


class AppendEventResponse(BaseModel):
    """Response after appending an event"""

    id: str
    chain_hash: str
    created_at: str


class VerifyChainResponse(BaseModel):
    """Response from chain verification"""

    valid: bool
    total_events: int
    error: Optional[str] = None


class EventResponse(BaseModel):
    """Single event response"""

    id: str
    tenant_id: str
    event_type: str
    event_data: dict
    created_at: str
    content_hash: str
    previous_hash: str
    chain_hash: str
    user_id: Optional[str]
    correlation_id: Optional[str]
    description: Optional[str]


class EventListResponse(BaseModel):
    """List of events response"""

    events: list[EventResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# Application Lifecycle
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("ledger-svc startup: initializing database")

    # Check database connection
    if not check_db_connection():
        logger.error("Database connection failed. Service may not function correctly.")
    else:
        # Initialize database schema
        try:
            init_db()
            logger.info("Database schema initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    logger.info("ledger-svc startup complete")

    try:
        yield
    finally:
        logger.info("ledger-svc shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="CORTX Ledger Service",
    version="0.1.0",
    description="Append-only event log with SHA-256 hash chaining",
    lifespan=lifespan,
)


# ============================================================================
# Health Endpoints
# ============================================================================


@app.get("/healthz", tags=["health"])
async def healthz() -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse({"status": "ok"})


@app.get("/readyz", tags=["health"])
async def readyz() -> JSONResponse:
    """Readiness check with database status"""
    db_status = "connected" if check_db_connection() else "disconnected"

    # Get event count
    try:
        with get_db() as db:
            total_events = db.query(LedgerEvent).count()
    except Exception:
        total_events = 0

    return JSONResponse(
        {
            "status": "ready" if db_status == "connected" else "degraded",
            "database": db_status,
            "total_events": total_events,
        }
    )


# ============================================================================
# Ledger Endpoints
# ============================================================================


@app.post("/append", response_model=AppendEventResponse, tags=["ledger"])
async def append_event(request: AppendEventRequest):
    """
    Append a new event to the ledger.

    This operation:
    1. Computes content hash of event data
    2. Gets previous event's chain hash
    3. Computes new chain hash
    4. Inserts event (append-only, no updates/deletes)
    """
    try:
        with get_db() as db:
            # 1. Compute content hash
            content_hash = compute_content_hash(request.event_data)

            # 2. Get previous event's chain hash
            prev_event = (
                db.query(LedgerEvent)
                .filter(LedgerEvent.tenant_id == request.tenant_id)
                .order_by(desc(LedgerEvent.created_at))
                .first()
            )
            previous_hash = prev_event.chain_hash if prev_event else GENESIS_HASH

            # 3. Compute chain hash
            chain_hash = compute_chain_hash(content_hash, previous_hash)

            # 4. Create and insert event
            new_event = LedgerEvent(
                tenant_id=request.tenant_id,
                event_type=request.event_type,
                event_data=request.event_data,
                content_hash=content_hash,
                previous_hash=previous_hash,
                chain_hash=chain_hash,
                user_id=request.user_id,
                correlation_id=request.correlation_id,
                description=request.description,
            )

            db.add(new_event)
            db.commit()
            db.refresh(new_event)

            logger.info(
                f"Event appended: type={request.event_type}, "
                f"tenant={request.tenant_id}, id={new_event.id}"
            )

            return AppendEventResponse(
                id=str(new_event.id),
                chain_hash=new_event.chain_hash,
                created_at=new_event.created_at.isoformat(),
            )

    except Exception as e:
        logger.error(f"Failed to append event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to append event: {str(e)}")


@app.get("/verify", response_model=VerifyChainResponse, tags=["ledger"])
async def verify_chain(tenant_id: str = Query(..., description="Tenant ID to verify chain for")):
    """
    Verify the integrity of the ledger chain for a tenant.

    This operation:
    1. Retrieves all events for the tenant in order
    2. Recalculates content hash and chain hash for each event
    3. Verifies previous_hash matches previous event's chain_hash
    """
    try:
        with get_db() as db:
            events = (
                db.query(LedgerEvent)
                .filter(LedgerEvent.tenant_id == tenant_id)
                .order_by(LedgerEvent.created_at)
                .all()
            )

            if not events:
                return VerifyChainResponse(valid=True, total_events=0)

            # Verify each event
            for i, event in enumerate(events):
                # Verify content hash
                expected_content = compute_content_hash(event.event_data)
                if event.content_hash != expected_content:
                    return VerifyChainResponse(
                        valid=False,
                        total_events=len(events),
                        error=f"Content hash mismatch at event {event.id}",
                    )

                # Verify chain hash
                expected_chain = compute_chain_hash(event.content_hash, event.previous_hash)
                if event.chain_hash != expected_chain:
                    return VerifyChainResponse(
                        valid=False,
                        total_events=len(events),
                        error=f"Chain hash mismatch at event {event.id}",
                    )

                # Verify previous hash link
                if i == 0:
                    # First event should point to genesis
                    if event.previous_hash != GENESIS_HASH:
                        return VerifyChainResponse(
                            valid=False,
                            total_events=len(events),
                            error=f"First event doesn't point to genesis: {event.id}",
                        )
                else:
                    # Subsequent events should point to previous event
                    if event.previous_hash != events[i - 1].chain_hash:
                        return VerifyChainResponse(
                            valid=False,
                            total_events=len(events),
                            error=f"Chain broken at event {event.id}",
                        )

            logger.info(f"Chain verification passed for tenant {tenant_id}")
            return VerifyChainResponse(valid=True, total_events=len(events))

    except Exception as e:
        logger.error(f"Failed to verify chain: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify chain: {str(e)}")


@app.get("/events", response_model=EventListResponse, tags=["ledger"])
async def list_events(
    tenant_id: str = Query(..., description="Tenant ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List events from the ledger.

    Events are returned in reverse chronological order (newest first).
    """
    try:
        with get_db() as db:
            # Build query
            query = db.query(LedgerEvent).filter(LedgerEvent.tenant_id == tenant_id)

            if event_type:
                query = query.filter(LedgerEvent.event_type == event_type)

            if correlation_id:
                query = query.filter(LedgerEvent.correlation_id == correlation_id)

            # Get total count
            total = query.count()

            # Get paginated results
            events = query.order_by(desc(LedgerEvent.created_at)).limit(limit).offset(offset).all()

            return EventListResponse(
                events=[EventResponse(**e.to_dict()) for e in events],
                total=total,
                limit=limit,
                offset=offset,
            )

    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")


@app.get("/export", tags=["ledger"])
async def export_csv(
    tenant_id: str = Query(..., description="Tenant ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
):
    """
    Export ledger events as CSV for auditors.

    Returns a CSV file with all event fields.
    """
    try:
        with get_db() as db:
            # Build query
            query = db.query(LedgerEvent).filter(LedgerEvent.tenant_id == tenant_id)

            if event_type:
                query = query.filter(LedgerEvent.event_type == event_type)

            events = query.order_by(LedgerEvent.created_at).all()

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "tenant_id",
                    "event_type",
                    "created_at",
                    "content_hash",
                    "previous_hash",
                    "chain_hash",
                    "user_id",
                    "correlation_id",
                    "description",
                ],
            )
            writer.writeheader()

            for event in events:
                writer.writerow(
                    {
                        "id": str(event.id),
                        "tenant_id": event.tenant_id,
                        "event_type": event.event_type,
                        "created_at": event.created_at.isoformat(),
                        "content_hash": event.content_hash,
                        "previous_hash": event.previous_hash,
                        "chain_hash": event.chain_hash,
                        "user_id": event.user_id or "",
                        "correlation_id": event.correlation_id or "",
                        "description": event.description or "",
                    }
                )

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=ledger_{tenant_id}.csv"},
            )

    except Exception as e:
        logger.error(f"Failed to export events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export events: {str(e)}")
