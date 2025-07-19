"""
Pytest configuration and fixtures for LogBERT Hadoop RCA testing.

This module provides shared test fixtures and configurations for the entire test suite,
including API client setup, database mocking, model mocking, and test data generation.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, List
from unittest.mock import Mock, MagicMock
import json

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import torch
    import numpy as np
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# Test Configuration
@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration settings."""
    return {
        "test_mode": True,
        "debug": True,
        "log_level": "DEBUG",
        "api_host": "127.0.0.1",
        "api_port": 8001,  # Different from development port
        "model_path": "tests/fixtures/mock_model",
        "data_path": "tests/fixtures/test_data",
        "batch_size": 4,
        "max_sequence_length": 128,
        "mock_ml_models": True,
    }


# Temporary Directory Fixtures
@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test isolation."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    test_data_path = Path(tempfile.mkdtemp(prefix="logbert_test_data_"))
    try:
        # Create test data structure
        (test_data_path / "logs").mkdir(exist_ok=True)
        (test_data_path / "models").mkdir(exist_ok=True)
        (test_data_path / "output").mkdir(exist_ok=True)
        yield test_data_path
    finally:
        shutil.rmtree(test_data_path, ignore_errors=True)


# API Testing Fixtures
@pytest.fixture(scope="session")
def mock_app() -> FastAPI:
    """Create a mock FastAPI application for testing."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not available for testing")
    
    from src.api.main import create_app
    from src.utils.config import Settings
    
    # Create test settings
    test_settings = Settings(
        environment="testing",
        debug=True,
        log_level="DEBUG",
        api_host="127.0.0.1",
        api_port=8001,
        enable_cors=True,
        mock_ml_models=True,
    )
    
    app = create_app(settings=test_settings)
    return app


@pytest.fixture(scope="function")
def api_client(mock_app: FastAPI) -> Generator[TestClient, None, None]:
    """Create a test client for API testing."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not available for testing")
    
    with TestClient(mock_app) as client:
        yield client


# Mock Model Fixtures
@pytest.fixture(scope="session")
def mock_logbert_model():
    """Mock LogBERT model for testing."""
    if TORCH_AVAILABLE:
        model = Mock()
        model.eval.return_value = None
        model.to.return_value = model
        model.parameters.return_value = []
        
        # Mock forward pass
        def mock_forward(input_ids, attention_mask=None, **kwargs):
            batch_size = input_ids.shape[0] if hasattr(input_ids, 'shape') else 1
            return Mock(
                logits=torch.randn(batch_size, 2),  # Binary classification
                hidden_states=torch.randn(batch_size, 128, 768),
                attentions=torch.randn(batch_size, 8, 128, 128)
            )
        
        model.forward = mock_forward
        model.__call__ = mock_forward
        return model
    else:
        # Simple mock for when torch is not available
        model = Mock()
        model.eval.return_value = None
        return model


@pytest.fixture(scope="session")
def mock_tokenizer():
    """Mock tokenizer for testing."""
    tokenizer = Mock()
    tokenizer.encode.return_value = [101, 102, 103, 104, 105]  # Mock token IDs
    tokenizer.decode.return_value = "mock decoded text"
    tokenizer.vocab_size = 30522
    tokenizer.pad_token_id = 0
    tokenizer.cls_token_id = 101
    tokenizer.sep_token_id = 102
    tokenizer.max_len = 512
    
    def mock_encode_plus(text, **kwargs):
        return {
            'input_ids': [101, 102, 103, 104, 105],
            'attention_mask': [1, 1, 1, 1, 1],
            'token_type_ids': [0, 0, 0, 0, 0]
        }
    
    tokenizer.encode_plus = mock_encode_plus
    tokenizer.__call__ = mock_encode_plus
    return tokenizer


@pytest.fixture(scope="session")
def mock_deep_svdd_model():
    """Mock Deep SVDD model for testing."""
    if TORCH_AVAILABLE:
        model = Mock()
        model.eval.return_value = None
        model.to.return_value = model
        model.center = torch.randn(128)
        model.radius = torch.tensor(1.0)
        
        def mock_forward(x):
            batch_size = x.shape[0] if hasattr(x, 'shape') else 1
            return torch.randn(batch_size, 128)
        
        model.forward = mock_forward
        model.__call__ = mock_forward
        return model
    else:
        model = Mock()
        model.eval.return_value = None
        return model


# Test Data Fixtures
@pytest.fixture(scope="session")
def sample_hadoop_logs() -> List[str]:
    """Sample Hadoop log entries for testing."""
    return [
        "2023-07-19 10:15:30,123 INFO [main] org.apache.hadoop.hdfs.server.namenode.NameNode: Starting NameNode",
        "2023-07-19 10:15:31,456 WARN [main] org.apache.hadoop.hdfs.server.namenode.FSNamesystem: Block pool ID unassigned",
        "2023-07-19 10:15:32,789 ERROR [main] org.apache.hadoop.hdfs.server.datanode.DataNode: Failed to connect to namenode",
        "2023-07-19 10:15:33,012 INFO [main] org.apache.hadoop.yarn.server.resourcemanager.ResourceManager: Starting ResourceManager",
        "2023-07-19 10:15:34,345 FATAL [main] org.apache.hadoop.hdfs.server.namenode.NameNode: OutOfMemoryError in NameNode"
    ]


