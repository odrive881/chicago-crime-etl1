import logging
import json
import time
from datetime import datetime
from contextlib import contextmanager

LOG_FILE = "chicago_data/pipeline_log.jsonl"


class JsonlFormatter(logging.Formatter):
    """Renders each log record as a single line of JSON (JSONL)"""

    def format(self, record):
        payload = {
            "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "segment": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        duration = getattr(record, "duration_seconds", None)    #None <- a default value
        if duration is not None:
            payload["duration_seconds"] = round(duration, 3)

        details = getattr(record, "details", None)
        if details:
            payload["details"] = details

        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def get_logger(segment_name):
    """Returns a logger for a specific pipeline segment"""
    logger = logging.getLogger(segment_name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(JsonlFormatter())
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(console_handler)

        logger.propagate = False

    return logger


@contextmanager
def timed_segment(logger, segment_label):
    """Context manager that times and logs a pipeline segment"""
    start = time.perf_counter()
    details = {}
    logger.info(f"{segment_label} started")

    try:
        yield details
    except Exception as e:
        elapsed = time.perf_counter() - start
        details["error"] = str(e)
        logger.error(
            f"{segment_label} failed",
            extra={"duration_seconds": elapsed, "details": details},
        )
        raise
    else:
        elapsed = time.perf_counter() - start
        logger.info(
            f"{segment_label} complete",
            extra={"duration_seconds": elapsed, "details": details or None},
        )
