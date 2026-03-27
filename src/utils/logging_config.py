"""
Logging configuration for the trading system.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_dir: Directory to store log files
        level: Logging level (default: INFO)
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_path / 'trading.log')
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Log startup
    logging.info(f"Logging configured. Log file: {log_path / 'trading.log'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
