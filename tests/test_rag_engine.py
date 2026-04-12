"""
Tests for ErrorLens RAG Engine

This module contains comprehensive tests for the RAGEngine class,
including unit tests with mocked Groq API calls.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

from backend.rag_engine import RAGEngine
from backend.endee_client import EndeeClient
from backend.embedder import Embedder


class TestRAGEngine:
    """Test suite for RAGEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_endee_client = MagicMock(spec=EndeeClient)
        self.mock_embedder = MagicMock(spec=Embedder)
        
        # Configure mock embedder
        self.mock_embedder.model_name = "all-MiniLM-L6-v2"
        self.mock_embedder.get_dimension.return_value = 384
        self.mock_embedder.embed.return_value = [0.1] * 384
        
        # Configure mock endee client
        self.mock_endee_client.base_url = "http://test-endee:8080"
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_rag_engine_initialization_with_groq(self, mock_groq_class):
        """Test RAG engine initialization with Groq available."""
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        
        assert engine.endee_client == self.mock_endee_client
        assert engine.embedder == self.mock_embedder
        assert engine.model == "llama3-8b-8192"
        assert engine.groq_available is True
        assert engine.max_context_logs == 5
        assert engine.timeout_seconds == 30
        assert engine.max_retries == 2
        
        mock_groq_class.assert_called_once_with(api_key="test-key")
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', False)
    def test_rag_engine_initialization_without_groq(self):
        """Test RAG engine initialization without Groq library."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        
        assert engine.groq_available is False
        assert engine.groq_client is None
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_rag_engine_initialization_no_api_key(self, mock_groq_class):
        """Test RAG engine initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            engine = RAGEngine(
                endee_client=self.mock_endee_client,
                embedder=self.mock_embedder
            )
            
            assert engine.groq_available is False
            assert engine.groq_client is None
    
    def test_build_prompt_with_logs(self):
        """Test prompt building with retrieved logs."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        query = "Why are users getting authentication errors?"
        retrieved_logs = [
            {
                "id": "log_001",
                "score": 0.95,
                "metadata": {
                    "severity": "ERROR",
                    "service": "auth_service",
                    "message": "Invalid credentials",
                    "timestamp": "2024-01-15T10:30:45Z"
                }
            },
            {
                "id": "log_002",
                "score": 0.87,
                "metadata": {
                    "severity": "WARN",
                    "service": "auth_service",
                    "message": "Multiple failed login attempts",
                    "timestamp": "2024-01-15T10:30:50Z"
                }
            }
        ]
        
        prompt = engine._build_prompt(query, retrieved_logs)
        
        # Check prompt contains key elements
        assert "Why are users getting authentication errors?" in prompt
        assert "ERROR" in prompt
        assert "auth_service" in prompt
        assert "Invalid credentials" in prompt
        assert "similarity: 0.95" in prompt
        assert "Root Cause" in prompt
        assert "Fix Suggestions" in prompt
        assert "Prevention" in prompt
    
    def test_build_prompt_no_logs(self):
        """Test prompt building with no retrieved logs."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        query = "Test query"
        retrieved_logs = []
        
        prompt = engine._build_prompt(query, retrieved_logs)
        
        assert "Test query" in prompt
        assert "None found" in prompt
        assert "Root Cause" in prompt
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_call_groq_success(self, mock_groq_class):
        """Test successful Groq API call."""
        # Setup mock Groq client
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """## Root Cause
Database connection timeout

## Fix Suggestions
1. Increase connection timeout
2. Check database server status

## Prevention
Implement connection pooling"""
        
        mock_groq_instance.chat.completions.create.return_value = mock_response
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        
        result = engine._call_groq("test prompt")
        
        assert result["root_cause"] == "Database connection timeout"
        assert "Increase connection timeout" in result["fix_suggestions"]
        assert "connection pooling" in result["prevention"]
        
        # Verify Groq was called correctly
        mock_groq_instance.chat.completions.create.assert_called_once()
        call_args = mock_groq_instance.chat.completions.create.call_args
        assert call_args[1]["model"] == "llama3-8b-8192"
        assert call_args[1]["max_tokens"] == 1000
        assert call_args[1]["temperature"] == 0.1
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_call_groq_failure_with_retries(self, mock_groq_class):
        """Test Groq API call failure with retries."""
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        # Mock API failure
        mock_groq_instance.chat.completions.create.side_effect = Exception("API Error")
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        engine.max_retries = 1  # Reduce for faster testing
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = engine._call_groq("test prompt")
        
        # Should return graceful degradation response
        assert "API error" in result["root_cause"]
        assert "try again later" in result["fix_suggestions"]
        
        # Should have retried
        assert mock_groq_instance.chat.completions.create.call_count == 2
    
    def test_call_groq_not_available(self):
        """Test Groq API call when Groq is not available."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        engine.groq_available = False
        
        result = engine._call_groq("test prompt")
        
        assert "not available" in result["root_cause"]
        assert "API configuration" in result["fix_suggestions"]
    
    def test_parse_groq_response_structured(self):
        """Test parsing structured Groq response."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        content = """## Root Cause
