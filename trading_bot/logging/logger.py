import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger = logging.getLogger("trading_bot")
logger.setLevel(LOG_LEVEL)

ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)

formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
ch.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(ch)

# TODO: Extend for audit logging
