import logging
from src.config import config

# Convert the string log level to the corresponding logging constant
log_level = getattr(logging, config.LOG_LEVEL.upper(), None)
if log_level is None:
    raise ValueError(f"Invalid log level: {config.LOG_LEVEL}")

logging.basicConfig(level=log_level)

log = logging.getLogger("MILVUS-ADAPTER")

werkzeug_log = logging.getLogger('werkzeug')
werkzeug_log.setLevel(logging.ERROR)
