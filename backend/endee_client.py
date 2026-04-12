"""
ErrorLens Endee Client

This module provides a client interface for interacting with the Endee vector database.
Handles collection management, vector operations, and search functionality.
"""

import logging
import os
import requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EndeeClient:
    """
    Client for interacting with Endee vector database.
    
    Provides methods for collection management, vector upsert, and similarity search.
    Endee is a REST API-based vector database running on http://localhost:8080.
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Endee client.
        
        Args:
            base_url (str, optional): Base URL for Endee API. 
                                    Defaults to ENDEE_URL environment variable or http://localhost:8080
            timeout (int): Request timeout in seconds. Default is 30.
        """
        self.base_url = base_url or os.getenv("ENDEE_URL", "http://localhost:8080")
        self.timeout = timeout
        
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip('/')
        
        # Default collection name for ErrorLens
        self.default_collection = "error_logs"
        
        logger.info(f"EndeeClient initialized with base_url: {self.base_url}")
        logger.info(f"Default collection: {self.default_collection}")
        logger.info(f"Request timeout: {timeout}s")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to Endee API.
        
        Args:
            method (str): HTTP method (GET, POST, DELETE)
            endpoint (str): API endpoint (without base URL)
            data (dict, optional): JSON data for POST requests
            params (dict, optional): Query parameters
            
        Returns:
            dict: Response JSON data
            
        Raises:
            ConnectionError: If Endee is unreachable
            requests.HTTPError: If HTTP error occurs
            ValueError: If response is not valid JSON
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            if data:
                logger.debug(f"Request data: {json.dumps(data, indent=2)}")
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                result = response.json()
                logger.debug(f"Response data: {json.dumps(result, indent=2)}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {response.text}")
                raise ValueError(f"Invalid JSON response from Endee: {e}")
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Endee at {self.base_url}: {e}")
            raise ConnectionError(f"Cannot connect to Endee at {self.base_url}. Is Endee running?")
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout after {self.timeout}s: {e}")
            raise ConnectionError(f"Request to Endee timed out after {self.timeout}s")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code}: {response.text}")
            raise requests.HTTPError(f"Endee API error {response.status_code}: {response.text}")
    
    def create_collection(self, name: Optional[str] = None, dimension: int = 384, 
                         metric: str = "cosine") -> Dict[str, Any]:
        """
        Create a new collection in Endee.
        
        Args:
            name (str, optional): Collection name. Defaults to default_collection.
            dimension (int): Vector dimension. Default is 384 for all-MiniLM-L6-v2.
            metric (str): Distance metric. Default is "cosine".
            
        Returns:
            dict: Creation response from Endee
            
        Raises:
            ConnectionError: If Endee is unreachable
            requests.HTTPError: If collection creation fails
        """
        collection_name = name or self.default_collection
        
        data = {
            "name": collection_name,
            "dimension": dimension,
            "metric": metric
        }
        
        logger.info(f"Creating collection '{collection_name}' with dimension {dimension} and metric '{metric}'")
        
        try:
            result = self._make_request("POST", "/collections", data=data)
            logger.info(f"Collection '{collection_name}' created successfully")
            return result
            
        except requests.HTTPError as e:
            if "already exists" in str(e).lower():
                logger.warning(f"Collection '{collection_name}' already exists")
                return {"status": "exists", "name": collection_name}
            else:
                logger.error(f"Failed to create collection '{collection_name}': {e}")
                raise
    
    def collection_exists(self, name: Optional[str] = None) -> bool:
        """
        Check if a collection exists.
        
        Args:
            name (str, optional): Collection name. Defaults to default_collection.
            
        Returns:
            bool: True if collection exists, False otherwise
        """
        collection_name = name or self.default_collection
        
        try:
            # Try to get collection info
            self._make_request("GET", f"/collections/{collection_name}")
            logger.debug(f"Collection '{collection_name}' exists")
            return True
            
        except requests.HTTPError as e:
            if "404" in str(e):
                logger.debug(f"Collection '{collection_name}' does not exist")
                return False
            else:
                logger.error(f"Error checking collection existence: {e}")
                raise
    
    def delete_collection(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a collection from Endee.
        
        Args:
            name (str, optional): Collection name. Defaults to default_collection.
            
        Returns:
            dict: Deletion response from Endee
            
        Raises:
            ConnectionError: If Endee is unreachable
            requests.HTTPError: If collection deletion fails
        """
        collection_name = name or self.default_collection
        
        logger.info(f"Deleting collection '{collection_name}'")
        
        try:
            result = self._make_request("DELETE", f"/collections/{collection_name}")
            logger.info(f"Collection '{collection_name}' deleted successfully")
            return result
            
        except requests.HTTPError as e:
            if "404" in str(e):
                logger.warning(f"Collection '{collection_name}' does not exist")
                return {"status": "not_found", "name": collection_name}
            else:
                logger.error(f"Failed to delete collection '{collection_name}': {e}")
                raise
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]], 
                      collection: Optional[str] = None) -> Dict[str, Any]:
        """
        Upsert vectors into a collection.
        
        Args:
            vectors (List[Dict]): List of vector objects with id, vector, and metadata
            collection (str, optional): Collection name. Defaults to default_collection.
            
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
            ConnectionError: If Endee is unreachable
            requests.HTTPError: If upsert fails
        """
        collection_name = collection or self.default_collection
        
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
        
        data = {
            "collection": collection_name,
            "vectors": vectors
        }
        
        logger.info(f"Upserting {len(vectors)} vectors to collection '{collection_name}'")
        
        try:
            result = self._make_request("POST", "/vectors/upsert", data=data)
            logger.info(f"Successfully upserted {len(vectors)} vectors")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise
    
    def search(self, query_vector: List[float], top_k: int = 10, 
              collection: Optional[str] = None, similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Search for similar vectors in a collection.
        
        Args:
            query_vector (List[float]): Query vector (384-dimensional)
            top_k (int): Number of results to return. Default is 10.
            collection (str, optional): Collection name. Defaults to default_collection.
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
            ConnectionError: If Endee is unreachable
            requests.HTTPError: If search fails
        """
        collection_name = collection or self.default_collection
        
        # Validate query vector
        if not isinstance(query_vector, list):
            raise ValueError("Query vector must be a list")
        
        if len(query_vector) != 384:
            raise ValueError(f"Query vector must have 384 dimensions, got {len(query_vector)}")
        
        if not all(isinstance(x, (int, float)) for x in query_vector):
            raise ValueError("Query vector must contain only numbers")
        
        if top_k < 1 or top_k > 1000:
            raise ValueError("top_k must be between 1 and 1000")
        
        data = {
            "collection": collection_name,
            "vector": query_vector,
            "top_k": top_k
        }
        
        logger.info(f"Searching collection '{collection_name}' for top {top_k} similar vectors")
        
        try:
            result = self._make_request("POST", "/vectors/search", data=data)
            
            # Filter results by similarity threshold
            if "results" in result:
                filtered_results = [
                    r for r in result["results"] 
                    if r.get("score", 0) >= similarity_threshold
                ]
                
                logger.info(f"Found {len(result['results'])} results, {len(filtered_results)} above threshold {similarity_threshold}")
                
                result["results"] = filtered_results
                result["filtered_count"] = len(filtered_results)
                result["total_count"] = len(result.get("results", []))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise
    
    def get_stats(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """
        Get collection statistics from Endee.
        
        Args:
            collection (str, optional): Collection name. Defaults to default_collection.
            
        Returns:
            dict: Collection statistics
            
        Stats format:
            {
                "collection": "error_logs",
                "vector_count": 1500,
                "dimension": 384,
                "metric": "cosine"
            }
            
        Raises:
            ConnectionError: If Endee is unreachable
            requests.HTTPError: If stats retrieval fails
        """
        collection_name = collection or self.default_collection
        
        logger.info(f"Getting statistics for collection '{collection_name}'")
        
        try:
            result = self._make_request("GET", f"/collections/{collection_name}/stats")
            logger.info(f"Retrieved stats for collection '{collection_name}': {result.get('vector_count', 0)} vectors")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
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
            ConnectionError: If Endee is unreachable
        """
        logger.info("Performing Endee health check")
        
        try:
            result = self._make_request("GET", "/health")
            logger.info(f"Endee health check successful: {result.get('status', 'unknown')}")
            return result
            
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
            "default_collection": self.default_collection
        }