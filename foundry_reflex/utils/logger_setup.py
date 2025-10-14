# utils/logger_setup.py
import logging
import sys
from pathlib import Path

def get_logger(name: str, log_file: str, level=logging.INFO):
    """
    Creates and configures a logger that writes to a specific file.

    Args:
        name (str): The name of the logger (e.g., 'pipeline', 'engine', 'ui').
        log_file (str): The path to the log file (e.g., 'logs/pipeline.log').
        level (int): The logging level (e.g., logging.INFO).

    Returns:
        logging.Logger: A configured logger instance.
    """
    # Ensure the logs directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)

    # Use the name to get the specific logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevents adding handlers multiple times if the function is called again
    if logger.hasHandlers():
        return logger

    # Configure handler for writing to the specified file
    file_handler = logging.FileHandler(log_path)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Configure handler for writing to the console (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    return logger