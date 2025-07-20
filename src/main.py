"""
FastAPI Application with AI Agent Integration

This module provides the main FastAPI application for the AI agent system
with a pure API interface (no web UI components) and Socket.IO support for real-time communication.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import socketio

from .api.routes_dev import router as api_router
from .utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # In production, specify exact origins
    logger=True,
    engineio_logger=True
)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"🔌 Socket.IO client connected: {sid}")
    await sio.emit('status', {'message': 'Connected to LogBERT AI Agent System'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"🔌 Socket.IO client disconnected: {sid}")

@sio.event
async def log_analysis_progress(sid, data):
    """Handle log analysis progress updates."""
    logger.info(f"📊 Progress update from {sid}: {data}")
    # You can broadcast progress to all connected clients or specific rooms
    await sio.emit('analysis_progress', data)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🤖 Starting LogBERT AI Agent System")
    logger.info("🌐 API available at: http://localhost:8000")
    logger.info("📚 API documentation at: http://localhost:8000/docs")
    logger.info("🔍 API health check at: http://localhost:8000/health")
    logger.info("🔌 Socket.IO server initialized for real-time communication")
    
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

# Mount Socket.IO server
socket_app = socketio.ASGIApp(sio, app)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (without prefix to match frontend expectations)
app.include_router(api_router, tags=["AI Agents"])


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
        "health_check": "/health",
        "socketio": {
            "enabled": True,
            "endpoint": "/socket.io/",
            "description": "Real-time communication for log analysis progress"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:socket_app",  # Use module path for Socket.IO support
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
