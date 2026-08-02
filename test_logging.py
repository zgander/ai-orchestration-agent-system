import logging
from app.utils.logger import get_logger

print("=== PASS 3 - ROOT LOGGER DIAGNOSTICS ===")
root_logger = logging.getLogger()
print("Root Handlers:", root_logger.handlers)
print("Root Level:", root_logger.level)
print("Root Disabled:", root_logger.disabled)
print("Root Propagate:", root_logger.propagate)

logger = get_logger("test_module")
print("=== PASS 4 - APP LOGGER DIAGNOSTICS ===")
print("App Handlers:", logger.handlers)
print("App Level:", logger.level)
print("App Propagate:", logger.propagate)
print("App Disabled:", logger.disabled)
print("Effective Level:", logger.getEffectiveLevel())

logger.info("Test log via get_logger")
logging.info("Test log via root logger")
