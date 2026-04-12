"""
ErrorLens Embedder

This module provides vector embedding functionality using sentence-transformers.
Converts log text into 384-dimensional semantic vectors for similarity search.
"""

import logging
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch

from .models import LogEntry

logger = logging.getLogger(__name__)


class Embedder:
    """
    Vector embedder using sentence-transformers for semantic log analysis.
    
    Uses the all-MiniLM-L6-v2 model to generate 384-dimensional vectors
    that capture the semantic meaning of log entries for similarity search.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedder with sentence-transformers model.
        
        Args:
            model_name (str): Name of the sentence-transformers model to use.
                            Default is "all-MiniLM-L6-v2" (384 dimensions, 22M parameters)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
        
        logger.info(f"Embedder initialized with model: {model_name}")
        logger.info(f"Model device: {self.model.device}")
        logger.info(f"Vector dimension: {self.get_dimension()}")
    
    def _load_model(self):
        """Load the sentence-transformers model with caching."""
        try:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            
            # Load model (will cache automatically after first download)
            self.model = SentenceTransformer(self.model_name)
            
            # Set to evaluation mode for inference
            self.model.eval()
            
            logger.info(f"Model loaded successfully. Dimension: {self.get_dimension()}")
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise RuntimeError(f"Could not load embedding model: {e}")
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for single text.
        
        Args:
            text (str): Input text to embed
            
        Returns:
            List[float]: 384-dimensional normalized vector
            
        Raises:
            ValueError: If text is empty or None
            RuntimeError: If model is not loaded
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or None")
        
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        try:
            # Generate embedding
            with torch.no_grad():  # Disable gradient computation for inference
                embedding = self.model.encode(
                    text.strip(),
                    convert_to_tensor=False,  # Return numpy array
                    normalize_embeddings=True  # Normalize to unit length
                )
            
            # Convert to list of floats
            if isinstance(embedding, np.ndarray):
                embedding_list = embedding.tolist()
            else:
                embedding_list = list(embedding)
            
            logger.debug(f"Generated embedding for text: '{text[:50]}...' (dim: {len(embedding_list)})")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text '{text[:50]}...': {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for batch of texts.
        
        More efficient than calling embed() multiple times as it processes
        texts in parallel using the model's batch processing capabilities.
        
        Args:
            texts (List[str]): List of input texts to embed
            
        Returns:
            List[List[float]]: List of 384-dimensional normalized vectors
            
        Raises:
            ValueError: If texts list is empty or contains invalid entries
            RuntimeError: If model is not loaded
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        # Filter out empty texts and keep track of indices
        valid_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text.strip())
                valid_indices.append(i)
            else:
                logger.warning(f"Skipping empty text at index {i}")
        
        if not valid_texts:
            raise ValueError("No valid texts found in input list")
        
        try:
            logger.info(f"Generating embeddings for batch of {len(valid_texts)} texts")
            
            # Generate embeddings in batch
            with torch.no_grad():
                embeddings = self.model.encode(
                    valid_texts,
                    convert_to_tensor=False,  # Return numpy array
                    normalize_embeddings=True,  # Normalize to unit length
                    batch_size=32,  # Process in batches of 32
                    show_progress_bar=len(valid_texts) > 100  # Show progress for large batches
                )
            
            # Convert to list of lists
            if isinstance(embeddings, np.ndarray):
                embeddings_list = embeddings.tolist()
            else:
                embeddings_list = [list(emb) for emb in embeddings]
            
            # Create result list with None for invalid texts
            result = [None] * len(texts)
            for i, embedding in zip(valid_indices, embeddings_list):
                result[i] = embedding
            
            # Replace None with zero vectors for consistency
            dimension = self.get_dimension()
            zero_vector = [0.0] * dimension
            
            for i in range(len(result)):
                if result[i] is None:
                    result[i] = zero_vector
                    logger.warning(f"Using zero vector for empty text at index {i}")
            
            logger.info(f"Generated {len(embeddings_list)} embeddings successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise RuntimeError(f"Batch embedding generation failed: {e}")
    
    def embed_log_entry(self, entry: LogEntry) -> List[float]:
        """
        Generate embedding from LogEntry fields.
        
        Combines severity, service, and message fields into embedding text
        using the LogEntry.to_embedding_text() method.
        
        Args:
            entry (LogEntry): Log entry to embed
            
        Returns:
            List[float]: 384-dimensional normalized vector
            
        Raises:
            ValueError: If entry is None
            RuntimeError: If embedding generation fails
        """
        if entry is None:
            raise ValueError("LogEntry cannot be None")
        
        try:
            # Use LogEntry's method to create embedding text
            embedding_text = entry.to_embedding_text()
            
            logger.debug(f"Embedding log entry: {embedding_text}")
            
            return self.embed(embedding_text)
            
        except Exception as e:
            logger.error(f"Failed to embed log entry: {e}")
            raise RuntimeError(f"Log entry embedding failed: {e}")
    
    def embed_log_entries(self, entries: List[LogEntry]) -> List[List[float]]:
        """
        Generate embeddings for multiple log entries.
        
        Args:
            entries (List[LogEntry]): List of log entries to embed
            
        Returns:
            List[List[float]]: List of 384-dimensional normalized vectors
            
        Raises:
            ValueError: If entries list is empty or None
            RuntimeError: If embedding generation fails
        """
        if not entries:
            raise ValueError("Entries list cannot be empty")
        
        try:
            # Convert log entries to embedding texts
            embedding_texts = [entry.to_embedding_text() for entry in entries]
            
            logger.info(f"Embedding {len(entries)} log entries")
            
            return self.embed_batch(embedding_texts)
            
        except Exception as e:
            logger.error(f"Failed to embed log entries: {e}")
            raise RuntimeError(f"Log entries embedding failed: {e}")
    
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            int: Vector dimension (384 for all-MiniLM-L6-v2)
        """
        if self.model is None:
            return 384  # Default dimension for all-MiniLM-L6-v2
        
        try:
            # Get dimension from model
            return self.model.get_sentence_embedding_dimension()
        except Exception:
            return 384  # Fallback
    
    def is_model_loaded(self) -> bool:
        """
        Check if the model is loaded and ready.
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            dict: Model information including name, dimension, device
        """
        return {
            "model_name": self.model_name,
            "dimension": self.get_dimension(),
            "device": str(self.model.device) if self.model else "not_loaded",
            "is_loaded": self.is_model_loaded()
        }
    
    def verify_vector_properties(self, vector: List[float]) -> dict:
        """
        Verify that a vector has the expected properties.
        
        Args:
            vector (List[float]): Vector to verify
            
        Returns:
            dict: Verification results including dimension, magnitude, etc.
        """
        if not vector:
            return {"valid": False, "error": "Vector is empty"}
        
        try:
            # Convert to numpy for calculations
            vec_array = np.array(vector)
            
            # Calculate magnitude
            magnitude = np.linalg.norm(vec_array)
            
            # Check dimension
            dimension = len(vector)
            expected_dimension = self.get_dimension()
            
            return {
                "valid": dimension == expected_dimension and 0.99 <= magnitude <= 1.01,
                "dimension": dimension,
                "expected_dimension": expected_dimension,
                "magnitude": float(magnitude),
                "is_normalized": 0.99 <= magnitude <= 1.01,
                "has_nan": bool(np.isnan(vec_array).any()),
                "has_inf": bool(np.isinf(vec_array).any())
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}