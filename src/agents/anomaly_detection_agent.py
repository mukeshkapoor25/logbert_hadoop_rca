"""
Anomaly Detection Agent

This agent specializes in detecting anomalies in log data using LogBERT models.
It handles model loading, preprocessing, and anomaly scoring.
"""

import asyncio
import logging
import torch
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse, AgentStatus, AgentCapability
from ..models.schemas import (
    Anomaly,
    AnomalyType,
    SeverityLevel,
    ConfidenceLevel,
    AnomalyDetectionResponse
)


class AnomalyDetectionAgent(BaseAgent):
    """
    AI Agent specialized in anomaly detection using LogBERT models.
    
    This agent:
    - Loads and manages LogBERT models
    - Preprocesses log data for analysis
    - Detects anomalies using deep learning models
    - Provides confidence scores and severity levels
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        capabilities = [
            AgentCapability.ANOMALY_DETECTION,
            AgentCapability.PREPROCESSING
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name or "AnomalyDetectionAgent",
            capabilities=capabilities,
            config=config or {}
        )
        
        # Model components
        self.model = None
        self.vocab = None
        self.center = None
        self.device = None
        self.threshold = self.config.get("threshold", 0.5)
        self.model_name = self.config.get("model_name", "logbert_hadoop")
        
    def _initialize(self):
        """Initialize the anomaly detection components."""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.logger.info(f"Initialized anomaly detection agent on device: {self.device}")
            
            # Load model lazily when first needed
            self._model_loaded = False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize anomaly detection agent: {e}")
            raise
    
    async def _load_model(self):
        """Load the LogBERT model and associated components."""
        if self._model_loaded:
            return
            
        try:
            self.logger.info("Loading LogBERT model...")
            
            # In a real implementation, this would load the actual model
            # For now, we'll simulate the model loading
            await asyncio.sleep(0.1)  # Simulate loading time
            
            # Mock model loading - replace with actual model loading logic
            self.model = MockLogBERTModel()
            self.vocab = MockVocab()
            self.center = torch.randn(512)  # Mock center vector
            
            self._model_loaded = True
            self.logger.info("LogBERT model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load LogBERT model: {e}")
            raise
    
    async def process(self, input_data: Dict[str, Any], **kwargs) -> AgentResponse:
        """
        Process log data for anomaly detection.
        
        Args:
            input_data: Dictionary containing:
                - log_text: Raw log text to analyze
                - threshold: Optional threshold override
                - model_name: Optional model name override
            **kwargs: Additional processing parameters
            
        Returns:
            AgentResponse with anomaly detection results
        """
        start_time = self.get_processing_time()
        
        # Extract parameters
        log_text = input_data.get("log_text")
        threshold = input_data.get("threshold", self.threshold)
        model_name = input_data.get("model_name", self.model_name)
        
        if not log_text:
            raise ValueError("log_text is required for anomaly detection")
        
        # Load model if not already loaded
        await self._load_model()
        
        # Preprocess log data
        processed_logs = await self._preprocess_logs(log_text)
        
        # Detect anomalies
        anomalies = await self._detect_anomalies(processed_logs, threshold)
        
        # Calculate processing time
        processing_time = self.get_processing_time() - start_time
        
        # Create response
        response_data = {
            "anomalies_detected": len(anomalies) > 0,
            "anomaly_count": len(anomalies),
            "anomalies": [anomaly.dict() for anomaly in anomalies],
            "threshold_used": threshold,
            "model_name": model_name,
            "processing_statistics": {
                "total_log_lines": len(processed_logs),
                "anomalous_lines": len(anomalies),
                "anomaly_rate": len(anomalies) / len(processed_logs) if processed_logs else 0
            }
        }
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=response_data,
            processing_time_ms=processing_time,
            metadata={
                "model_version": "1.0.0",
                "device": str(self.device),
                "threshold": threshold
            }
        )
    
    async def _preprocess_logs(self, log_text: str) -> List[Dict[str, Any]]:
        """
        Preprocess raw log text into structured format.
        
        Args:
            log_text: Raw log text
            
        Returns:
            List of processed log entries
        """
        lines = log_text.strip().split('\n')
        processed_logs = []
        
        for i, line in enumerate(lines):
            if line.strip():
                processed_logs.append({
                    "line_number": i + 1,
                    "log_entry": line.strip(),
                    "timestamp": self._extract_timestamp(line),
                    "component": self._extract_component(line),
                    "tokens": self._tokenize_log(line)
                })
        
        return processed_logs
    
    async def _detect_anomalies(
        self, 
        processed_logs: List[Dict[str, Any]], 
        threshold: float
    ) -> List[Anomaly]:
        """
        Detect anomalies in processed log data.
        
        Args:
            processed_logs: Preprocessed log entries
            threshold: Anomaly detection threshold
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for log_entry in processed_logs:
            # Simulate anomaly detection
            anomaly_score = await self._calculate_anomaly_score(log_entry)
            
            if anomaly_score > threshold:
                anomaly = await self._create_anomaly(log_entry, anomaly_score)
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _calculate_anomaly_score(self, log_entry: Dict[str, Any]) -> float:
        """
        Calculate anomaly score for a log entry.
        
        Args:
            log_entry: Processed log entry
            
        Returns:
            Anomaly score between 0.0 and 1.0
        """
        # Simulate model inference
        await asyncio.sleep(0.001)  # Simulate processing time
        
        # Mock anomaly scoring based on keywords
        log_text = log_entry["log_entry"].lower()
        error_keywords = ["error", "exception", "failed", "timeout", "crash"]
        warning_keywords = ["warning", "warn", "retry", "slow"]
        
        score = 0.0
        for keyword in error_keywords:
            if keyword in log_text:
                score += 0.3
        
        for keyword in warning_keywords:
            if keyword in log_text:
                score += 0.2
        
        # Add some randomness to simulate model uncertainty
        import random
        score += random.uniform(0, 0.1)
        
        return min(score, 1.0)
    
    async def _create_anomaly(
        self, 
        log_entry: Dict[str, Any], 
        anomaly_score: float
    ) -> Anomaly:
        """
        Create an Anomaly object from log entry and score.
        
        Args:
            log_entry: Processed log entry
            anomaly_score: Calculated anomaly score
            
        Returns:
            Anomaly object
        """
        # Determine anomaly type based on log content
        anomaly_type = self._determine_anomaly_type(log_entry["log_entry"])
        
        # Determine severity based on score and type
        severity = self._determine_severity(anomaly_score, anomaly_type)
        
        # Determine confidence based on score
        confidence = self._determine_confidence(anomaly_score)
        
        # Generate description
        description = self._generate_description(log_entry, anomaly_type)
        
        return Anomaly(
            id=f"anomaly_{log_entry['line_number']}_{int(anomaly_score * 1000)}",
            line_number=log_entry["line_number"],
            log_entry=log_entry["log_entry"],
            anomaly_score=anomaly_score,
            anomaly_type=anomaly_type,
            severity=severity,
            confidence=confidence,
            timestamp=log_entry.get("timestamp"),
            component=log_entry.get("component"),
            description=description
        )
    
    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """Extract timestamp from log line."""
        # Simple timestamp extraction - could be enhanced
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}[\s\T]\d{2}:\d{2}:\d{2}'
        match = re.search(timestamp_pattern, log_line)
        return match.group(0) if match else None
    
    def _extract_component(self, log_line: str) -> Optional[str]:
        """Extract component name from log line."""
        # Simple component extraction
        components = ["namenode", "datanode", "resourcemanager", "nodemanager", "hdfs", "yarn"]
        log_lower = log_line.lower()
        
        for component in components:
            if component in log_lower:
                return component
        
        return None
    
    def _tokenize_log(self, log_line: str) -> List[str]:
        """Tokenize log line."""
        # Simple tokenization - could use more sophisticated methods
        return log_line.split()
    
    def _determine_anomaly_type(self, log_entry: str) -> AnomalyType:
        """Determine anomaly type based on log content."""
        log_lower = log_entry.lower()
        
        if any(keyword in log_lower for keyword in ["error", "exception", "failed", "crash"]):
            return AnomalyType.ERROR
        elif any(keyword in log_lower for keyword in ["warning", "warn"]):
            return AnomalyType.WARNING
        elif any(keyword in log_lower for keyword in ["slow", "timeout", "latency"]):
            return AnomalyType.PERFORMANCE
        elif any(keyword in log_lower for keyword in ["memory", "cpu", "disk", "resource"]):
            return AnomalyType.RESOURCE
        elif any(keyword in log_lower for keyword in ["network", "connection", "socket"]):
            return AnomalyType.NETWORK
        else:
            return AnomalyType.UNKNOWN
    
    def _determine_severity(self, score: float, anomaly_type: AnomalyType) -> SeverityLevel:
        """Determine severity level based on score and type."""
        if anomaly_type == AnomalyType.ERROR and score > 0.8:
            return SeverityLevel.CRITICAL
        elif score > 0.8:
            return SeverityLevel.HIGH
        elif score > 0.6:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _determine_confidence(self, score: float) -> ConfidenceLevel:
        """Determine confidence level based on score."""
        if score > 0.8:
            return ConfidenceLevel.HIGH
        elif score > 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_description(
        self, 
        log_entry: Dict[str, Any], 
        anomaly_type: AnomalyType
    ) -> str:
        """Generate human-readable description of the anomaly."""
        component = log_entry.get("component", "system")
        
        descriptions = {
            AnomalyType.ERROR: f"Error detected in {component} component",
            AnomalyType.WARNING: f"Warning condition identified in {component}",
            AnomalyType.PERFORMANCE: f"Performance issue detected in {component}",
            AnomalyType.RESOURCE: f"Resource constraint identified in {component}",
            AnomalyType.NETWORK: f"Network-related issue detected in {component}",
            AnomalyType.UNKNOWN: f"Unusual pattern detected in {component}"
        }
        
        return descriptions.get(anomaly_type, "Anomalous behavior detected")


# Mock classes for demonstration
class MockLogBERTModel:
    """Mock LogBERT model for demonstration."""
    def __init__(self):
        self.version = "1.0.0"
    
    def predict(self, tokens):
        return torch.randn(1, 512)  # Mock embedding


class MockVocab:
    """Mock vocabulary for demonstration."""
    def __init__(self):
        self.size = 10000
    
    def encode(self, text):
        return [1, 2, 3, 4, 5]  # Mock token IDs
