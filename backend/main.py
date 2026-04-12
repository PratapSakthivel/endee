"""
ErrorLens FastAPI Backend

This module provides the REST API endpoints for the ErrorLens system.
Handles log ingestion, semantic search, and RAG analysis.
"""

import logging
import os
import tempfile
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import (
    SearchRequest, SearchResponse, SearchResult, 
    IngestionStats, RAGAnalysis, HealthResponse, StatsResponse
)
from .log_parser import LogParser
from .embedder import Embedder
from .endee_client import EndeeClient
from .rag_engine import RAGEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ErrorLens API",
    description="Intelligent Semantic Error Log Analyzer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized on startup)
log_parser: Optional[LogParser] = None
embedder: Optional[Embedder] = None
endee_client: Optional[EndeeClient] = None
rag_engine: Optional[RAGEngine] = None

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
BATCH_SIZE = 100  # Process logs in batches
ALLOWED_EXTENSIONS = {'.log', '.txt', '.json'}


@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup."""
    global log_parser, embedder, endee_client, rag_engine
    
    logger.info("Starting ErrorLens API...")
    
    try:
        # Initialize components
        logger.info("Initializing LogParser...")
        log_parser = LogParser()
        
        logger.info("Initializing Embedder...")
        embedder = Embedder()
        
        logger.info("Initializing EndeeClient...")
        endee_client = EndeeClient()
        
        logger.info("Initializing RAGEngine...")
        rag_engine = RAGEngine(
            endee_client=endee_client,
            embedder=embedder
        )
        
        # Ensure Endee collection exists
        logger.info("Ensuring Endee collection exists...")
        try:
            if not endee_client.collection_exists():
                endee_client.create_collection()
                logger.info("Created default collection in Endee")
            else:
                logger.info("Default collection already exists in Endee")
        except Exception as e:
            logger.warning(f"Could not verify/create Endee collection: {e}")
        
        logger.info("ErrorLens API startup complete!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down ErrorLens API...")


def get_components():
    """Dependency to get initialized components."""
    if not all([log_parser, embedder, endee_client, rag_engine]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service components not initialized"
        )
    return log_parser, embedder, endee_client, rag_engine


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Check file size (approximate, since we can't get exact size without reading)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )


@app.post("/ingest", response_model=IngestionStats)
async def ingest_logs(
    file: UploadFile = File(...),
    components = Depends(get_components)
):
    """
    Ingest log file and store vectors in Endee.
    
    Accepts .log, .txt, or .json files up to 50MB.
    Processes logs in batches and returns ingestion statistics.
    """
    parser, embedder_comp, endee_comp, _ = components
    
    # Validate file
    validate_file(file)
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting ingestion of file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Check actual file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Parse logs
        logger.info("Parsing log entries...")
        # Decode content to string
        content_str = content.decode('utf-8')
        log_entries = parser.parse_file(content_str, file.filename)
        
        if not log_entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid log entries found in file"
            )
        
        # Process in batches
        total_processed = 0
        total_errors = 0
        batch_count = 0
        
        for i in range(0, len(log_entries), BATCH_SIZE):
            batch = log_entries[i:i + BATCH_SIZE]
            batch_count += 1
            
            logger.info(f"Processing batch {batch_count} ({len(batch)} entries)")
            
            try:
                # Generate embeddings for batch
                embeddings = embedder_comp.embed_log_entries(batch)
                
                # Prepare vectors for Endee
                vectors = []
                for j, (entry, embedding) in enumerate(zip(batch, embeddings)):
                    vector_obj = endee_comp.prepare_log_vector(
                        entry, embedding, entry.line_number
                    )
                    vectors.append(vector_obj)
                
                # Upsert to Endee
                endee_comp.upsert_vectors(vectors)
                
                total_processed += len(batch)
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_count}: {e}")
                total_errors += len(batch)
        
        processing_time = time.time() - start_time
        
        # Prepare statistics
        stats = {
            "total_lines": len(log_entries),
            "processed_successfully": total_processed,
            "processing_errors": total_errors,
            "processing_time_seconds": round(processing_time, 2),
            "batches_processed": batch_count,
            "logs_per_second": round(total_processed / processing_time, 2) if processing_time > 0 else 0
        }
        
        logger.info(f"Ingestion complete: {total_processed}/{len(log_entries)} entries processed in {processing_time:.2f}s")
        
        return IngestionStats(
            status="success" if total_errors == 0 else "partial_success",
            filename=file.filename,
            stats=stats
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post("/search", response_model=SearchResponse)
async def search_logs(
    request: SearchRequest,
    components = Depends(get_components)
):
    """
    Perform semantic search on ingested logs.
    
    Optionally includes RAG analysis for root cause and fix suggestions.
    """
    _, embedder_comp, endee_comp, rag_comp = components
    
    try:
        logger.info(f"Search request: '{request.query}' (top_k={request.top_k}, rag={request.rag_enabled})")
        
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = embedder_comp.embed(request.query)
        
        # Search Endee
        search_result = endee_comp.search(
            query_vector=query_embedding,
            top_k=request.top_k,
            similarity_threshold=0.3
        )
        
        # Convert results to API format
        results = []
        for result in search_result.get("results", []):
            metadata = result.get("metadata", {})
            
            search_result_obj = SearchResult(
                severity=metadata.get("severity", "UNKNOWN"),
                service=metadata.get("service", "unknown"),
                message=metadata.get("message", ""),
                timestamp=metadata.get("timestamp", "unknown"),
                raw_log=metadata.get("raw_log", ""),
                similarity_score=result.get("score", 0.0)
            )
            results.append(search_result_obj)
        
        # Perform RAG analysis if requested
        rag_analysis = None
        if request.rag_enabled and rag_comp.groq_available:
            try:
                logger.info("Performing RAG analysis...")
                rag_result = rag_comp.analyze(request.query, top_k=5)
                rag_analysis = rag_result.get("analysis", {})
            except Exception as e:
                logger.warning(f"RAG analysis failed: {e}")
                rag_analysis = {
                    "root_cause": f"RAG analysis failed: {str(e)[:100]}",
                    "fix_suggestions": "Please try again or analyze the search results manually",
                    "prevention": "Ensure RAG service is properly configured"
                }
        elif request.rag_enabled and not rag_comp.groq_available:
            rag_analysis = {
                "root_cause": "RAG analysis unavailable - Groq API not configured",
                "fix_suggestions": "Configure GROQ_API_KEY environment variable to enable RAG analysis",
                "prevention": "Ensure proper API configuration for intelligent analysis"
            }
        
        search_time = time.time() - start_time
        logger.info(f"Search completed in {search_time:.2f}s, found {len(results)} results")
        
        return SearchResponse(
            query=request.query,
            results=results,
            count=len(results),
            rag_analysis=rag_analysis
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check(components = Depends(get_components)):
    """
    Check system health and component status.
    """
    _, embedder_comp, endee_comp, rag_comp = components
    
    try:
        # Check Endee connectivity
        endee_connected = False
        try:
            endee_comp.health_check()
            endee_connected = True
        except Exception as e:
            logger.warning(f"Endee health check failed: {e}")
        
        # Check model status
        model_loaded = embedder_comp.is_model_loaded()
        
        # Determine overall status
        if endee_connected and model_loaded:
            status_code = status.HTTP_200_OK
            health_status = "healthy"
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            health_status = "unhealthy"
        
        response = HealthResponse(
            status=health_status,
            endee_connected=endee_connected,
            model_loaded=model_loaded
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response.dict()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "endee_connected": False,
                "model_loaded": False,
                "error": str(e)
            }
        )


@app.get("/stats", response_model=StatsResponse)
async def get_stats(components = Depends(get_components)):
    """
    Get collection statistics from Endee.
    """
    _, _, endee_comp, _ = components
    
    try:
        stats = endee_comp.get_stats()
        
        return StatsResponse(
            collection=stats.get("collection", "error_logs"),
            vector_count=stats.get("vector_count", 0),
            dimension=stats.get("dimension", 384),
            metric=stats.get("metric", "cosine")
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get statistics: {str(e)}"
        )


@app.delete("/reset")
async def reset_collection(components = Depends(get_components)):
    """
    Reset the error logs collection (delete and recreate).
    """
    _, _, endee_comp, _ = components
    
    try:
        logger.info("Resetting error logs collection...")
        
        # Delete existing collection
        try:
            endee_comp.delete_collection()
            logger.info("Deleted existing collection")
        except Exception as e:
            logger.warning(f"Failed to delete collection (may not exist): {e}")
        
        # Create new collection
        endee_comp.create_collection()
        logger.info("Created new collection")
        
        return {"status": "success", "message": "Collection reset successfully"}
        
    except Exception as e:
        logger.error(f"Failed to reset collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset collection: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ErrorLens API",
        "version": "1.0.0",
        "description": "Intelligent Semantic Error Log Analyzer",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "stats": "/stats",
            "ingest": "/ingest",
            "search": "/search",
            "reset": "/reset"
        }
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "status_code": 500}
    )


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )