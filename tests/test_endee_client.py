"""
Tests for ErrorLens EndeeClient

This module contains comprehensive tests for the EndeeClient class,
including unit tests with mocked HTTP requests.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import requests

from backend.endee_client import EndeeClient
from backend.models import LogEntry


class TestEndeeClient:
    """Test suite for EndeeClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = EndeeClient(base_url="http://test-endee:8080")
        
    def test_client_initialization(self):
        """Test client initialization."""
        # Test with custom URL
        client = EndeeClient("http://custom:9000")
        assert client.base_url == "http://custom:9000"
        assert client.default_collection == "error_logs"
        assert client.timeout == 30
        
        # Test with environment variable
        with patch.dict('os.environ', {'ENDEE_URL': 'http://env:8080'}):
            client = EndeeClient()
            assert client.base_url == "http://env:8080"
        
        # Test with trailing slash removal
        client = EndeeClient("http://test:8080/")
        assert client.base_url == "http://test:8080"
    
    @patch('requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_request.return_value = mock_response
        
        result = self.client._make_request("GET", "/test")
        
        assert result == {"status": "success"}
        mock_request.assert_called_once_with(
            method="GET",
            url="http://test-endee:8080/test",
            json=None,
            params=None,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
    
    @patch('requests.request')
    def test_make_request_connection_error(self, mock_request):
        """Test connection error handling."""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError, match="Cannot connect to Endee"):
            self.client._make_request("GET", "/test")
    
    @patch('requests.request')
    def test_make_request_timeout(self, mock_request):
        """Test timeout error handling."""
        mock_request.side_effect = requests.exceptions.Timeout("Timeout")
        
        with pytest.raises(ConnectionError, match="Request to Endee timed out"):
            self.client._make_request("GET", "/test")
    
    @patch('requests.request')
    def test_make_request_http_error(self, mock_request):
        """Test HTTP error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Error")
        mock_request.return_value = mock_response
        
        with pytest.raises(requests.HTTPError, match="Endee API error 404"):
            self.client._make_request("GET", "/test")
    
    @patch('requests.request')
    def test_make_request_invalid_json(self, mock_request):
        """Test invalid JSON response handling."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON"
        mock_request.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid JSON response from Endee"):
            self.client._make_request("GET", "/test")
    
    @patch.object(EndeeClient, '_make_request')
    def test_create_collection(self, mock_request):
        """Test collection creation."""
        mock_request.return_value = {"status": "created", "name": "error_logs"}
        
        result = self.client.create_collection()
        
        assert result["status"] == "created"
        mock_request.assert_called_once_with(
            "POST", 
            "/collections", 
            data={
                "name": "error_logs",
                "dimension": 384,
                "metric": "cosine"
            }
        )
    
    @patch.object(EndeeClient, '_make_request')
    def test_create_collection_custom_params(self, mock_request):
        """Test collection creation with custom parameters."""
        mock_request.return_value = {"status": "created", "name": "custom_logs"}
        
        result = self.client.create_collection(
            name="custom_logs",
            dimension=512,
            metric="euclidean"
        )
        
        assert result["status"] == "created"
        mock_request.assert_called_once_with(
            "POST",
            "/collections",
            data={
                "name": "custom_logs", 
                "dimension": 512,
                "metric": "euclidean"
            }
        )
    
    @patch.object(EndeeClient, '_make_request')
    def test_create_collection_already_exists(self, mock_request):
        """Test collection creation when collection already exists."""
        mock_request.side_effect = requests.HTTPError("Collection already exists")
        
        result = self.client.create_collection()
        
        assert result["status"] == "exists"
        assert result["name"] == "error_logs"
    
    @patch.object(EndeeClient, '_make_request')
    def test_collection_exists_true(self, mock_request):
        """Test collection existence check - exists."""
        mock_request.return_value = {"name": "error_logs", "dimension": 384}
        
        exists = self.client.collection_exists()
        
        assert exists is True
        mock_request.assert_called_once_with("GET", "/collections/error_logs")
    
    @patch.object(EndeeClient, '_make_request')
    def test_collection_exists_false(self, mock_request):
        """Test collection existence check - does not exist."""
        mock_request.side_effect = requests.HTTPError("404 Not Found")
        
        exists = self.client.collection_exists()
        
        assert exists is False
    
    @patch.object(EndeeClient, '_make_request')
    def test_delete_collection(self, mock_request):
        """Test collection deletion."""
        mock_request.return_value = {"status": "deleted", "name": "error_logs"}
        
        result = self.client.delete_collection()
        
        assert result["status"] == "deleted"
        mock_request.assert_called_once_with("DELETE", "/collections/error_logs")
    
    @patch.object(EndeeClient, '_make_request')
    def test_delete_collection_not_found(self, mock_request):
        """Test collection deletion when collection doesn't exist."""
        mock_request.side_effect = requests.HTTPError("404 Not Found")
        
        result = self.client.delete_collection()
        
        assert result["status"] == "not_found"
        assert result["name"] == "error_logs"
    
    def test_upsert_vectors_validation(self):
        """Test vector upsert validation."""
        # Test empty vectors
        with pytest.raises(ValueError, match="Vectors list cannot be empty"):
            self.client.upsert_vectors([])
        
        # Test invalid vector format
        with pytest.raises(ValueError, match="must be a dictionary"):
            self.client.upsert_vectors(["invalid"])
        
        # Test missing required fields
        with pytest.raises(ValueError, match="missing required field"):
            self.client.upsert_vectors([{"id": "test"}])
        
        # Test invalid vector type
        with pytest.raises(ValueError, match="'vector' field must be a list"):
            self.client.upsert_vectors([{
                "id": "test",
                "vector": "invalid",
                "metadata": {}
            }])
        
        # Test wrong vector dimension
        with pytest.raises(ValueError, match="must have 384 dimensions"):
            self.client.upsert_vectors([{
                "id": "test",
                "vector": [0.1, 0.2],  # Wrong dimension
                "metadata": {}
            }])
    
    @patch.object(EndeeClient, '_make_request')
    def test_upsert_vectors_success(self, mock_request):
        """Test successful vector upsert."""
        mock_request.return_value = {"status": "success", "upserted": 2}
        
        vectors = [
            {
                "id": "log_001",
                "vector": [0.1] * 384,
                "metadata": {
                    "severity": "ERROR",
                    "service": "auth_service",
                    "message": "Invalid credentials"
                }
            },
            {
                "id": "log_002", 
                "vector": [0.2] * 384,
                "metadata": {
                    "severity": "WARN",
                    "service": "payment_service",
                    "message": "Timeout occurred"
                }
            }
        ]
        
        result = self.client.upsert_vectors(vectors)
        
        assert result["status"] == "success"
        assert result["upserted"] == 2
        
        mock_request.assert_called_once_with(
            "POST",
            "/vectors/upsert",
            data={
                "collection": "error_logs",
                "vectors": vectors
            }
        )
    
    def test_search_validation(self):
        """Test search parameter validation."""
        # Test invalid query vector type
        with pytest.raises(ValueError, match="Query vector must be a list"):
            self.client.search("invalid")
        
        # Test wrong vector dimension
        with pytest.raises(ValueError, match="must have 384 dimensions"):
            self.client.search([0.1, 0.2])
        
        # Test non-numeric values
        with pytest.raises(ValueError, match="must contain only numbers"):
            self.client.search([0.1] * 383 + ["invalid"])
        
        # Test invalid top_k
        with pytest.raises(ValueError, match="top_k must be between 1 and 1000"):
            self.client.search([0.1] * 384, top_k=0)
        
        with pytest.raises(ValueError, match="top_k must be between 1 and 1000"):
            self.client.search([0.1] * 384, top_k=1001)
    
    @patch.object(EndeeClient, '_make_request')
    def test_search_success(self, mock_request):
        """Test successful vector search."""
        mock_request.return_value = {
            "results": [
                {
                    "id": "log_001",
                    "score": 0.95,
                    "metadata": {
                        "severity": "ERROR",
                        "service": "auth_service",
                        "message": "Invalid credentials"
                    }
                },
                {
                    "id": "log_002",
                    "score": 0.25,  # Below threshold
                    "metadata": {
                        "severity": "INFO",
                        "service": "api_gateway",
                        "message": "Request processed"
                    }
                }
            ]
        }
        
        query_vector = [0.1] * 384
        result = self.client.search(query_vector, top_k=5, similarity_threshold=0.3)
        
        # Should filter out results below threshold
        assert len(result["results"]) == 1
        assert result["results"][0]["score"] == 0.95
        assert result["filtered_count"] == 1
        
        mock_request.assert_called_once_with(
            "POST",
            "/vectors/search",
            data={
                "collection": "error_logs",
                "vector": query_vector,
                "top_k": 5
            }
        )
    
    @patch.object(EndeeClient, '_make_request')
    def test_get_stats(self, mock_request):
        """Test getting collection statistics."""
        mock_request.return_value = {
            "collection": "error_logs",
            "vector_count": 1500,
            "dimension": 384,
            "metric": "cosine"
        }
        
        result = self.client.get_stats()
        
        assert result["collection"] == "error_logs"
        assert result["vector_count"] == 1500
        assert result["dimension"] == 384
        
        mock_request.assert_called_once_with("GET", "/collections/error_logs/stats")
    
    @patch.object(EndeeClient, '_make_request')
    def test_health_check(self, mock_request):
        """Test health check."""
        mock_request.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": "2h 30m"
        }
        
        result = self.client.health_check()
        
        assert result["status"] == "healthy"
        assert result["version"] == "1.0.0"
        
        mock_request.assert_called_once_with("GET", "/health")
    
    def test_generate_vector_id(self):
        """Test vector ID generation."""
        # Test with custom timestamp
        vector_id = self.client.generate_vector_id(
            line_number=42,
            timestamp="2024-01-15T10:30:45Z"
        )
        
        assert vector_id.startswith("log_20240115_103045")
        assert vector_id.endswith("_042")
        
        # Test with current timestamp (no timestamp provided)
        vector_id = self.client.generate_vector_id(line_number=1)
        
        assert vector_id.startswith("log_")
        assert vector_id.endswith("_001")
        assert len(vector_id.split("_")) == 4  # log_YYYYMMDD_HHMMSS_NNN
    
    def test_prepare_log_vector(self):
        """Test log vector preparation."""
        log_entry = LogEntry(
            severity="ERROR",
            service="auth_service",
            message="Invalid credentials",
            timestamp="2024-01-15T10:30:45Z",
            raw_log="[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            line_number=1
        )
        
        embedding = [0.1] * 384
        
        vector_obj = self.client.prepare_log_vector(log_entry, embedding, line_number=42)
        
        assert vector_obj["id"].startswith("log_20240115_103045")
        assert vector_obj["id"].endswith("_042")
        assert vector_obj["vector"] == embedding
        assert vector_obj["metadata"]["severity"] == "ERROR"
        assert vector_obj["metadata"]["service"] == "auth_service"
        assert vector_obj["metadata"]["message"] == "Invalid credentials"
    
    def test_get_connection_info(self):
        """Test getting connection information."""
        info = self.client.get_connection_info()
        
        assert info["base_url"] == "http://test-endee:8080"
        assert info["timeout"] == 30
        assert info["default_collection"] == "error_logs"


