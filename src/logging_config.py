import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configures logging to write to a file only, with rotation.
    Removes any existing handlers (like StreamHandler) to prevent console output.
    """
    log_file = "app.log"
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    log_level = logging.INFO

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove all existing handlers (including default StreamHandler)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure RotatingFileHandler
    # maxBytes: 5MB, backupCount: 3
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Add file handler to root logger
    root_logger.addHandler(file_handler)

    # Specifically ensure 'src' and 'uvicorn' loggers follow the same configuration
    # and don't propagate to a console handler if one were to be recreated.
    for logger_name in ["src", "uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = True # Let them propagate to the root logger's file handler

    logging.info("Logging initialized. Logs are being written to %s", os.path.abspath(log_file))
