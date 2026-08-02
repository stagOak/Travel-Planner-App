import logging
import sys
from pathlib import Path


def setup_logger(name: str = "app_logger", log_file: str = "app.log") -> logging.Logger:
    """Configures and returns a standardized logger instance."""
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Define standard format
    log_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / log_file)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger
