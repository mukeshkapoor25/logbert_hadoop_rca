"""
FastAPI Application with AI Agent Integration

This module provides the main FastAPI application for the AI agent system
with a pure API interface (no web UI components).
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import router as api_router
from utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🤖 Starting LogBERT AI Agent System")
    logger.info("🌐 API available at: http://localhost:8000/api")
    logger.info("📚 API documentation at: http://localhost:8000/docs")
    logger.info("🔍 API health check at: http://localhost:8000/api/health")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down LogBERT AI Agent System")

# Create FastAPI app
app = FastAPI(
    title="LogBERT Hadoop RCA - AI Agent System",
    description="AI Agent-based Log Analysis and Root Cause Analysis for Hadoop Ecosystem",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api", tags=["AI Agents"])

# Add endpoint to handle Socket.IO requests with informative message
@app.get("/socket.io/")
@app.post("/socket.io/")
async def socket_io_info():
    """
    Information endpoint for Socket.IO requests.
    This application doesn't currently support Socket.IO real-time communication.
    """
    return {
        "error": "Socket.IO not supported",
        "message": "This API uses standard HTTP/REST endpoints only",
        "alternatives": {
            "polling": "Use GET /api/health for status checks",
            "webhooks": "Configure webhooks for event notifications (if implemented)",
            "api_docs": "Visit /docs for available endpoints"
        }
    }

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "name": "LogBERT Hadoop RCA - AI Agent System",
        "description": "AI Agent-based Log Analysis and Root Cause Analysis for Hadoop Ecosystem",
        "version": "2.0.0",
        "status": "operational",
        "api_docs": "/docs",
        "api_redoc": "/redoc",
        "api_endpoints": "/api",
        "health_check": "/api/health",
        "real_time": {
            "socketio": False,
            "websockets": False,
            "message": "Use HTTP polling for status updates"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
