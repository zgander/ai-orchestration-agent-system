import logging
import time
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import deque
from app.config.settings import settings


class StructuredLogStore:
    _instance = None
    _logs: deque = deque(maxlen=1000)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_log(self, record: logging.LogRecord):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "category": self._determine_category(record.name)
        }
        self._logs.append(log_entry)

    def _determine_category(self, name: str) -> str:
        if "investigation" in name: return "investigation"
        if "chat" in name: return "chat"
        if "review" in name: return "review"
        if "cache" in name: return "cache"
        if "tool" in name: return "tool"
        if "llm" in name: return "llm"
        return "general"

    def get_logs(self, category: str = "All", level: str = "All") -> List[Dict[str, Any]]:
        filtered = list(self._logs)
        if category != "All":
            filtered = [log for log in filtered if log["category"] == category]
        if level != "All":
            filtered = [log for log in filtered if log["level"] == level]
        return filtered


class StructuredLogHandler(logging.Handler):
    def emit(self, record):
        StructuredLogStore.get_instance().add_log(record)


def setup_logging():
    """Configure the central 'app' logger once."""
    import sys
    app_logger = logging.getLogger("app")
    app_logger.propagate = False  # Prevent bubbling up to root where Streamlit might interfere
    
    # Clear existing handlers to prevent duplicates on Streamlit reruns
    app_logger.handlers.clear()
    
    # Use sys.__stderr__ to bypass Streamlit's stdout/stderr interception
    console_handler = logging.StreamHandler(sys.__stderr__)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)
    
    struct_handler = StructuredLogHandler()
    app_logger.addHandler(struct_handler)
    
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    app_logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
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
