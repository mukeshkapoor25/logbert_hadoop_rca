"""
LogBERT Inference Service

This module provides the main inference service for LogBERT models.
It handles model loading, anomaly detection, and prediction services.
"""

import os
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer

from ..models.logbert import LogBERTModel
from ..models.deep_svdd import DeepSVDDModel
from ..models.anomaly_detector import AnomalyDetector
from ..models.schemas import (
    AnomalyDetectionResponse,
    Anomaly,
    AnomalyType,
    SeverityLevel,
    ConfidenceLevel,
    ModelInfo,
)
from ..utils.config import get_settings
from ..data.preprocessing import LogPreprocessor
from ..utils.logging import setup_logging

# Setup logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class LogBERTInference:
    """
    Main inference service for LogBERT anomaly detection.
    
    This service handles:
    - Model loading and management
    - Log preprocessing and tokenization
    - Anomaly detection using LogBERT + Deep SVDD
    - Result formatting and confidence scoring
    """
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the LogBERT inference service.
        
        Args:
            model_path: Path to the trained model directory
            device: Device to run inference on ('cpu', 'cuda', or None for auto)
        """
        self.model_path = model_path or settings.MODEL_PATH
        self.device = device or self._get_device()
        self.model_version = "1.0.0"
        
        # Initialize components
        self.logbert_model: Optional[LogBERTModel] = None
        self.deep_svdd: Optional[DeepSVDDModel] = None
        self.anomaly_detector: Optional[AnomalyDetector] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.preprocessor: Optional[LogPreprocessor] = None
        
        # Model metadata
        self.is_loaded = False
        self.load_time: Optional[datetime] = None
        self.model_info: Dict[str, Any] = {}
        
        logger.info(f"LogBERT inference service initialized on device: {self.device}")
    
    def _get_device(self) -> str:
        """Determine the best available device for inference."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    async def load_model(self, model_name: str = "logbert_hadoop") -> None:
        """
        Load the LogBERT model and associated components.
        
        Args:
            model_name: Name of the model to load
        """
        try:
            start_time = time.time()
            logger.info(f"Loading LogBERT model: {model_name}")
            
            # Load model configuration
            config_path = os.path.join(self.model_path, model_name, "config.json")
            model_weights_path = os.path.join(self.model_path, model_name, "pytorch_model.bin")
            
            if not os.path.exists(model_weights_path):
                raise FileNotFoundError(f"Model weights not found: {model_weights_path}")
            
            # Initialize preprocessor
            self.preprocessor = LogPreprocessor()
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                os.path.join(self.model_path, model_name, "tokenizer"),
                trust_remote_code=True
            )
            
            # Load LogBERT model
            self.logbert_model = LogBERTModel(
                vocab_size=len(self.tokenizer),
                hidden_size=512,
                num_hidden_layers=6,
                num_attention_heads=8,
                intermediate_size=2048,
                max_position_embeddings=512,
                device=self.device
            )
            
            # Load model weights
            checkpoint = torch.load(model_weights_path, map_location=self.device)
            self.logbert_model.load_state_dict(checkpoint['model_state_dict'])
            self.logbert_model.to(self.device)
            self.logbert_model.eval()
            
            # Load Deep SVDD model
            svdd_path = os.path.join(self.model_path, model_name, "deep_svdd.bin")
            if os.path.exists(svdd_path):
                self.deep_svdd = DeepSVDDModel(
                    input_dim=512,  # LogBERT hidden size
                    hidden_dims=[256, 128, 64],
                    device=self.device
                )
                svdd_checkpoint = torch.load(svdd_path, map_location=self.device)
                self.deep_svdd.load_state_dict(svdd_checkpoint['model_state_dict'])
                self.deep_svdd.to(self.device)
                self.deep_svdd.eval()
            
            # Initialize anomaly detector
            self.anomaly_detector = AnomalyDetector(
                logbert_model=self.logbert_model,
                deep_svdd=self.deep_svdd,
                tokenizer=self.tokenizer,
                device=self.device
            )
            
            # Update model info
            load_time = time.time() - start_time
            self.load_time = datetime.utcnow()
            self.is_loaded = True
            self.model_info = {
                "name": model_name,
                "version": self.model_version,
                "load_time_seconds": load_time,
                "device": self.device,
                "parameters": sum(p.numel() for p in self.logbert_model.parameters()),
                "memory_usage_mb": self._get_memory_usage(),
            }
            
            logger.info(f"Model loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
            raise RuntimeError(f"Model loading failed: {e}")
    
    async def detect_anomalies(
        self,
        log_text: str,
        threshold: float = 0.5,
        model_name: str = "logbert_hadoop",
        batch_size: int = 32,
    ) -> AnomalyDetectionResponse:
        """
        Detect anomalies in log text using LogBERT.
        
        Args:
            log_text: Raw log text to analyze
            threshold: Anomaly detection threshold (0.0-1.0)
            model_name: Name of the model to use
            batch_size: Batch size for processing
            
        Returns:
            Anomaly detection results
        """
        try:
            start_time = time.time()
            
            # Ensure model is loaded
            if not self.is_loaded:
                await self.load_model(model_name)
            
            # Preprocess log text
            log_lines = log_text.strip().split('\n')
            processed_logs = []
            
            for i, line in enumerate(log_lines):
                if line.strip():  # Skip empty lines
                    processed_line = self.preprocessor.preprocess_log_line(line)
                    processed_logs.append({
                        'line_number': i + 1,
                        'original_text': line,
                        'processed_text': processed_line,
                    })
            
            if not processed_logs:
                return AnomalyDetectionResponse(
                    anomalies_detected=False,
                    total_anomalies=0,
                    anomalies=[],
                    processing_time_ms=0.0,
                    model_version=self.model_version,
                    threshold_used=threshold,
                    statistics={"total_lines": 0, "processed_lines": 0}
                )
            
            # Detect anomalies in batches
            anomalies = []
            
            for i in range(0, len(processed_logs), batch_size):
                batch = processed_logs[i:i + batch_size]
                batch_anomalies = await self._detect_batch_anomalies(batch, threshold)
                anomalies.extend(batch_anomalies)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Prepare response
            response = AnomalyDetectionResponse(
                anomalies_detected=len(anomalies) > 0,
                total_anomalies=len(anomalies),
                anomalies=anomalies,
                processing_time_ms=processing_time,
                model_version=self.model_version,
                threshold_used=threshold,
                statistics={
                    "total_lines": len(log_lines),
                    "processed_lines": len(processed_logs),
                    "empty_lines": len(log_lines) - len(processed_logs),
                    "average_line_length": np.mean([len(log['original_text']) for log in processed_logs]),
                }
            )
            
            logger.info(f"Anomaly detection completed: {len(anomalies)} anomalies found")
            return response
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}", exc_info=True)
            raise RuntimeError(f"Anomaly detection failed: {e}")
    
    async def _detect_batch_anomalies(
        self,
        batch: List[Dict[str, Any]],
        threshold: float
    ) -> List[Anomaly]:
        """
        Detect anomalies in a batch of log lines.
        
        Args:
            batch: Batch of preprocessed log lines
            threshold: Anomaly detection threshold
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            # Prepare texts for tokenization
            texts = [log['processed_text'] for log in batch]
            
            # Tokenize batch
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Get LogBERT embeddings
            with torch.no_grad():
                outputs = self.logbert_model(**inputs)
                embeddings = outputs.last_hidden_state[:, 0, :]  # Use [CLS] token
            
            # Detect anomalies using the anomaly detector
            batch_results = await self.anomaly_detector.detect_anomalies(
                embeddings=embeddings,
                texts=texts,
                threshold=threshold
            )
            
            # Convert results to Anomaly objects
            for i, (log_data, result) in enumerate(zip(batch, batch_results)):
                if result['is_anomaly']:
                    anomaly = Anomaly(
                        id=f"anomaly_{log_data['line_number']}_{int(time.time())}",
                        line_number=log_data['line_number'],
                        log_entry=log_data['original_text'],
                        anomaly_score=result['anomaly_score'],
                        anomaly_type=self._classify_anomaly_type(log_data['original_text']),
                        severity=self._determine_severity(result['anomaly_score']),
                        confidence=self._determine_confidence(result['confidence']),
                        timestamp=self._extract_timestamp(log_data['original_text']),
                        component=self._extract_component(log_data['original_text']),
                        description=self._generate_description(log_data['original_text'], result),
                    )
                    anomalies.append(anomaly)
            
        except Exception as e:
            logger.error(f"Batch anomaly detection failed: {e}", exc_info=True)
            # Continue processing other batches
        
        return anomalies
    
    def _classify_anomaly_type(self, log_entry: str) -> AnomalyType:
        """Classify the type of anomaly based on log content."""
        log_lower = log_entry.lower()
        
        if any(keyword in log_lower for keyword in ['error', 'exception', 'failed', 'fail']):
            return AnomalyType.ERROR
        elif any(keyword in log_lower for keyword in ['warn', 'warning']):
            return AnomalyType.WARNING
        elif any(keyword in log_lower for keyword in ['timeout', 'slow', 'latency', 'performance']):
            return AnomalyType.PERFORMANCE
        elif any(keyword in log_lower for keyword in ['security', 'unauthorized', 'forbidden']):
            return AnomalyType.SECURITY
        elif any(keyword in log_lower for keyword in ['memory', 'cpu', 'disk', 'resource']):
            return AnomalyType.RESOURCE
        elif any(keyword in log_lower for keyword in ['network', 'connection', 'socket']):
            return AnomalyType.NETWORK
        else:
            return AnomalyType.UNKNOWN
    
    def _determine_severity(self, anomaly_score: float) -> SeverityLevel:
        """Determine severity level based on anomaly score."""
        if anomaly_score >= 0.9:
            return SeverityLevel.CRITICAL
        elif anomaly_score >= 0.7:
            return SeverityLevel.HIGH
        elif anomaly_score >= 0.5:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _determine_confidence(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level based on confidence score."""
        if confidence_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _extract_timestamp(self, log_entry: str) -> Optional[str]:
        """Extract timestamp from log entry."""
        # Simple timestamp extraction - could be enhanced
        import re
        
        # Look for common timestamp patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_entry)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_component(self, log_entry: str) -> Optional[str]:
        """Extract system component from log entry."""
        # Simple component extraction
        components = [
            'namenode', 'datanode', 'resourcemanager', 'nodemanager',
            'jobtracker', 'tasktracker', 'yarn', 'hdfs', 'mapreduce'
        ]
        
        log_lower = log_entry.lower()
        for component in components:
            if component in log_lower:
                return component
        
        return None
    
    def _generate_description(self, log_entry: str, result: Dict[str, Any]) -> str:
        """Generate human-readable description of the anomaly."""
        anomaly_type = self._classify_anomaly_type(log_entry)
        score = result['anomaly_score']
        
        base_descriptions = {
            AnomalyType.ERROR: "Error condition detected in system operation",
            AnomalyType.WARNING: "Warning condition that may indicate potential issues",
            AnomalyType.PERFORMANCE: "Performance degradation or timing issue detected",
            AnomalyType.SECURITY: "Security-related anomaly detected",
            AnomalyType.RESOURCE: "Resource utilization anomaly detected",
            AnomalyType.NETWORK: "Network connectivity or communication issue",
            AnomalyType.UNKNOWN: "Unusual log pattern detected",
        }
        
        description = base_descriptions.get(anomaly_type, "Anomaly detected")
        description += f" (confidence: {score:.2f})"
        
        return description
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 2)
        else:
            # For CPU, this is a rough estimate
            return 0.0
    
    async def list_available_models(self) -> List[ModelInfo]:
        """List all available models."""
        models = []
        
        try:
            if os.path.exists(self.model_path):
                for model_dir in os.listdir(self.model_path):
                    model_path = os.path.join(self.model_path, model_dir)
                    if os.path.isdir(model_path):
                        model_info = await self._get_model_metadata(model_dir, model_path)
                        models.append(model_info)
        except Exception as e:
            logger.error(f"Error listing models: {e}")
        
        return models
    
    async def get_model_info(self, model_name: str) -> ModelInfo:
        """Get information about a specific model."""
        model_path = os.path.join(self.model_path, model_name)
        
        if not os.path.exists(model_path):
            raise ValueError(f"Model not found: {model_name}")
        
        return await self._get_model_metadata(model_name, model_path)
    
    async def _get_model_metadata(self, model_name: str, model_path: str) -> ModelInfo:
        """Get metadata for a model."""
        # Default model info
        model_info = ModelInfo(
            name=model_name,
            version=self.model_version,
            description=f"LogBERT model for {model_name}",
            architecture="BERT-6L-8H-512D",
            training_data="Hadoop cluster logs",
            performance_metrics={},
            supported_log_types=["hadoop", "hdfs", "yarn"],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            size_mb=0.0,
        )
        
        try:
            # Try to load metadata file if it exists
            metadata_path = os.path.join(model_path, "metadata.json")
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    model_info = ModelInfo(**metadata)
            
            # Calculate model size
            total_size = 0
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            model_info.size_mb = total_size / (1024 ** 2)
            
        except Exception as e:
            logger.warning(f"Could not load metadata for {model_name}: {e}")
        
        return model_info
