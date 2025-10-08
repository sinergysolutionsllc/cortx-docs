from .logging import logger
from .models import AuditEvent


async def emit_audit(event: AuditEvent) -> None:
    logger.info("audit.event", **event.model_dump())
