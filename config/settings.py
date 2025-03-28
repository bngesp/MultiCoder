"""Configuration settings for the MultiCoder system.

This module contains all configuration settings that can be
customized for the MultiCoder system.
"""
import os
from typing import Dict, Any

# Redis configuration
REDIS_HOST = os.environ.get("MULTICODER_REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("MULTICODER_REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("MULTICODER_REDIS_DB", 0))
REDIS_URL = os.environ.get(
    "MULTICODER_REDIS_URL", 
    f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
)

# Channels configuration
CHANNELS = {
    "requests": "multicoder:requests",
    "responses": "multicoder:responses",
    "generator": "multicoder:generator",
    "validator": "multicoder:validator",
}

# Logging configuration
LOG_LEVEL = os.environ.get("MULTICODER_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Agent configuration
DEFAULT_TIMEOUT = int(os.environ.get("MULTICODER_DEFAULT_TIMEOUT", 60))

# Get full configuration dictionary
def get_config() -> Dict[str, Any]:
    """Get the complete configuration dictionary.
    
    Returns:
        Dictionary containing all configuration settings.
    """
    return {
        "redis": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": REDIS_DB,
            "url": REDIS_URL,
        },
        "channels": CHANNELS,
        "logging": {
            "level": LOG_LEVEL,
            "format": LOG_FORMAT,
        },
        "timeouts": {
            "default": DEFAULT_TIMEOUT,
        }
    }