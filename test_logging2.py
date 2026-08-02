import sys
import logging
from app.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("app.services.test")
logger.info("This is a test log")
