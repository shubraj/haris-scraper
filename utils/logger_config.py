"""
Logging configuration for Harris County Property Scraper.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    log_file = logs_dir / f"harris_scraper_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_scraper_logger() -> logging.Logger:
    """
    Get the main scraper logger.
    
    Returns:
        Configured logger for scraper operations
    """
    return setup_logger("harris_scraper", "INFO")


def get_app_logger() -> logging.Logger:
    """
    Get the application logger.
    
    Returns:
        Configured logger for application operations
    """
    return setup_logger("harris_app", "INFO")


def get_utils_logger() -> logging.Logger:
    """
    Get the utilities logger.
    
    Returns:
        Configured logger for utility operations
    """
    return setup_logger("harris_utils", "INFO")


def cleanup_old_logs(days_to_keep: int = 30):
    """
    Clean up old log files.
    
    Args:
        days_to_keep: Number of days to keep log files
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    
    for log_file in logs_dir.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_date:
            try:
                log_file.unlink()
                print(f"Deleted old log file: {log_file}")
            except Exception as e:
                print(f"Error deleting {log_file}: {e}")


if __name__ == "__main__":
    # Test the logging setup
    logger = get_scraper_logger()
    logger.info("Logging setup test - INFO level")
    logger.warning("Logging setup test - WARNING level")
    logger.error("Logging setup test - ERROR level")
    logger.debug("Logging setup test - DEBUG level")
    
    print(f"Log file created at: logs/harris_scraper_{datetime.now().strftime('%Y%m%d')}.log")
