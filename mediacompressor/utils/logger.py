import os
import sys
import logging
from datetime import datetime

class QueueHandler(logging.Handler):
    """Custom logging handler to send log messages to a queue for Tkinter UI."""
    def __init__(self, log_queue=None):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        if self.log_queue:
            self.log_queue.put(('LOG', msg))

def setup_logger(log_dir: str = "logs", log_queue=None) -> logging.Logger:
    """Configures thread-safe application logging."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger("MediaCompressor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )

    # Console Handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setFormatter(formatter)
    logger.addHandler(c_handler)

    # File Handler
    f_handler = logging.FileHandler(log_file, encoding="utf-8")
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)

    # UI Queue Handler
    if log_queue:
        q_handler = QueueHandler(log_queue)
        q_handler.setFormatter(formatter)
        logger.addHandler(q_handler)

    return logger
