import logging

SHUTDOWN_ADDR = "shutdown.addr"
SHUTDOWN_PORT = "shutdown.port"

LOG_LEVEL = "log.level"
LOG_FORMAT = "log.format"
LOG_FILE = "log.file"

LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "WARNING"
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_CRITICAL = "CRITICAL"

log_level = {LOG_LEVEL_INFO: logging.INFO,
             LOG_LEVEL_WARNING: logging.WARNING,
             LOG_LEVEL_DEBUG: logging.DEBUG,
             LOG_LEVEL_ERROR: logging.ERROR,
             LOG_LEVEL_CRITICAL: logging.CRITICAL}

DEFAULT_LOG_FORMAT = "%(asctime)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_FILE = "./log/ibridge.log"
DEFAULT_LOGF_LEVEL = log_level[LOG_LEVEL_INFO]

DEFAULT_SHUTDOWN_ADDR = "127.0.0.1"
DEFAULT_SHUTDOWN_PORT = 9999