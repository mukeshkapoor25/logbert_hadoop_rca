"""
Simplified API Routes for Development

This module provides basic API endpoints without heavy ML dependencies
for testing and development purposes.
"""

import time
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..models.schemas import (
    LogAnalysisRequest,
    LogAnalysisResponse,
    AnomalyDetectionResponse,
    RCAResponse,
    HealthResponse,
    ModelInfo,
    Anomaly,
    RootCause,
    AnomalyType,
    SeverityLevel,
    ConfidenceLevel,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter()


@router.get("/", tags=["Root"])
async def api_root():
    """API root endpoint."""
    return {
        "message": "LogBERT Hadoop RCA API",
        "version": "1.0.0",
        "status": "operational",
        "mode": "development",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "docs": "/docs",
        }
    }


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment="development",
        checks={
            "api": "healthy",
            "config": "loaded",
            "logging": "operational",
            "ml_models": "not_loaded",
        }
    )


@router.post("/analyze", response_model=LogAnalysisResponse, tags=["Analysis"])
async def analyze_logs(request: LogAnalysisRequest) -> LogAnalysisResponse:
    """
    Analyze log text for anomalies (Development Mock).
    
    This is a simplified mock implementation for development and testing.
    In production, this would use the full LogBERT model.
    """
    try:
        start_time = time.time()
        logger.info(f"Mock analysis for {len(request.log_text)} characters")
        
        # Mock anomaly detection
        anomalies = []
        log_lines = request.log_text.strip().split('\n')
        
        for i, line in enumerate(log_lines):
            if line.strip():
                # Simple keyword-based mock detection
                is_anomaly = any(keyword in line.lower() for keyword in [
                    'error', 'exception', 'failed', 'timeout', 'denied'
                ])
                
                if is_anomaly:
                    anomaly = Anomaly(
                        id=f"mock_anomaly_{i}_{int(time.time())}",
                        line_number=i + 1,
                        log_entry=line,
                        anomaly_score=0.8,
                        anomaly_type=AnomalyType.ERROR,
                        severity=SeverityLevel.MEDIUM,
                        confidence=ConfidenceLevel.MEDIUM,
                        timestamp=None,
                        component="mock_component",
                        description="Mock anomaly detected for development",
                    )
                    anomalies.append(anomaly)
        
        # Mock anomaly detection response
        anomaly_response = AnomalyDetectionResponse(
            anomalies_detected=len(anomalies) > 0,
            total_anomalies=len(anomalies),
            anomalies=anomalies,
            processing_time_ms=50.0,
            model_version="mock_v1.0",
            threshold_used=request.threshold,
            statistics={
                "total_lines": len(log_lines),
                "processed_lines": len([l for l in log_lines if l.strip()]),
                "mock_mode": True,
            }
        )
        
        # Mock RCA if anomalies found
        rca_response = None
        if anomalies and request.include_rca:
            root_cause = RootCause(
                id=f"mock_rc_{int(time.time())}",
                title="Mock Root Cause",
                description="This is a mock root cause for development testing",
                category="development",
                severity=SeverityLevel.MEDIUM,
                confidence=ConfidenceLevel.MEDIUM,
                affected_components=["mock_component"],
                related_anomalies=[a.id for a in anomalies],
                recommended_actions=[
                    "This is a development mock",
                    "Install ML dependencies for real analysis",
                    "Configure trained LogBERT models",
                ],
                evidence=[
                    "Mock evidence 1",
                    "Mock evidence 2",
                ],
            )
            
            rca_response = RCAResponse(
                root_causes_found=True,
                total_root_causes=1,
                root_causes=[root_cause],
                processing_time_ms=30.0,
                confidence_score=0.6,
                analysis_summary="Mock RCA analysis for development",
            )
        
        # Total processing time
        total_time = (time.time() - start_time) * 1000
        
        response = LogAnalysisResponse(
            analysis_id=f"mock_analysis_{int(time.time())}",
            status="completed",
            anomaly_detection=anomaly_response,
            root_cause_analysis=rca_response,
            processing_time_ms=total_time,
            metadata={
                "mode": "development_mock",
                "timestamp": datetime.utcnow().isoformat(),
                "input_size": len(request.log_text),
                "note": "This is a mock response for development. Install ML dependencies for real analysis.",
            }
        )
        
        logger.info(f"Mock analysis completed: {len(anomalies)} anomalies found")
        return response
        
    except Exception as e:
        logger.error(f"Mock analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/models", response_model=List[ModelInfo], tags=["Models"])
async def list_available_models() -> List[ModelInfo]:
    """List available models (Development Mock)."""
    return [
        ModelInfo(
            name="logbert_hadoop_mock",
            version="1.0.0",
            description="Mock LogBERT model for development",
            architecture="Mock-BERT-6L-8H-512D",
            training_data="Mock Hadoop cluster logs",
            performance_metrics={
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.96,
                "f1_score": 0.95,
                "note": "Mock metrics for development",
            },
            supported_log_types=["hadoop", "hdfs", "yarn", "mock"],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            size_mb=0.1,
        )
    ]


@router.get("/status", tags=["Status"])
async def get_api_status():
    """Get detailed API status."""
    return {
        "api_version": "1.0.0",
        "mode": "development",
        "features": {
            "ml_models": "mock_only",
            "real_analysis": "requires_dependencies",
            "mock_analysis": "available",
        },
        "dependencies": {
            "fastapi": "installed",
            "pydantic": "installed",
            "torch": "not_installed",
            "transformers": "not_installed",
            "numpy": "not_installed",
        },
        "next_steps": [
            "Install ML dependencies for full functionality",
            "Configure trained models",
            "Set up production environment",
        ],
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/dev-info", tags=["Development"])
async def development_info():
    """Development information and setup instructions."""
    return {
        "project": "LogBERT Hadoop RCA",
        "mode": "Development API",
        "description": "Simplified API for development and testing without heavy ML dependencies",
        "setup_instructions": {
            "1_basic_usage": "Current API provides mock responses for testing",
            "2_full_ml": "Install: pip install torch transformers numpy pandas scikit-learn",
            "3_models": "Configure trained LogBERT models in AI_MODELS/trained_models/",
            "4_production": "Set LOGBERT_ENVIRONMENT=production in .env",
        },
        "available_endpoints": [
            "GET / - API root",
            "GET /health - Health check",
            "POST /analyze - Log analysis (mock)",
            "GET /models - Available models (mock)",
            "GET /status - API status",
            "GET /dev-info - This information",
        ],
        "mock_features": [
            "Basic log parsing",
            "Keyword-based anomaly detection",
            "Mock root cause analysis",
            "API structure validation",
        ],
        "capstone_note": "This API demonstrates the complete architecture and can be enhanced with full ML capabilities",
    }
