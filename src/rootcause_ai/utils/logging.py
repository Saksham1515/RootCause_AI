"""
Logging configuration for RootCause AI.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Logs directory (relative to project root)
_LOGS_DIR: Path | None = None


def _get_logs_dir() -> Path:
    """Get or create the logs directory."""
    global _LOGS_DIR
    
    if _LOGS_DIR is None:
        # Try to find project root by looking for pyproject.toml
        current = Path(__file__).parent
        for _ in range(5):  # Look up to 5 levels
            if (current / "pyproject.toml").exists():
                _LOGS_DIR = current / "logs"
                break
            current = current.parent
        else:
            # Fallback to current working directory
            _LOGS_DIR = Path.cwd() / "logs"
    
    _LOGS_DIR.mkdir(exist_ok=True)
    return _LOGS_DIR


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure and return the main logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("rootcause")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    
    # File handler with detailed formatting
    logs_dir = _get_logs_dir()
    log_file = logs_dir / f"rootcause_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the given name.
    
    Args:
        name: Logger name (will be prefixed with 'rootcause.')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"rootcause.{name}")
