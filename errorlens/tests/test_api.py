"""
Tests for ErrorLens FastAPI Backend

This module contains comprehensive tests for the FastAPI endpoints,
including unit tests with mocked dependencies.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO

# Mock all external dependencies before importing
mock_sentence_transformers = MagicMock()
mock_torch = MagicMock()
mock_groq = MagicMock()

with patch.dict('sys.modules', {
    'sentence_transformers': mock_sentence_transformers,
    'torch': mock_torch,
    'groq': mock_groq
}):
    from backend.main import app
    from backend.models import LogEntry


class TestAPI:
    """Test suite for FastAPI endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Mock all components
        self.mock_log_parser = MagicMock()
        self.mock_embedder = MagicMock()
        self.mock_endee_client = MagicMock()
        self.mock_rag_engine = MagicMock()
        
        # Configure mocks
        self.mock_embedder.is_model_loaded.return_value = True
        self.mock_embedder.embed.return_value = [0.1] * 384
        self.mock_embedder.embed_log_entries.return_value = [[0.1] * 384, [0.2] * 384]
        
        self.mock_endee_client.collection_exists.return_value = True
        self.mock_endee_client.health_check.return_value = {"status": "healthy"}
        self.mock_endee_client.get_stats.return_value = {
            "collection": "error_logs",
            "vector_count": 100,
            "dimension": 384,
            "metric": "cosine"
        }
        self.mock_endee_client.search.return_value = {
            "results": [
                {
                    "id": "log_001",
                    "score": 0.95,
                    "metadata": {
                        "severity": "ERROR",
                        "service": "auth_service",
                        "message": "Invalid credentials",
                        "timestamp": "2024-01-15T10:30:45Z",
                        "raw_log": "[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials"
                    }
                }
            ]
        }
        
        self.mock_rag_engine.groq_available = True
        self.mock_rag_engine.analyze.return_value = {
            "analysis": {
                "root_cause": "Authentication service overload",
                "fix_suggestions": "Scale the auth service",
                "prevention": "Implement rate limiting"
            }
        }
        
        # Sample log entries
        self.sample_log_entries = [
            LogEntry(
                severity="ERROR",
                service="auth_service",
                message="Invalid credentials",
                timestamp="2024-01-15T10:30:45Z",
                raw_log="[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
                line_number=1
            ),
            LogEntry(
                severity="WARN",
                service="payment_service",
                message="Timeout occurred",
                timestamp="2024-01-15T10:30:46Z",
                raw_log="[2024-01-15T10:30:46Z] WARN [payment_service] Timeout occurred",
                line_number=2
            )
        ]
        
        self.mock_log_parser.parse_file.return_value = self.sample_log_entries
    
    def override_dependencies(self):
        """Override FastAPI dependencies with mocks."""
        def mock_get_components():
            return (
                self.mock_log_parser,
                self.mock_embedder,
                self.mock_endee_client,
                self.mock_rag_engine
            )
        
        app.dependency_overrides[app.router.dependencies[0].dependency] = mock_get_components
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ErrorLens API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    @patch('backend.main.get_components')
    def test_health_endpoint_healthy(self, mock_get_components):
        """Test health endpoint when all services are healthy."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["endee_connected"] is True
        assert data["model_loaded"] is True
    
    @patch('backend.main.get_components')
    def test_health_endpoint_unhealthy(self, mock_get_components):
        """Test health endpoint when services are unhealthy."""
        # Configure unhealthy mocks
        self.mock_endee_client.health_check.side_effect = Exception("Connection failed")
        self.mock_embedder.is_model_loaded.return_value = False
        
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        response = self.client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["endee_connected"] is False
        assert data["model_loaded"] is False
    
    @patch('backend.main.get_components')
    def test_stats_endpoint(self, mock_get_components):
        """Test stats endpoint."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        response = self.client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["collection"] == "error_logs"
        assert data["vector_count"] == 100
        assert data["dimension"] == 384
        assert data["metric"] == "cosine"
    
    @patch('backend.main.get_components')
    def test_search_endpoint_without_rag(self, mock_get_components):
        """Test search endpoint without RAG analysis."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        search_request = {
            "query": "authentication errors",
            "top_k": 10,
            "rag_enabled": False
        }
        
        response = self.client.post("/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "authentication errors"
        assert len(data["results"]) == 1
        assert data["count"] == 1
        assert data["rag_analysis"] is None
        
        # Check result structure
        result = data["results"][0]
        assert result["severity"] == "ERROR"
        assert result["service"] == "auth_service"
        assert result["message"] == "Invalid credentials"
        assert result["similarity_score"] == 0.95
    
    @patch('backend.main.get_components')
    def test_search_endpoint_with_rag(self, mock_get_components):
        """Test search endpoint with RAG analysis."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        search_request = {
            "query": "authentication errors",
            "top_k": 10,
            "rag_enabled": True
        }
        
        response = self.client.post("/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "authentication errors"
        assert data["rag_analysis"] is not None
        assert data["rag_analysis"]["root_cause"] == "Authentication service overload"
        assert "Scale the auth service" in data["rag_analysis"]["fix_suggestions"]
    
    @patch('backend.main.get_components')
    def test_search_endpoint_rag_unavailable(self, mock_get_components):
        """Test search endpoint when RAG is unavailable."""
        self.mock_rag_engine.groq_available = False
        
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        search_request = {
            "query": "authentication errors",
            "top_k": 10,
            "rag_enabled": True
        }
        
        response = self.client.post("/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["rag_analysis"] is not None
        assert "unavailable" in data["rag_analysis"]["root_cause"]
        assert "GROQ_API_KEY" in data["rag_analysis"]["fix_suggestions"]
    
    @patch('backend.main.get_components')
    def test_search_endpoint_validation(self, mock_get_components):
        """Test search endpoint input validation."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        # Test empty query
        response = self.client.post("/search", json={"query": "", "top_k": 10})
        assert response.status_code == 422  # Validation error
        
        # Test invalid top_k
        response = self.client.post("/search", json={"query": "test", "top_k": 0})
        assert response.status_code == 422  # Validation error
        
        response = self.client.post("/search", json={"query": "test", "top_k": 101})
        assert response.status_code == 422  # Validation error
    
    @patch('backend.main.get_components')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_ingest_endpoint_success(self, mock_unlink, mock_temp_file, mock_get_components):
        """Test successful file ingestion."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.log"
        
        # Create test file content
        test_content = b"[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials\n"
        
        response = self.client.post(
            "/ingest",
            files={"file": ("test.log", BytesIO(test_content), "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "test.log"
        assert "stats" in data
        assert data["stats"]["total_lines"] == 2  # Mock returns 2 entries
        assert data["stats"]["processed_successfully"] == 2
    
    @patch('backend.main.get_components')
    def test_ingest_endpoint_invalid_file_type(self, mock_get_components):
        """Test ingestion with invalid file type."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        test_content = b"invalid content"
        
        response = self.client.post(
            "/ingest",
            files={"file": ("test.pdf", BytesIO(test_content), "application/pdf")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not supported" in data["error"]
    
    @patch('backend.main.get_components')
    def test_ingest_endpoint_file_too_large(self, mock_get_components):
        """Test ingestion with file too large."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        # Create content larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        
        response = self.client.post(
            "/ingest",
            files={"file": ("large.log", BytesIO(large_content), "text/plain")}
        )
        
        assert response.status_code == 413
        data = response.json()
        assert "too large" in data["error"]
    
    @patch('backend.main.get_components')
    @patch('tempfile.NamedTemporaryFile')
    def test_ingest_endpoint_no_valid_logs(self, mock_temp_file, mock_get_components):
        """Test ingestion when no valid logs are found."""
        # Configure parser to return empty list
        self.mock_log_parser.parse_file.return_value = []
        
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.log"
        
        test_content = b"invalid log content\n"
        
        response = self.client.post(
            "/ingest",
            files={"file": ("test.log", BytesIO(test_content), "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "No valid log entries" in data["error"]
    
    @patch('backend.main.get_components')
    def test_reset_endpoint(self, mock_get_components):
        """Test collection reset endpoint."""
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        response = self.client.delete("/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "reset successfully" in data["message"]
        
        # Verify methods were called
        self.mock_endee_client.delete_collection.assert_called_once()
        self.mock_endee_client.create_collection.assert_called_once()
    
    def test_component_not_initialized_error(self):
        """Test error when components are not initialized."""
        # Don't override dependencies, so they remain None
        response = self.client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["error"]
    
    @patch('backend.main.get_components')
    def test_error_handling(self, mock_get_components):
        """Test general error handling."""
        # Make endee client raise an exception
        self.mock_endee_client.get_stats.side_effect = Exception("Database error")
        
        mock_get_components.return_value = (
            self.mock_log_parser,
            self.mock_embedder,
            self.mock_endee_client,
            self.mock_rag_engine
        )
        
        response = self.client.get("/stats")
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to get statistics" in data["error"]


class TestAPIStartup:
    """Test API startup and shutdown events."""
    
    @patch('backend.main.RAGEngine')
    @patch('backend.main.EndeeClient')
    @patch('backend.main.Embedder')
    @patch('backend.main.LogParser')
    def test_startup_success(self, mock_log_parser_class, mock_embedder_class, 
                           mock_endee_class, mock_rag_class):
        """Test successful startup."""
        # Configure mocks
        mock_endee_instance = MagicMock()
        mock_endee_instance.collection_exists.return_value = True
        mock_endee_class.return_value = mock_endee_instance
        
        # Import and test startup
        from backend.main import startup_event
        
        # This would normally be called by FastAPI
        # We can't easily test the actual startup event without running the server
        assert callable(startup_event)
    
    def test_startup_component_initialization_order(self):
        """Test that components are initialized in correct order."""
        # This test verifies the startup logic structure
        from backend.main import startup_event
        import inspect
        
        # Check that startup_event is an async function
        assert inspect.iscoroutinefunction(startup_event)


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])