class TestEndeeClientIntegration:
    """Integration tests for EndeeClient (require running Endee)."""
    
    @pytest.mark.slow
    def test_real_endee_connection(self):
        """Test connection to real Endee instance (slow test)."""
        # This test requires Endee to be running on localhost:8080
        client = EndeeClient()
        
        try:
            # Test health check
            health = client.health_check()
            assert "status" in health
            
            # Test collection operations
            collection_name = "test_collection"
            
            # Clean up any existing test collection
            try:
                client.delete_collection(collection_name)
            except:
                pass  # Ignore if doesn't exist
            
            # Create collection
            result = client.create_collection(collection_name)
            assert result["status"] in ["created", "exists"]
            
            # Check if collection exists
            exists = client.collection_exists(collection_name)
            assert exists is True
            
            # Test vector operations
            test_vectors = [
                {
                    "id": "test_001",
                    "vector": [0.1] * 384,
                    "metadata": {
                        "severity": "ERROR",
                        "service": "test_service",
                        "message": "Test message"
                    }
                }
            ]
            
            # Upsert vectors
            upsert_result = client.upsert_vectors(test_vectors, collection_name)
            assert "status" in upsert_result
            
            # Search vectors
            query_vector = [0.1] * 384
            search_result = client.search(query_vector, top_k=5, collection=collection_name)
            assert "results" in search_result
            
            # Get stats
            stats = client.get_stats(collection_name)
            assert stats["vector_count"] >= 1
            
            # Clean up
            client.delete_collection(collection_name)
            
        except (ConnectionError, ValueError) as e:
            if "Invalid JSON response" in str(e) or "Cannot connect" in str(e):
                pytest.skip("Endee not running or not configured properly - skipping integration test")
            else:
                raise


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])