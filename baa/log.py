import logging
import sys

LOG_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logger(level: str = "DEBUG"):
    logger = logging.getLogger("baa")
    logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    log_level = LOG_LEVEL.get(level, logging.DEBUG)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(log_formatter)

    logger.addHandler(stream_handler)
    return logger
