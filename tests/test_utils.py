"""
Unit tests for utilities and configuration.

Tests the configuration management, logging setup, and utility functions.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json


class TestConfiguration:
    """Test configuration management."""
    
    def test_default_settings(self):
        """Test default configuration settings."""
        try:
            from src.utils.config import Settings
            
            settings = Settings()
            
            # Test default values
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 8000
            assert settings.log_level == "INFO"
            
        except ImportError:
            pytest.skip("Configuration module not available")
    
    def test_environment_override(self):
        """Test environment variable override."""
        try:
            from src.utils.config import Settings
            
            # Set environment variables
            with patch.dict(os.environ, {
                'ENVIRONMENT': 'production',
                'DEBUG': 'false',
                'API_PORT': '9000',
                'LOG_LEVEL': 'ERROR'
            }):
                settings = Settings()
                
                assert settings.environment == "production"
                assert settings.debug is False
                assert settings.api_port == 9000
                assert settings.log_level == "ERROR"
                
        except ImportError:
            pytest.skip("Configuration module not available")
    
    def test_invalid_environment(self):
        """Test handling of invalid environment values."""
        try:
            from src.utils.config import Settings
            
            with patch.dict(os.environ, {'ENVIRONMENT': 'invalid'}):
                settings = Settings()
                # Should default to development for invalid values
                assert settings.environment == "development"
                
        except ImportError:
            pytest.skip("Configuration module not available")


class TestLogging:
    """Test logging configuration."""
    
    def test_logger_creation(self):
        """Test logger creation and configuration."""
        try:
            from src.utils.logging import setup_logging, get_logger
            
            # Setup logging
            setup_logging("DEBUG")
            
            # Get a logger
            logger = get_logger("test_logger")
            
            assert logger is not None
            assert logger.name == "test_logger"
            
        except ImportError:
            pytest.skip("Logging module not available")
    
    def test_log_levels(self):
        """Test different log levels."""
        try:
            from src.utils.logging import setup_logging, get_logger
            
            setup_logging("INFO")
            logger = get_logger("test_levels")
            
            # Test that logger accepts different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            # No assertion needed, just testing that no exceptions occur
            
        except ImportError:
            pytest.skip("Logging module not available")
    
    def test_structured_logging(self, temp_dir):
        """Test structured logging to file."""
        try:
            from src.utils.logging import setup_logging, get_logger
            
            log_file = temp_dir / "test.log"
            
            # Setup logging with file output
            setup_logging("INFO", str(log_file))
            logger = get_logger("test_structured")
            
            # Log a structured message
            logger.info("Test message", extra={
                "user_id": "test_user",
                "action": "test_action",
                "duration": 0.123
            })
            
            # Verify log file was created
            assert log_file.exists()
            
        except ImportError:
            pytest.skip("Logging module not available")


class TestDataPreprocessing:
    """Test data preprocessing utilities."""
    
    def test_log_parsing(self, sample_hadoop_logs):
        """Test basic log parsing functionality."""
        try:
            from src.data.preprocessing import parse_log_entry, extract_timestamp
            
            log_entry = sample_hadoop_logs[0]
            parsed = parse_log_entry(log_entry)
            
            assert "timestamp" in parsed
            assert "level" in parsed
            assert "message" in parsed
            assert "component" in parsed
            
        except ImportError:
            pytest.skip("Preprocessing module not available")
    
    def test_log_cleaning(self, sample_hadoop_logs):
        """Test log cleaning and normalization."""
        try:
            from src.data.preprocessing import clean_log_entry, normalize_logs
            
            # Test single log cleaning
            raw_log = sample_hadoop_logs[0]
            cleaned = clean_log_entry(raw_log)
            
            assert isinstance(cleaned, str)
            assert len(cleaned) > 0
            
            # Test batch normalization
            normalized = normalize_logs(sample_hadoop_logs[:3])
            
            assert isinstance(normalized, list)
            assert len(normalized) == 3
            
        except ImportError:
            pytest.skip("Preprocessing module not available")
    
    def test_feature_extraction(self, sample_hadoop_logs):
        """Test feature extraction from logs."""
        try:
            from src.data.preprocessing import extract_features, create_vocabulary
            
            # Extract features from logs
            features = extract_features(sample_hadoop_logs[:3])
            
            assert isinstance(features, dict)
            assert "tokens" in features or "sequences" in features
            
            # Test vocabulary creation
            vocab = create_vocabulary(sample_hadoop_logs[:3])
            
            assert isinstance(vocab, dict)
            assert len(vocab) > 0
            
        except ImportError:
            pytest.skip("Preprocessing module not available")


class TestModelSchemas:
    """Test Pydantic schemas and data models."""
    
    def test_log_analysis_request_schema(self, sample_hadoop_logs):
        """Test LogAnalysisRequest schema validation."""
        try:
            from src.models.schemas import LogAnalysisRequest
            
            # Valid request
            valid_request = {
                "logs": sample_hadoop_logs[:3],
                "analysis_type": "anomaly_detection",
                "confidence_threshold": 0.5
            }
            
            request = LogAnalysisRequest(**valid_request)
            
            assert request.logs == sample_hadoop_logs[:3]
            assert request.analysis_type == "anomaly_detection"
            assert request.confidence_threshold == 0.5
            
        except ImportError:
            pytest.skip("Schemas module not available")
    
    def test_log_analysis_request_validation(self):
        """Test schema validation with invalid data."""
        try:
            from src.models.schemas import LogAnalysisRequest
            from pydantic import ValidationError
            
            # Invalid request - empty logs
            with pytest.raises(ValidationError):
                LogAnalysisRequest(
                    logs=[],
                    analysis_type="anomaly_detection"
                )
            
            # Invalid request - invalid analysis type
            with pytest.raises(ValidationError):
                LogAnalysisRequest(
                    logs=["test log"],
                    analysis_type="invalid_type"
                )
            
            # Invalid request - invalid confidence threshold
            with pytest.raises(ValidationError):
                LogAnalysisRequest(
                    logs=["test log"],
                    analysis_type="anomaly_detection",
                    confidence_threshold=2.0  # Should be between 0 and 1
                )
                
        except ImportError:
            pytest.skip("Schemas module not available")
    
    def test_anomaly_detection_response_schema(self):
        """Test AnomalyDetectionResponse schema."""
        try:
            from src.models.schemas import AnomalyDetectionResponse
            
            response_data = {
                "predictions": [0.1, 0.8, 0.3],
                "anomalies": [False, True, False],
                "confidence": [0.9, 0.95, 0.85],
                "summary": {
                    "total_logs": 3,
                    "anomaly_count": 1,
                    "normal_count": 2,
                    "anomaly_rate": 0.33
                },
                "processing_time": 0.123,
                "model_info": {
                    "name": "LogBERT-Hadoop",
                    "version": "1.0.0"
                }
            }
            
            response = AnomalyDetectionResponse(**response_data)
            
            assert response.predictions == [0.1, 0.8, 0.3]
            assert response.anomalies == [False, True, False]
            assert response.summary.total_logs == 3
            assert response.processing_time == 0.123
            
        except ImportError:
            pytest.skip("Schemas module not available")


class TestInferenceService:
    """Test inference service functionality."""
    
    def test_inference_service_creation(self):
        """Test inference service initialization."""
        try:
            from src.services.inference import LogBERTInference
            
            # Create service with mock models
            service = LogBERTInference(mock_mode=True)
            
            assert service is not None
            assert service.is_ready()
            
        except ImportError:
            pytest.skip("Inference service module not available")
    
    def test_mock_inference(self, sample_hadoop_logs):
        """Test mock inference functionality."""
        try:
            from src.services.inference import LogBERTInference
            
            service = LogBERTInference(mock_mode=True)
            
            # Test log analysis
            results = service.analyze_logs(sample_hadoop_logs[:3])
            
            assert "predictions" in results
            assert "anomalies" in results
            assert "confidence" in results
            assert len(results["predictions"]) == 3
            
        except ImportError:
            pytest.skip("Inference service module not available")
    
    def test_batch_processing(self, sample_hadoop_logs):
        """Test batch processing of logs."""
        try:
            from src.services.inference import LogBERTInference
            
            service = LogBERTInference(mock_mode=True)
            
            # Process larger batch
            large_batch = sample_hadoop_logs * 10  # 50 logs
            results = service.analyze_logs(large_batch, batch_size=8)
            
            assert "predictions" in results
            assert len(results["predictions"]) == len(large_batch)
            
        except ImportError:
            pytest.skip("Inference service module not available")


class TestRCAService:
    """Test Root Cause Analysis service."""
    
    def test_rca_service_creation(self):
        """Test RCA service initialization."""
        try:
            from src.services.rca import RootCauseAnalyzer
            
            service = RootCauseAnalyzer(mock_mode=True)
            
            assert service is not None
            assert service.is_ready()
            
        except ImportError:
            pytest.skip("RCA service module not available")
    
    def test_root_cause_analysis(self, sample_hadoop_logs):
        """Test root cause analysis functionality."""
        try:
            from src.services.rca import RootCauseAnalyzer
            
            service = RootCauseAnalyzer(mock_mode=True)
            
            # Filter anomalous logs (indices 2 and 4 based on our sample data)
            anomalous_logs = [sample_hadoop_logs[2], sample_hadoop_logs[4]]
            
            results = service.analyze_root_cause(anomalous_logs)
            
            assert "root_causes" in results
            assert "recommendations" in results
            assert "severity" in results
            assert isinstance(results["root_causes"], list)
            
        except ImportError:
            pytest.skip("RCA service module not available")


@pytest.mark.integration
class TestIntegrationUtils:
    """Integration tests for utility components."""
    
    def test_full_pipeline_configuration(self):
        """Test complete configuration pipeline."""
        try:
            from src.utils.config import Settings
            from src.utils.logging import setup_logging, get_logger
            
            # Load configuration
            settings = Settings()
            
            # Setup logging based on configuration
            setup_logging(settings.log_level)
            logger = get_logger("integration_test")
            
            # Log configuration info
            logger.info(f"Environment: {settings.environment}")
            logger.info(f"Debug mode: {settings.debug}")
            logger.info(f"API endpoint: {settings.api_host}:{settings.api_port}")
            
            # Verify everything works together
            assert settings is not None
            assert logger is not None
            
        except ImportError:
            pytest.skip("Configuration or logging modules not available")


@pytest.mark.performance
class TestUtilsPerformance:
    """Performance tests for utility functions."""
    
    def test_log_processing_performance(self, sample_hadoop_logs, performance_timer):
        """Test log processing performance."""
        try:
            from src.data.preprocessing import normalize_logs, extract_features
            
            # Create a larger dataset for performance testing
            large_dataset = sample_hadoop_logs * 100  # 500 logs
            
            # Test normalization performance
            performance_timer.start()
            normalized = normalize_logs(large_dataset)
            normalization_time = performance_timer.stop()
            
            assert len(normalized) == len(large_dataset)
            # Should process 500 logs in under 1 second
            assert normalization_time < 1.0
            
        except ImportError:
            pytest.skip("Preprocessing module not available")
