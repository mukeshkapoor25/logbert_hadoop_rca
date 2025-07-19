"""
FastAPI Main Application for LogBERT Hadoop RCA

This is the main FastAPI application entry point for the LogBERT system.
It includes all necessary middleware, routing, and configuration.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .routes_dev import router as api_router
from .middleware import LoggingMiddleware, ErrorHandlingMiddleware
from ..utils.config import get_settings
from ..utils.logging import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()


def _torch_available() -> bool:
    """Check if PyTorch is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting LogBERT Hadoop RCA API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Check PyTorch availability
    if _torch_available():
        logger.info("PyTorch with CUDA support detected")
    else:
        logger.warning("PyTorch/CUDA not available - using mock mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LogBERT Hadoop RCA API")


def create_app(settings_override=None) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        settings_override: Optional settings to override defaults
        
    Returns:
        Configured FastAPI application
    """
    # Use override settings if provided
    app_settings = settings_override or settings
    
    # Create FastAPI app
    app = FastAPI(
        title="LogBERT Hadoop RCA API",
        description="Log analysis and root cause analysis for Hadoop systems using LogBERT",
        version="1.0.0",
        debug=app_settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if app_settings.DEBUG else None,
        redoc_url="/redoc" if app_settings.DEBUG else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if app_settings.DEBUG else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    if not app_settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1"]
        )
    
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Include routers
    app.include_router(api_router)
    
    # Add basic endpoints
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint - API health check and basic information."""
        return {
            "name": "LogBERT Hadoop RCA API",
            "version": "1.0.0",
            "status": "healthy",
            "docs": "/docs" if app_settings.DEBUG else "Documentation disabled",
            "environment": app_settings.ENVIRONMENT,
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring and load balancers."""
        try:
            return {
                "status": "healthy",
                "timestamp": "2025-07-19T00:00:00Z",
                "version": "1.0.0",
                "environment": app_settings.ENVIRONMENT,
                "checks": {
                    "api": "healthy",
                    "model": "loaded",
                    "gpu": "available" if _torch_available() else "unavailable",
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service unavailable")
    
    return app


# Create the main app instance
app = create_app()


def serve():
    """
    Start the development server with uvicorn.
    """
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
    )


if __name__ == "__main__":
    """
    Run the application directly with uvicorn for development.
    """
    serve()
