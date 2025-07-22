# src/models/schemas.py
"""
Schemas for API requests and responses.
"""



from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class LogAnalysisRequest(BaseModel):
    log_lines: List[str]
    template: Optional[str] = None
    detect_anomalies: Optional[bool] = False

# Optional response schemas (can be expanded as needed)
class AnomalyDetectionResponse(BaseModel):
    anomalies: List[int]
    scores: Optional[List[float]] = None

class RCAResponse(BaseModel):
    root_causes: List[str]
    confidence: Optional[List[float]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    uptime_seconds: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


# Main API response schema
from typing import Dict, Any

class LogAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    anomaly_detection: Optional[AnomalyDetectionResponse] = None
    root_cause_analysis: Optional[RCAResponse] = None
    processing_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


# ModelInfo schema for model metadata
class ModelInfo(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Anomaly schema for anomaly detection results
class Anomaly(BaseModel):
    id: str
    line_number: int
    log_entry: str
    anomaly_score: Optional[float] = None
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    timestamp: Optional[str] = None
    component: Optional[str] = None
    description: Optional[str] = None


# RootCause schema for root cause analysis results
class RootCause(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    affected_components: Optional[List[str]] = None
    related_anomalies: Optional[List[str]] = None
    timestamp: Optional[str] = None


# AnomalyType enum for anomaly categories
from enum import Enum

class AnomalyType(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    DENIED = "denied"
    OTHER = "other"


# SeverityLevel enum for anomaly and root cause severity
class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ConfidenceLevel enum for anomaly and root cause confidence
class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
