import logging
import time
from contextlib import contextmanager
from app.config.settings import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    return logger


@contextmanager
def time_it(logger: logging.Logger, operation: str):
    start_time = time.time()
    logger.info(f"Starting: {operation}")
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Completed: {operation} in {duration:.3f}s")