@pytest.fixture(scope="session") 
def sample_log_templates() -> List[str]:
    """Sample log templates for testing."""
    return [
        "Starting <*>",
        "Block pool ID <*>",
        "Failed to connect to <*>",
        "Starting <*>",
        "<*> in <*>"
    ]


@pytest.fixture(scope="session")
def sample_anomaly_labels() -> List[int]:
    """Sample anomaly labels for testing (0=normal, 1=anomaly)."""
    return [0, 0, 1, 0, 1]  # Matches sample_hadoop_logs


@pytest.fixture(scope="function")
def mock_log_file(temp_dir: Path, sample_hadoop_logs: List[str]) -> Path:
    """Create a mock log file for testing."""
    log_file = temp_dir / "test.log"
    with open(log_file, 'w') as f:
        for log_entry in sample_hadoop_logs:
            f.write(f"{log_entry}\n")
    return log_file


# Mock Service Fixtures
@pytest.fixture(scope="function")
def mock_inference_service():
    """Mock LogBERT inference service."""
    service = Mock()
    
    def mock_analyze_logs(logs: List[str], **kwargs):
        return {
            "predictions": [0.1, 0.2, 0.8, 0.1, 0.9],  # Anomaly scores
            "anomalies": [False, False, True, False, True],
            "confidence": [0.95, 0.88, 0.92, 0.94, 0.96],
            "processing_time": 0.123
        }
    
    def mock_detect_anomalies(logs: List[str], **kwargs):
        return {
            "anomaly_count": 2,
            "normal_count": 3,
            "anomaly_rate": 0.4,
            "detailed_results": [
                {"log_index": 2, "anomaly_score": 0.8, "is_anomaly": True},
                {"log_index": 4, "anomaly_score": 0.9, "is_anomaly": True}
            ]
        }
    
    service.analyze_logs = mock_analyze_logs
    service.detect_anomalies = mock_detect_anomalies
    service.is_ready = Mock(return_value=True)
    service.get_model_info = Mock(return_value={
        "model_name": "LogBERT-Hadoop",
        "version": "1.0.0",
        "parameters": 110000000
    })
    
    return service


@pytest.fixture(scope="function")
def mock_rca_service():
    """Mock Root Cause Analysis service."""
    service = Mock()
    
    def mock_analyze_root_cause(anomalous_logs: List[str], **kwargs):
        return {
            "root_causes": [
                {
                    "category": "Memory",
                    "description": "OutOfMemoryError detected",
                    "confidence": 0.95,
                    "affected_logs": [4]
                },
                {
                    "category": "Network",
                    "description": "Connection failure to namenode",
                    "confidence": 0.88,
                    "affected_logs": [2]
                }
            ],
            "recommendations": [
                "Increase heap memory allocation for NameNode",
                "Check network connectivity to namenode"
            ],
            "severity": "HIGH"
        }
    
    service.analyze_root_cause = mock_analyze_root_cause
    service.is_ready = Mock(return_value=True)
    
    return service


# Environment Setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_config: Dict[str, Any]):
    """Setup test environment variables."""
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["MOCK_ML_MODELS"] = "true"
    
    yield
    
    # Cleanup environment variables
    test_env_vars = ["ENVIRONMENT", "DEBUG", "LOG_LEVEL", "MOCK_ML_MODELS"]
    for var in test_env_vars:
        os.environ.pop(var, None)


# Pytest Configuration
def pytest_configure(config):
    """Pytest configuration hook."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "ml: marks tests as machine learning tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add slow marker to tests that might be slow
        if "integration" in item.nodeid or "e2e" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add markers based on file location
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "test_models" in item.nodeid or "test_inference" in item.nodeid:
            item.add_marker(pytest.mark.ml)
        elif "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)


# Skip conditions
skipif_no_torch = pytest.mark.skipif(
    not TORCH_AVAILABLE,
    reason="PyTorch not available"
)

skipif_no_fastapi = pytest.mark.skipif(
    not FASTAPI_AVAILABLE,
    reason="FastAPI not available"
)


# Utility functions for tests
@pytest.fixture
def assert_log_analysis_response():
    """Helper function to validate log analysis responses."""
    def _assert_response(response_data: Dict[str, Any]):
        assert "predictions" in response_data
        assert "anomalies" in response_data
        assert "confidence" in response_data
        assert "processing_time" in response_data
        assert isinstance(response_data["predictions"], list)
        assert isinstance(response_data["anomalies"], list)
        assert isinstance(response_data["confidence"], list)
        assert isinstance(response_data["processing_time"], (int, float))
    
    return _assert_response


@pytest.fixture
def assert_rca_response():
    """Helper function to validate RCA responses."""
    def _assert_response(response_data: Dict[str, Any]):
        assert "root_causes" in response_data
        assert "recommendations" in response_data
        assert "severity" in response_data
        assert isinstance(response_data["root_causes"], list)
        assert isinstance(response_data["recommendations"], list)
        assert response_data["severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    return _assert_response


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed_time
        
        @property
        def elapsed_time(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()
