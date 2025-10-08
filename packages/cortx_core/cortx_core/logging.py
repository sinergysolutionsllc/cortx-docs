import logging
import structlog


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level))
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("cortx")
