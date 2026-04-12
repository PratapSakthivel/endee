"""
ErrorLens Data Models

This module contains all data models used throughout the ErrorLens system.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


@dataclass
class LogEntry:
    """
    Structured representation of a log line.
    
    This dataclass represents a parsed log entry with all extracted fields
    and provides methods for converting to different formats needed by
    the embedding and storage systems.
    """
    severity: str          # ERROR, WARN, INFO, DEBUG, UNKNOWN
    service: str           # Service name or "unknown"
    message: str           # Core error message
    timestamp: str         # ISO 8601 format or "unknown"
    raw_log: str          # Original log text
    line_number: int      # Line number in file
    
    def to_embedding_text(self) -> str:
        """
        Generate text for embedding generation.
        
        Combines severity, service, and message fields into a single string
        that captures the semantic meaning for vector embedding.
        
        Returns:
            str: Formatted text for embedding (e.g., "ERROR auth_service: Invalid credentials")
        """
        return f"{self.severity} {self.service}: {self.message}"
    
    def to_metadata(self) -> Dict[str, Any]:
        """
        Convert to Endee metadata format.
        
        Returns a dictionary containing all log entry fields that will be
        stored as metadata alongside the vector in Endee.
        
        Returns:
            Dict[str, Any]: Metadata dictionary for Endee storage
        """
        return {
            "severity": self.severity,
            "service": self.service,
            "message": self.message,
            "timestamp": self.timestamp,
            "raw_log": self.raw_log,
            "line_number": self.line_number
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"LogEntry(severity={self.severity}, service={self.service}, message={self.message[:50]}...)"


# Pydantic models for API requests and responses

class SearchRequest(BaseModel):
    """Request model for semantic search API."""
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    rag_enabled: bool = Field(default=False, description="Enable RAG analysis")


class SearchResult(BaseModel):
    """Single search result."""
    severity: str = Field(..., description="Log severity level")
    service: str = Field(..., description="Service name")
    message: str = Field(..., description="Log message")
    timestamp: str = Field(..., description="Log timestamp")
    raw_log: str = Field(..., description="Original log text")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")


class SearchResponse(BaseModel):
    """Search API response."""
    query: str = Field(..., description="Original search query")
    results: list[SearchResult] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results returned")
    rag_analysis: Optional[Dict[str, str]] = Field(None, description="RAG analysis if enabled")


class IngestionStats(BaseModel):
    """Ingestion result statistics."""
    status: str = Field(..., description="Status: success or error")
    filename: str = Field(..., description="Uploaded filename")
    stats: Dict[str, Any] = Field(..., description="Processing statistics")


class RAGAnalysis(BaseModel):
    """RAG analysis result."""
    root_cause: str = Field(..., description="Root cause analysis")
    fix_suggestions: str = Field(..., description="Fix suggestions")
    prevention: str = Field(..., description="Prevention recommendations")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    endee_connected: bool = Field(..., description="Endee connectivity status")
    model_loaded: bool = Field(..., description="Embedding model status")


class StatsResponse(BaseModel):
    """Statistics response."""
    collection: str = Field(..., description="Collection name")
    vector_count: int = Field(..., description="Number of vectors")
    dimension: int = Field(..., description="Vector dimension")
    metric: str = Field(..., description="Distance metric")