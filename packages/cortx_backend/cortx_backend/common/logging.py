import logging
import os


def setup_logging(service_name: str) -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    return logger
