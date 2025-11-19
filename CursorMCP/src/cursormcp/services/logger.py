"""Structured logging setup"""

import logging
import sys
from typing import Optional
from ..config import get_settings


def setup_logging(level: Optional[str] = None) -> None:
    """Setup structured logging"""
    settings = get_settings()
    log_level = level or settings.log_level
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # MCP uses stderr for logs
        ]
    )

