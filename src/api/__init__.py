"""
FastAPI Application for LogBERT Hadoop RCA

This module contains the main FastAPI application with all routing and middleware.
"""

# Import only the main app to avoid dependency issues
from .main import app

__all__ = ["app"]

__version__ = "1.0.0"
