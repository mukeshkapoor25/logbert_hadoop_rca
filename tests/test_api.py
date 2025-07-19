"""
Unit tests for API endpoints.

Tests the FastAPI application endpoints including health checks,
log analysis, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_root_endpoint(self, api_client: TestClient):
        """Test root endpoint returns API information."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, api_client: TestClient):
        """Test health check endpoint."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
    
    def test_status_endpoint(self, api_client: TestClient):
        """Test detailed status endpoint."""
        response = api_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "api_status" in data
        assert "models_status" in data
        assert "system_info" in data


class TestAnalysisEndpoints:
    """Test log analysis endpoints."""
    
    def test_analyze_logs_endpoint(self, api_client: TestClient, sample_hadoop_logs):
        """Test log analysis endpoint with valid input."""
        request_data = {
            "logs": sample_hadoop_logs[:3],  # Use first 3 logs
            "analysis_type": "anomaly_detection",
            "confidence_threshold": 0.5
        }
        
        response = api_client.post("/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "summary" in data
        assert "processing_time" in data
        
        # Check results structure
        results = data["results"]
        assert "predictions" in results
        assert "anomalies" in results
        assert "confidence" in results
        
        # Verify response lengths match input
        assert len(results["predictions"]) == len(sample_hadoop_logs[:3])
        assert len(results["anomalies"]) == len(sample_hadoop_logs[:3])
        assert len(results["confidence"]) == len(sample_hadoop_logs[:3])
    
    def test_analyze_logs_empty_input(self, api_client: TestClient):
        """Test log analysis with empty input."""
        request_data = {
            "logs": [],
            "analysis_type": "anomaly_detection"
        }
        
        response = api_client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_analyze_logs_invalid_type(self, api_client: TestClient, sample_hadoop_logs):
        """Test log analysis with invalid analysis type."""
        request_data = {
            "logs": sample_hadoop_logs[:2],
            "analysis_type": "invalid_type"
        }
        
        response = api_client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_analyze_logs_rca(self, api_client: TestClient, sample_hadoop_logs):
        """Test root cause analysis endpoint."""
        request_data = {
            "logs": sample_hadoop_logs,
            "analysis_type": "root_cause_analysis",
            "anomaly_threshold": 0.7
        }
        
        response = api_client.post("/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "summary" in data
        
        # Check RCA-specific fields
        results = data["results"]
        if "root_causes" in results:
            assert isinstance(results["root_causes"], list)
        if "recommendations" in results:
            assert isinstance(results["recommendations"], list)


class TestModelEndpoints:
    """Test model-related endpoints."""
    
    def test_models_list(self, api_client: TestClient):
        """Test models listing endpoint."""
        response = api_client.get("/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        
        # Check model information structure
        if data["models"]:
            model = data["models"][0]
            assert "name" in model
            assert "version" in model
            assert "status" in model


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_endpoint(self, api_client: TestClient):
        """Test accessing non-existent endpoint."""
        response = api_client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self, api_client: TestClient):
        """Test using wrong HTTP method."""
        response = api_client.get("/analyze")  # Should be POST
        assert response.status_code == 405  # Method not allowed
    
    def test_malformed_json(self, api_client: TestClient):
        """Test sending malformed JSON."""
        response = api_client.post(
            "/analyze",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    def test_complete_analysis_workflow(self, api_client: TestClient, sample_hadoop_logs):
        """Test complete log analysis workflow."""
        # Step 1: Check API health
        health_response = api_client.get("/health")
        assert health_response.status_code == 200
        
        # Step 2: Check available models
        models_response = api_client.get("/models")
        assert models_response.status_code == 200
        
        # Step 3: Perform log analysis
        analysis_request = {
            "logs": sample_hadoop_logs,
            "analysis_type": "anomaly_detection",
            "confidence_threshold": 0.5
        }
        
        analysis_response = api_client.post("/analyze", json=analysis_request)
        assert analysis_response.status_code == 200
        
        # Verify complete response
        data = analysis_response.json()
        assert "results" in data
        assert "summary" in data
        assert "processing_time" in data
        
        # Check that processing time is reasonable (under 10 seconds for mock)
        assert data["processing_time"] < 10.0


@pytest.mark.performance
class TestPerformance:
    """Performance tests for API endpoints."""
    
    def test_analysis_performance(self, api_client: TestClient, sample_hadoop_logs, performance_timer):
        """Test analysis endpoint performance."""
        request_data = {
            "logs": sample_hadoop_logs * 10,  # 50 logs total
            "analysis_type": "anomaly_detection"
        }
        
        performance_timer.start()
        response = api_client.post("/analyze", json=request_data)
        elapsed_time = performance_timer.stop()
        
        assert response.status_code == 200
        # Performance check: should complete within reasonable time
        assert elapsed_time < 5.0  # 5 seconds for mock analysis
    
    def test_concurrent_requests(self, api_client: TestClient, sample_hadoop_logs):
        """Test handling multiple concurrent requests."""
        import threading
        import time
        
        request_data = {
            "logs": sample_hadoop_logs[:3],
            "analysis_type": "anomaly_detection"
        }
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = api_client.post("/analyze", json=request_data)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create 5 concurrent threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)
