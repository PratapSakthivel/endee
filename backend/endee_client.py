"""
ErrorLens Endee Client

This module provides a client interface for interacting with the Endee vector database.
Handles index management, vector operations, and search functionality.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from endee import Endee

logger = logging.getLogger(__name__)


class EndeeClient:
    """
    Client for interacting with Endee vector database.
    
    Provides methods for index management, vector upsert, and similarity search.
    Endee is a high-performance vector database running on http://localhost:8080.
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Endee client.
        
        Args:
            base_url (str, optional): Base URL for Endee API. 
                                    Defaults to ENDEE_URL environment variable or http://localhost:8080/api/v1
            timeout (int): Request timeout in seconds. Default is 30.
        """
        self.base_url = base_url or os.getenv("ENDEE_URL", "http://localhost:8080/api/v1")
        self.timeout = timeout
        
        # Initialize Endee SDK client
        self.client = Endee()
        self.client.set_base_url(self.base_url)
        
        # Default index name for ErrorLens
        self.default_index = "error_logs"
        
        logger.info(f"EndeeClient initialized with base_url: {self.base_url}")
        logger.info(f"Default index: {self.default_index}")
        logger.info(f"Request timeout: {timeout}s")
    
    def create_collection(self, name: Optional[str] = None, dimension: int = 384, 
                         metric: str = "cosine") -> Dict[str, Any]:
        """
        Create a new index in Endee.
        
        Args:
            name (str, optional): Index name. Defaults to default_index.
            dimension (int): Vector dimension. Default is 384 for all-MiniLM-L6-v2.
            metric (str): Distance metric. Default is "cosine".
            
        Returns:
            dict: Creation response from Endee
            
        Raises:
            Exception: If index creation fails
        """
        index_name = name or self.default_index
        
        logger.info(f"Creating index '{index_name}' with dimension {dimension} and metric '{metric}'")
        
        try:
            # Check if index already exists
            if self.collection_exists(index_name):
                logger.warning(f"Index '{index_name}' already exists")
                return {"status": "exists", "name": index_name}
            
            # Create index using Endee SDK
            self.client.create_index(
                name=index_name,
                dimension=dimension,
                space_type=metric
            )
            
            logger.info(f"Index '{index_name}' created successfully")
            return {"status": "created", "name": index_name}
            
        except Exception as e:
            logger.error(f"Failed to create index '{index_name}': {e}")
            # If error mentions "already exists", treat as success
            if "already exists" in str(e).lower() or "exist" in str(e).lower():
                logger.warning(f"Index '{index_name}' already exists")
                return {"status": "exists", "name": index_name}
            raise
    
    def collection_exists(self, name: Optional[str] = None) -> bool:
        """
        Check if an index exists.
        
        Args:
            name (str, optional): Index name. Defaults to default_index.
            
        Returns:
            bool: True if index exists, False otherwise
        """
        index_name = name or self.default_index
        
        try:
            # Try to get index info
            indexes = self.client.list_indexes()
            # indexes might be a list of strings or dicts
            if indexes and len(indexes) > 0:
                if isinstance(indexes[0], str):
                    exists = index_name in indexes
                else:
                    exists = index_name in [idx.get("name") if isinstance(idx, dict) else idx for idx in indexes]
            else:
                exists = False
            
            logger.debug(f"Index '{index_name}' exists: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False
    
    def delete_collection(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete an index from Endee.
        
        Args:
            name (str, optional): Index name. Defaults to default_index.
            
        Returns:
            dict: Deletion response from Endee
            
        Raises:
            Exception: If index deletion fails
        """
        index_name = name or self.default_index
        
        logger.info(f"Deleting index '{index_name}'")
        
        try:
            if not self.collection_exists(index_name):
                logger.warning(f"Index '{index_name}' does not exist")
                return {"status": "not_found", "name": index_name}
            
            self.client.delete_index(index_name)
            logger.info(f"Index '{index_name}' deleted successfully")
            return {"status": "deleted", "name": index_name}
            
        except Exception as e:
            logger.error(f"Failed to delete index '{index_name}': {e}")
            if "not found" in str(e).lower():
                logger.warning(f"Index '{index_name}' does not exist")
                return {"status": "not_found", "name": index_name}
            raise
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]], 
                      collection: Optional[str] = None) -> Dict[str, Any]:
        """
        Upsert vectors into an index.
        
        Args:
            vectors (List[Dict]): List of vector objects with id, vector, and metadata
            collection (str, optional): Index name. Defaults to default_index.
            
        Vector format:
            {
                "id": "log_20240115_103045_001",
                "vector": [0.1, 0.2, ...],  # 384-dimensional
                "metadata": {
                    "severity": "ERROR",
                    "service": "auth_service", 
                    "message": "Invalid credentials",
                    "timestamp": "2024-01-15T10:30:45Z",
                    "line_number": 1
                }
            }
            
        Returns:
            dict: Upsert response from Endee
            
        Raises:
            ValueError: If vectors format is invalid
            Exception: If upsert fails
        """
        index_name = collection or self.default_index
        
        if not vectors:
            raise ValueError("Vectors list cannot be empty")
        
        # Validate vector format
        for i, vector in enumerate(vectors):
            if not isinstance(vector, dict):
                raise ValueError(f"Vector at index {i} must be a dictionary")
            
            required_fields = ["id", "vector", "metadata"]
            for field in required_fields:
                if field not in vector:
                    raise ValueError(f"Vector at index {i} missing required field: {field}")
            
            if not isinstance(vector["vector"], list):
                raise ValueError(f"Vector at index {i} 'vector' field must be a list")
            
            if len(vector["vector"]) != 384:
                raise ValueError(f"Vector at index {i} must have 384 dimensions, got {len(vector['vector'])}")
        
        logger.info(f"Upserting {len(vectors)} vectors to index '{index_name}'")
        
        try:
            # Get index object
            index = self.client.get_index(name=index_name)
            
            # Convert to Endee format (meta instead of metadata)
            endee_vectors = []
            for v in vectors:
                endee_vectors.append({
                    "id": v["id"],
                    "vector": v["vector"],
                    "meta": v["metadata"]
                })
            
            # Upsert vectors
            index.upsert(endee_vectors)
            
            logger.info(f"Successfully upserted {len(vectors)} vectors")
            return {"status": "success", "count": len(vectors)}
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise
    
    def search(self, query_vector: List[float], top_k: int = 10, 
              collection: Optional[str] = None, similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Search for similar vectors in an index.
        
        Args:
            query_vector (List[float]): Query vector (384-dimensional)
            top_k (int): Number of results to return. Default is 10.
            collection (str, optional): Index name. Defaults to default_index.
            similarity_threshold (float): Minimum similarity score. Default is 0.3.
            
        Returns:
            dict: Search results from Endee
            
        Result format:
            {
                "results": [
                    {
                        "id": "log_20240115_103045_001",
                        "score": 0.95,
                        "metadata": {
                            "severity": "ERROR",
                            "service": "auth_service",
                            "message": "Invalid credentials",
                            "timestamp": "2024-01-15T10:30:45Z",
                            "line_number": 1
                        }
                    }
                ]
            }
            
        Raises:
            ValueError: If query_vector format is invalid
            Exception: If search fails
        """
        index_name = collection or self.default_index
        
        # Validate query vector
        if not isinstance(query_vector, list):
            raise ValueError("Query vector must be a list")
        
        if len(query_vector) != 384:
            raise ValueError(f"Query vector must have 384 dimensions, got {len(query_vector)}")
        
        if not all(isinstance(x, (int, float)) for x in query_vector):
            raise ValueError("Query vector must contain only numbers")
        
        if top_k < 1 or top_k > 1000:
            raise ValueError("top_k must be between 1 and 1000")
        
        logger.info(f"Searching index '{index_name}' for top {top_k} similar vectors")
        
        try:
            # Get index object
            index = self.client.get_index(name=index_name)
            
            # Search vectors
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                include_vectors=False
            )
            
            # Convert results to our format (meta -> metadata, similarity -> score)
            formatted_results = []
            for r in results:
                if r.get("similarity", 0) >= similarity_threshold:
                    formatted_results.append({
                        "id": r["id"],
                        "score": r["similarity"],
                        "metadata": r.get("meta", {})
                    })
            
            logger.info(f"Found {len(results)} results, {len(formatted_results)} above threshold {similarity_threshold}")
            
            return {
                "results": formatted_results,
                "filtered_count": len(formatted_results),
                "total_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise
    
    def get_stats(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """
        Get index statistics from Endee.
        
        Args:
            collection (str, optional): Index name. Defaults to default_index.
            
        Returns:
            dict: Index statistics
            
        Stats format:
            {
                "collection": "error_logs",
                "vector_count": 1500,
                "dimension": 384,
                "metric": "cosine"
            }
            
        Raises:
            Exception: If stats retrieval fails
        """
        index_name = collection or self.default_index
        
        logger.info(f"Getting statistics for index '{index_name}'")
        
        try:
            # Get index object
            index = self.client.get_index(name=index_name)
            
            # Get index description
            desc = index.describe()
            
            # Format stats
            stats = {
                "collection": index_name,
                "vector_count": desc.get("count", 0),
                "dimension": desc.get("dimension", 384),
                "metric": desc.get("space_type", "cosine")
            }
            
            logger.info(f"Retrieved stats for index '{index_name}': {stats.get('vector_count', 0)} vectors")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if Endee is healthy and reachable.
        
        Returns:
            dict: Health status
            
        Health format:
            {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": "2h 30m"
            }
            
        Raises:
            Exception: If Endee is unreachable
        """
        logger.info("Performing Endee health check")
        
        try:
            # Try to list indexes as a health check
            indexes = self.client.list_indexes()
            
            logger.info(f"Endee health check successful: {len(indexes)} indexes found")
            return {
                "status": "healthy",
                "indexes": len(indexes)
            }
            
        except Exception as e:
            logger.error(f"Endee health check failed: {e}")
            raise
    
    def generate_vector_id(self, line_number: int, timestamp: Optional[str] = None) -> str:
        """
        Generate a unique vector ID for log entries.
        
        Args:
            line_number (int): Line number in the log file
            timestamp (str, optional): Log timestamp. Defaults to current time.
            
        Returns:
            str: Unique vector ID in format "log_YYYYMMDD_HHMMSS_NNN"
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            # Parse and reformat timestamp if needed
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime("%Y%m%d_%H%M%S")
            except Exception:
                # Use as-is if parsing fails
                timestamp = timestamp.replace(':', '').replace('-', '').replace('T', '_')[:15]
        
        vector_id = f"log_{timestamp}_{line_number:03d}"
        logger.debug(f"Generated vector ID: {vector_id}")
        
        return vector_id
    
    def prepare_log_vector(self, log_entry, embedding: List[float], 
                          line_number: int) -> Dict[str, Any]:
        """
        Prepare a log entry for vector upsert.
        
        Args:
            log_entry: LogEntry object
            embedding (List[float]): 384-dimensional embedding vector
            line_number (int): Line number in the log file
            
        Returns:
            dict: Vector object ready for upsert
        """
        vector_id = self.generate_vector_id(line_number, log_entry.timestamp)
        
        vector_obj = {
            "id": vector_id,
            "vector": embedding,
            "metadata": log_entry.to_metadata()
        }
        
        logger.debug(f"Prepared vector object for log entry: {vector_id}")
        
        return vector_obj
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information for debugging.
        
        Returns:
            dict: Connection details
        """
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "default_index": self.default_index
        }