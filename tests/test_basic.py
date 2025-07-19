"""
Simple tests for core functionality without heavy dependencies.

These tests validate the basic functionality that doesn't require
FastAPI, PyTorch, or other heavy dependencies.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestBasicFunctionality:
    """Test basic project functionality."""
    
    def test_project_structure(self):
        """Test that basic project structure exists."""
        project_root = Path(__file__).parent.parent
        
        # Check core directories exist
        assert (project_root / "src").exists()
        assert (project_root / "src" / "api").exists()
        assert (project_root / "src" / "models").exists()
        assert (project_root / "src" / "services").exists()
        assert (project_root / "src" / "utils").exists()
        assert (project_root / "tests").exists()
    
    def test_config_import(self):
        """Test that configuration can be imported."""
        try:
            from src.utils.config import Settings, get_settings
            
            # Test basic settings creation
            settings = Settings()
            assert settings is not None
            
            # Test get_settings function
            settings2 = get_settings()
            assert settings2 is not None
            
        except ImportError as e:
            pytest.fail(f"Configuration import failed: {e}")
    
    def test_logging_import(self):
        """Test that logging module can be imported."""
        try:
            from src.utils.logging import setup_logging, get_logger
            
            # Test basic logging setup
            setup_logging("INFO")
            
            # Test logger creation
            logger = get_logger("test")
            assert logger is not None
            assert logger.name == "test"
            
        except ImportError as e:
            pytest.fail(f"Logging import failed: {e}")
    
    def test_schemas_import(self):
        """Test that schemas can be imported."""
        try:
            from src.models.schemas import LogAnalysisRequest
            
            # Test basic schema functionality
            assert LogAnalysisRequest is not None
            
        except ImportError as e:
            pytest.fail(f"Schemas import failed: {e}")


class TestConfigurationBasics:
    """Test basic configuration functionality."""
    
    def test_settings_creation(self):
        """Test settings can be created."""
        from src.utils.config import Settings
        
        settings = Settings()
        assert settings is not None
        
        # Test that basic attributes exist
        assert hasattr(settings, 'DEBUG')
        assert hasattr(settings, 'API_HOST')
        assert hasattr(settings, 'API_PORT')
    
    def test_environment_variables(self):
        """Test environment variable handling."""
        from src.utils.config import Settings
        
        # Test with environment override
        with patch.dict(os.environ, {'DEBUG': 'true', 'API_PORT': '9000'}):
            settings = Settings()
            assert settings.DEBUG is True
            assert settings.API_PORT == 9000


class TestLoggingBasics:
    """Test basic logging functionality."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        from src.utils.logging import setup_logging, get_logger
        
        # Test setup with different levels
        setup_logging("DEBUG")
        setup_logging("INFO")
        setup_logging("WARNING")
        
        # Test logger creation after setup
        logger = get_logger("test_logger")
        assert logger.name == "test_logger"
    
    def test_logger_methods(self):
        """Test logger has required methods."""
        from src.utils.logging import get_logger
        
        logger = get_logger("method_test")
        
        # Test that logger has standard methods
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'critical')
        
        # Test methods are callable
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)
        assert callable(logger.critical)


class TestSchemaBasics:
    """Test basic schema functionality."""
    
    def test_log_analysis_request_exists(self):
        """Test LogAnalysisRequest schema exists."""
        from src.models.schemas import LogAnalysisRequest
        
        assert LogAnalysisRequest is not None
        
        # Test it's a class
        assert isinstance(LogAnalysisRequest, type)
    
    def test_response_schemas_exist(self):
        """Test response schemas exist."""
        try:
            from src.models.schemas import (
                AnomalyDetectionResponse,
                RCAResponse,
                HealthResponse
            )
            
            assert AnomalyDetectionResponse is not None
            assert RCAResponse is not None
            assert HealthResponse is not None
            
        except ImportError:
            # Some schemas might not exist yet, which is okay
            pytest.skip("Some response schemas not implemented yet")


class TestServiceImports:
    """Test service imports."""
    
    def test_inference_service_import(self):
        """Test inference service can be imported."""
        try:
            from src.services.inference import LogBERTInference
            assert LogBERTInference is not None
        except ImportError:
            pytest.skip("Inference service not implemented or dependencies missing")
    
    def test_rca_service_import(self):
        """Test RCA service can be imported."""
        try:
            from src.services.rca import RootCauseAnalyzer
            assert RootCauseAnalyzer is not None
        except ImportError:
            pytest.skip("RCA service not implemented or dependencies missing")


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_file_operations(self, temp_dir):
        """Test basic file operations."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_content = "This is a test file"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Verify file was created
        assert test_file.exists()
        
        # Read file content
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == test_content
    
    def test_directory_operations(self, temp_dir):
        """Test directory operations."""
        # Create subdirectory
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()
        
        assert sub_dir.exists()
        assert sub_dir.is_dir()
        
        # Create file in subdirectory
        sub_file = sub_dir / "subfile.txt"
        sub_file.write_text("Sub file content")
        
        assert sub_file.exists()
        assert sub_file.read_text() == "Sub file content"


class TestMockData:
    """Test mock data functionality."""
    
    def test_sample_logs(self, sample_hadoop_logs):
        """Test sample log data."""
        assert sample_hadoop_logs is not None
        assert isinstance(sample_hadoop_logs, list)
        assert len(sample_hadoop_logs) > 0
        
        # Check first log entry
        first_log = sample_hadoop_logs[0]
        assert isinstance(first_log, str)
        assert len(first_log) > 0
    
    def test_sample_templates(self, sample_log_templates):
        """Test sample log templates."""
        assert sample_log_templates is not None
        assert isinstance(sample_log_templates, list)
        assert len(sample_log_templates) > 0
    
    def test_anomaly_labels(self, sample_anomaly_labels):
        """Test anomaly labels."""
        assert sample_anomaly_labels is not None
        assert isinstance(sample_anomaly_labels, list)
        assert all(isinstance(label, int) for label in sample_anomaly_labels)
        assert all(label in [0, 1] for label in sample_anomaly_labels)


@pytest.mark.performance
class TestPerformanceBasics:
    """Basic performance tests."""
    
    def test_import_performance(self, performance_timer):
        """Test import performance."""
        performance_timer.start()
        
        # Import core modules
        from src.utils.config import Settings
        from src.utils.logging import get_logger
        from src.models.schemas import LogAnalysisRequest
        
        elapsed = performance_timer.stop()
        
        # Imports should be fast (under 1 second)
        assert elapsed < 1.0
    
    def test_config_creation_performance(self, performance_timer):
        """Test configuration creation performance."""
        from src.utils.config import Settings
        
        performance_timer.start()
        
        # Create multiple settings instances
        for _ in range(100):
            settings = Settings()
        
        elapsed = performance_timer.stop()
        
        # Should be able to create 100 instances quickly
        assert elapsed < 0.1
