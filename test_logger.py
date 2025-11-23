from config.my_logger import get_logger

logger = get_logger("test_logger", class_name="TestClass")

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
try:
    1 / 0
except Exception:
    logger.exception("This is an exception message")