Database connection timeout due to high load

## Fix Suggestions
1. Increase connection timeout settings
2. Scale database resources
3. Implement connection pooling

## Prevention
Monitor database performance and set up alerts"""
        
        result = engine._parse_groq_response(content)
        
        assert result["root_cause"] == "Database connection timeout due to high load"
        assert "Increase connection timeout" in result["fix_suggestions"]
        assert "Monitor database performance" in result["prevention"]
    
    def test_parse_groq_response_unstructured(self):
        """Test parsing unstructured Groq response."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        content = "The issue appears to be related to authentication failures."
        
        result = engine._parse_groq_response(content)
        
        assert result["root_cause"] == content
        assert "Review the analysis" in result["fix_suggestions"]
    
    def test_parse_groq_response_empty(self):
        """Test parsing empty Groq response."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        result = engine._parse_groq_response("")
        
        assert "Unable to parse" in result["root_cause"]
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_analyze_success(self, mock_groq_class):
        """Test successful RAG analysis."""
        # Setup mocks
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """## Root Cause
Authentication service overload

## Fix Suggestions
Scale the auth service

## Prevention
Implement rate limiting"""
        
        mock_groq_instance.chat.completions.create.return_value = mock_response
        
        # Configure endee client mock
        self.mock_endee_client.search.return_value = {
            "results": [
                {
                    "id": "log_001",
                    "score": 0.95,
                    "metadata": {
                        "severity": "ERROR",
                        "service": "auth_service",
                        "message": "Too many requests",
                        "timestamp": "2024-01-15T10:30:45Z"
                    }
                }
            ]
        }
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        
        result = engine.analyze("Why are auth requests failing?")
        
        # Check result structure
        assert result["query"] == "Why are auth requests failing?"
        assert len(result["retrieved_logs"]) == 1
        assert result["analysis"]["root_cause"] == "Authentication service overload"
        assert "Scale the auth service" in result["analysis"]["fix_suggestions"]
        assert "rate limiting" in result["analysis"]["prevention"]
        
        # Check metadata
        metadata = result["metadata"]
        assert metadata["logs_found"] == 1
        assert metadata["groq_available"] is True
        assert "retrieval_time" in metadata
        assert "analysis_time" in metadata
        assert "total_time" in metadata
        
        # Verify method calls
        self.mock_embedder.embed.assert_called_once_with("Why are auth requests failing?")
        self.mock_endee_client.search.assert_called_once()
    
    def test_analyze_no_logs_found(self):
        """Test analysis when no logs are found."""
        # Configure endee client to return no results
        self.mock_endee_client.search.return_value = {"results": []}
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        engine.groq_available = False  # Disable Groq for this test
        
        result = engine.analyze("Test query")
        
        assert len(result["retrieved_logs"]) == 0
        assert "No similar log entries found" in result["analysis"]["root_cause"]
        assert result["metadata"]["logs_found"] == 0
    
    def test_analyze_error_handling(self):
        """Test analysis error handling."""
        # Make embedder raise an exception
        self.mock_embedder.embed.side_effect = Exception("Embedding failed")
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        result = engine.analyze("Test query")
        
        assert "Analysis failed" in result["analysis"]["root_cause"]
        assert "Embedding failed" in result["analysis"]["root_cause"]
        assert "error" in result["metadata"]
    
    def test_get_engine_info(self):
        """Test getting engine information."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        info = engine.get_engine_info()
        
        assert info["groq_available"] is False
        assert info["groq_model"] == "llama3-8b-8192"
        assert info["max_context_logs"] == 5
        assert info["timeout_seconds"] == 30
        assert info["max_retries"] == 2
        assert info["endee_connected"] == "http://test-endee:8080"
        assert info["embedder_model"] == "all-MiniLM-L6-v2"
        assert info["embedder_dimension"] == 384
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_test_groq_connection_success(self, mock_groq_class):
        """Test successful Groq connection test."""
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_groq_instance.chat.completions.create.return_value = mock_response
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        
        result = engine.test_groq_connection()
        
        assert result["status"] == "connected"
        assert "response_time" in result
        assert result["model"] == "llama3-8b-8192"
        assert result["response_preview"] == "OK"
    
    def test_test_groq_connection_unavailable(self):
        """Test Groq connection test when unavailable."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        engine.groq_available = False
        
        result = engine.test_groq_connection()
        
        assert result["status"] == "unavailable"
        assert "not initialized" in result["error"]
    
    @patch('backend.rag_engine.GROQ_AVAILABLE', True)
    @patch('backend.rag_engine.Groq')
    def test_test_groq_connection_error(self, mock_groq_class):
        """Test Groq connection test with error."""
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        mock_groq_instance.chat.completions.create.side_effect = Exception("Connection failed")
        
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder,
            groq_api_key="test-key"
        )
        
        result = engine.test_groq_connection()
        
        assert result["status"] == "error"
        assert "Connection failed" in result["error"]
    
    def test_set_configuration(self):
        """Test setting engine configuration."""
        engine = RAGEngine(
            endee_client=self.mock_endee_client,
            embedder=self.mock_embedder
        )
        
        # Test valid configuration
        engine.set_configuration(
            max_context_logs=8,
            timeout_seconds=60,
            max_retries=3
        )
        
        assert engine.max_context_logs == 8
        assert engine.timeout_seconds == 60
        assert engine.max_retries == 3
        
        # Test boundary validation
        engine.set_configuration(
            max_context_logs=15,  # Should be capped at 10
            timeout_seconds=200,  # Should be capped at 120
            max_retries=10       # Should be capped at 5
        )
        
        assert engine.max_context_logs == 10
        assert engine.timeout_seconds == 120
        assert engine.max_retries == 5
        
        # Test minimum validation
        engine.set_configuration(
            max_context_logs=0,   # Should be at least 1
            timeout_seconds=1,    # Should be at least 5
            max_retries=-1       # Should be at least 0
        )
        
        assert engine.max_context_logs == 1
        assert engine.timeout_seconds == 5
        assert engine.max_retries == 0


class TestRAGEngineIntegration:
    """Integration tests for RAGEngine (require real services)."""
    
    @pytest.mark.slow
    def test_real_groq_integration(self):
        """Test integration with real Groq API (slow test)."""
        # This test requires a valid Groq API key
        import os
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            pytest.skip("GROQ_API_KEY not available - skipping integration test")
        
        # Create mock dependencies
        mock_endee_client = MagicMock(spec=EndeeClient)
        mock_embedder = MagicMock(spec=Embedder)
        
        mock_embedder.model_name = "all-MiniLM-L6-v2"
        mock_embedder.get_dimension.return_value = 384
        mock_embedder.embed.return_value = [0.1] * 384
        mock_endee_client.base_url = "http://localhost:8080"
        
        # Mock search results
        mock_endee_client.search.return_value = {
            "results": [
                {
                    "id": "log_001",
                    "score": 0.95,
                    "metadata": {
                        "severity": "ERROR",
                        "service": "auth_service",
                        "message": "Connection timeout",
                        "timestamp": "2024-01-15T10:30:45Z"
                    }
                }
            ]
        }
        
        try:
            engine = RAGEngine(
                endee_client=mock_endee_client,
                embedder=mock_embedder,
                groq_api_key=groq_api_key
            )
            
            # Test connection
            connection_result = engine.test_groq_connection()
            assert connection_result["status"] == "connected"
            
            # Test analysis
            result = engine.analyze("Why are users getting connection timeouts?")
            
            assert result["query"] == "Why are users getting connection timeouts?"
            assert len(result["retrieved_logs"]) == 1
            assert "root_cause" in result["analysis"]
            assert "fix_suggestions" in result["analysis"]
            assert "prevention" in result["analysis"]
            assert result["metadata"]["groq_available"] is True
            
        except Exception as e:
            if "API key" in str(e) or "authentication" in str(e).lower():
                pytest.skip(f"Groq API authentication failed - skipping integration test: {e}")
            else:
                raise


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])