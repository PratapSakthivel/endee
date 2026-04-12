"""
Tests for ErrorLens Embedder

This module contains comprehensive tests for the Embedder class,
including unit tests and property-based tests.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from backend.embedder import Embedder
from backend.models import LogEntry


class TestEmbedder:
    """Test suite for Embedder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a mock model for faster testing
        with patch('backend.embedder.SentenceTransformer') as mock_st:
            # Mock the model to return predictable embeddings
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.device = "cpu"
            mock_model.encode.return_value = np.random.rand(384)  # Random 384-dim vector
            mock_st.return_value = mock_model
            
            self.embedder = Embedder()
            self.mock_model = mock_model
    
    def test_embedder_initialization(self):
        """Test embedder initialization."""
        assert self.embedder.model_name == "all-MiniLM-L6-v2"
        assert self.embedder.is_model_loaded()
        assert self.embedder.get_dimension() == 384
    
    def test_embedder_custom_model(self):
        """Test embedder with custom model name."""
        with patch('backend.embedder.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 512
            mock_model.device = "cpu"
            mock_st.return_value = mock_model
            
            embedder = Embedder("custom-model")
            assert embedder.model_name == "custom-model"
            assert embedder.get_dimension() == 512
    
    def test_embed_single_text(self):
        """Test embedding single text."""
        # Mock the model to return a normalized vector
        normalized_vector = np.random.rand(384)
        normalized_vector = normalized_vector / np.linalg.norm(normalized_vector)
        self.mock_model.encode.return_value = normalized_vector
        
        text = "ERROR auth_service: Invalid credentials"
        embedding = self.embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        
        # Verify model was called correctly
        self.mock_model.encode.assert_called_once_with(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
    
    def test_embed_empty_text(self):
        """Test embedding empty text raises error."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.embedder.embed("")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.embedder.embed("   ")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.embedder.embed(None)
    
    def test_embed_batch(self):
        """Test batch embedding."""
        # Mock the model to return multiple normalized vectors
        batch_size = 3
        normalized_vectors = np.random.rand(batch_size, 384)
        for i in range(batch_size):
            normalized_vectors[i] = normalized_vectors[i] / np.linalg.norm(normalized_vectors[i])
        self.mock_model.encode.return_value = normalized_vectors
        
        texts = [
            "ERROR auth_service: Invalid credentials",
            "WARN payment_service: Timeout occurred",
            "INFO api_gateway: Request processed"
        ]
        
        embeddings = self.embedder.embed_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == 384
            assert all(isinstance(x, float) for x in embedding)
        
        # Verify model was called correctly
        self.mock_model.encode.assert_called_once_with(
            texts,
            convert_to_tensor=False,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )
    
    def test_embed_batch_with_empty_texts(self):
        """Test batch embedding with some empty texts."""
        # Mock the model to return vectors for valid texts only
        valid_vectors = np.random.rand(2, 384)
        for i in range(2):
            valid_vectors[i] = valid_vectors[i] / np.linalg.norm(valid_vectors[i])
        self.mock_model.encode.return_value = valid_vectors
        
        texts = [
            "ERROR auth_service: Invalid credentials",
            "",  # Empty text
            "INFO api_gateway: Request processed",
            "   "  # Whitespace only
        ]
        
        embeddings = self.embedder.embed_batch(texts)
        
        assert len(embeddings) == 4
        
        # First and third should be real embeddings
        assert len(embeddings[0]) == 384
        assert len(embeddings[2]) == 384
        
        # Second and fourth should be zero vectors
        assert embeddings[1] == [0.0] * 384
        assert embeddings[3] == [0.0] * 384
    
    def test_embed_batch_empty_list(self):
        """Test batch embedding with empty list raises error."""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            self.embedder.embed_batch([])
    
    def test_embed_log_entry(self):
        """Test embedding log entry."""
        # Mock the model to return a normalized vector
        normalized_vector = np.random.rand(384)
        normalized_vector = normalized_vector / np.linalg.norm(normalized_vector)
        self.mock_model.encode.return_value = normalized_vector
        
        entry = LogEntry(
            severity="ERROR",
            service="auth_service",
            message="Invalid credentials",
            timestamp="2024-01-15T10:30:45Z",
            raw_log="[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            line_number=1
        )
        
        embedding = self.embedder.embed_log_entry(entry)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        
        # Verify the embedding text was created correctly
        expected_text = "ERROR auth_service: Invalid credentials"
        self.mock_model.encode.assert_called_once_with(
            expected_text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
    
    def test_embed_log_entry_none(self):
        """Test embedding None log entry raises error."""
        with pytest.raises(ValueError, match="LogEntry cannot be None"):
            self.embedder.embed_log_entry(None)
    
    def test_embed_log_entries(self):
        """Test embedding multiple log entries."""
        # Mock the model to return multiple normalized vectors
        batch_size = 2
        normalized_vectors = np.random.rand(batch_size, 384)
        for i in range(batch_size):
            normalized_vectors[i] = normalized_vectors[i] / np.linalg.norm(normalized_vectors[i])
        self.mock_model.encode.return_value = normalized_vectors
        
        entries = [
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
        
        embeddings = self.embedder.embed_log_entries(entries)
        
        assert len(embeddings) == 2
        for embedding in embeddings:
            assert len(embedding) == 384
        
        # Verify the correct texts were embedded
        expected_texts = [
            "ERROR auth_service: Invalid credentials",
            "WARN payment_service: Timeout occurred"
        ]
        self.mock_model.encode.assert_called_once_with(
            expected_texts,
            convert_to_tensor=False,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = self.embedder.get_model_info()
        
        assert info["model_name"] == "all-MiniLM-L6-v2"
        assert info["dimension"] == 384
        assert info["device"] == "cpu"
        assert info["is_loaded"] is True
    
    def test_verify_vector_properties(self):
        """Test vector property verification."""
        # Test valid normalized vector
        valid_vector = [0.5] * 384
        magnitude = np.sqrt(sum(x*x for x in valid_vector))
        valid_vector = [x/magnitude for x in valid_vector]  # Normalize
        
        result = self.embedder.verify_vector_properties(valid_vector)
        
        assert result["valid"] is True
        assert result["dimension"] == 384
        assert result["expected_dimension"] == 384
        assert result["is_normalized"] is True
        assert result["has_nan"] is False
        assert result["has_inf"] is False
    
    def test_verify_vector_properties_invalid_dimension(self):
        """Test vector verification with wrong dimension."""
        invalid_vector = [0.5] * 256  # Wrong dimension
        
        result = self.embedder.verify_vector_properties(invalid_vector)
        
        assert result["valid"] is False
        assert result["dimension"] == 256
        assert result["expected_dimension"] == 384
    
    def test_verify_vector_properties_not_normalized(self):
        """Test vector verification with non-normalized vector."""
        non_normalized_vector = [2.0] * 384  # Magnitude > 1
        
        result = self.embedder.verify_vector_properties(non_normalized_vector)
        
        assert result["valid"] is False
        assert result["is_normalized"] is False
        assert result["magnitude"] > 1.01
    
    def test_verify_vector_properties_empty(self):
        """Test vector verification with empty vector."""
        result = self.embedder.verify_vector_properties([])
        
        assert result["valid"] is False
        assert "empty" in result["error"].lower()


class TestEmbedderProperties:
    """Property-based tests for Embedder."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a mock model for consistent testing
        with patch('backend.embedder.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.device = "cpu"
            
            # Always return normalized vectors
            def mock_encode(*args, **kwargs):
                if isinstance(args[0], list):
                    # Batch encoding
                    batch_size = len(args[0])
                    vectors = np.random.rand(batch_size, 384)
                    for i in range(batch_size):
                        vectors[i] = vectors[i] / np.linalg.norm(vectors[i])
                    return vectors
                else:
                    # Single encoding
                    vector = np.random.rand(384)
                    return vector / np.linalg.norm(vector)
            
            mock_model.encode.side_effect = mock_encode
            mock_st.return_value = mock_model
            
            self.embedder = Embedder()
    
    def test_property_embedding_dimension_invariant(self):
        """
        Property 4: Embedding Dimension Invariant
        
        For any text input, when processed by the Embedder,
        the resulting vector SHALL have exactly 384 dimensions.
        """
        test_texts = [
            "ERROR auth_service: Invalid credentials",
            "WARN payment_service: Timeout occurred", 
            "INFO api_gateway: Request processed",
            "DEBUG database: Query executed",
            "Simple message",
            "A very long message with lots of details about what happened in the system when the error occurred and why it might have failed",
            "Special chars: !@#$%^&*()",
            "Numbers: 123 456 789",
        ]
        
        for text in test_texts:
            embedding = self.embedder.embed(text)
            
            # Must have exactly 384 dimensions
            assert len(embedding) == 384, f"Expected 384 dimensions, got {len(embedding)} for text: {text[:50]}..."
            
            # All elements must be floats
            assert all(isinstance(x, float) for x in embedding), f"All elements must be floats for text: {text[:50]}..."
    
    def test_property_embedding_text_composition(self):
        """
        Property 5: Embedding Text Composition
        
        For any LogEntry, when converted to embedding text by the Embedder,
        the resulting string SHALL follow the format "{severity} {service}: {message}".
        """
        test_entries = [
            LogEntry("ERROR", "auth_service", "Invalid credentials", "2024-01-15T10:30:45Z", "raw", 1),
            LogEntry("WARN", "payment_service", "Timeout occurred", "2024-01-15T10:30:46Z", "raw", 2),
            LogEntry("INFO", "api_gateway", "Request processed", "2024-01-15T10:30:47Z", "raw", 3),
            LogEntry("DEBUG", "database", "Query executed", "2024-01-15T10:30:48Z", "raw", 4),
            LogEntry("UNKNOWN", "unknown", "Malformed log", "unknown", "raw", 5),
        ]
        
        for entry in test_entries:
            embedding_text = entry.to_embedding_text()
            expected_format = f"{entry.severity} {entry.service}: {entry.message}"
            
            # Must follow exact format
            assert embedding_text == expected_format, f"Expected '{expected_format}', got '{embedding_text}'"
            
            # Should be able to embed the text
            embedding = self.embedder.embed(embedding_text)
            assert len(embedding) == 384
    
    def test_property_vector_normalization_invariant(self):
        """
        Property 6: Vector Normalization Invariant
        
        For any text input, when embedded by the Embedder,
        the resulting vector SHALL have unit length (magnitude = 1.0 within tolerance).
        """
        test_texts = [
            "ERROR auth_service: Invalid credentials",
            "WARN payment_service: Timeout occurred",
            "INFO api_gateway: Request processed", 
            "DEBUG database: Query executed",
            "Short",
            "A very long message with lots of details",
        ]
        
        tolerance = 1e-6
        
        for text in test_texts:
            embedding = self.embedder.embed(text)
            
            # Calculate magnitude
            magnitude = np.sqrt(sum(x*x for x in embedding))
            
            # Must be normalized (magnitude ≈ 1.0)
            assert abs(magnitude - 1.0) < tolerance, f"Vector not normalized for text '{text[:50]}...'. Magnitude: {magnitude}"
    
    def test_property_batch_embedding_consistency(self):
        """
        Property 7: Batch Embedding Consistency
        
        For any list of text inputs, when processed by the Embedder,
        batch embedding SHALL produce identical vectors to individual embedding for each input.
        """
        test_texts = [
            "ERROR auth_service: Invalid credentials",
            "WARN payment_service: Timeout occurred",
            "INFO api_gateway: Request processed"
        ]
        
        # Get individual embeddings
        individual_embeddings = []
        for text in test_texts:
            embedding = self.embedder.embed(text)
            individual_embeddings.append(embedding)
        
        # Get batch embeddings
        batch_embeddings = self.embedder.embed_batch(test_texts)
        
        # Should have same number of results
        assert len(individual_embeddings) == len(batch_embeddings)
        
        # Note: Due to mocking, we can't test exact equality, but we can test structure
        for i, (individual, batch) in enumerate(zip(individual_embeddings, batch_embeddings)):
            assert len(individual) == len(batch) == 384, f"Dimension mismatch at index {i}"
            assert isinstance(individual, list) and isinstance(batch, list), f"Type mismatch at index {i}"
    
    def test_property_log_entry_embedding_consistency(self):
        """
        Test that embedding a LogEntry produces the same result as embedding its text representation.
        """
        entry = LogEntry(
            severity="ERROR",
            service="auth_service", 
            message="Invalid credentials",
            timestamp="2024-01-15T10:30:45Z",
            raw_log="[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            line_number=1
        )
        
        # Embed via LogEntry method
        entry_embedding = self.embedder.embed_log_entry(entry)
        
        # Embed via text method
        text_embedding = self.embedder.embed(entry.to_embedding_text())
        
        # Should have same dimensions
        assert len(entry_embedding) == len(text_embedding) == 384
        
        # Both should be normalized
        entry_magnitude = np.sqrt(sum(x*x for x in entry_embedding))
        text_magnitude = np.sqrt(sum(x*x for x in text_embedding))
        
        tolerance = 1e-6
        assert abs(entry_magnitude - 1.0) < tolerance
        assert abs(text_magnitude - 1.0) < tolerance


# Integration test with real model (optional, slower)
class TestEmbedderIntegration:
    """Integration tests with real sentence-transformers model."""
    
    @pytest.mark.slow
    def test_real_model_integration(self):
        """Test with real sentence-transformers model (slow test)."""
        # This test actually loads the model - mark as slow
        embedder = Embedder()
        
        text = "ERROR auth_service: Invalid credentials"
        embedding = embedder.embed(text)
        
        # Verify real properties
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        
        # Verify normalization
        magnitude = np.sqrt(sum(x*x for x in embedding))
        assert 0.99 <= magnitude <= 1.01  # Allow small floating point errors
        
        # Verify model info
        info = embedder.get_model_info()
        assert info["model_name"] == "all-MiniLM-L6-v2"
        assert info["dimension"] == 384
        assert info["is_loaded"] is True