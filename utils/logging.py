"""Logging utilities for the MultiCoder system.

This module provides logging configuration and helper functions
for consistent logging across the application.
"""
import logging
import sys
from typing import Optional


def configure_logger(
    logger_name: str,
    level: str = "INFO",
    log_format: Optional[str] = None
) -> logging.Logger:
    """Configure and return a logger with consistent formatting.
    
    Args:
        logger_name: Name for the logger.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Custom log format string.
        
    Returns:
        Configured logger instance.
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # Default format if not specified
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Add console handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger