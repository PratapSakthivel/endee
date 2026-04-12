# Implementation Plan: ErrorLens Semantic Log Analyzer

## Overview

This implementation plan breaks down the ErrorLens system into 9 phases, following the blueprint architecture. Each phase builds incrementally with testing and git commits after completion. The system uses Python with FastAPI backend, Streamlit frontend, sentence-transformers for embeddings, and Endee vector database.

## Tasks

- [x] Phase 0: Project Setup and Environment Configuration
  - [x] 0.1 Initialize project structure and directories
    - Create directory structure: backend/, frontend/, frontend/pages/, tests/, data/sample_logs/
    - Create __init__.py files for Python packages
    - _Requirements: 12.1, 13.1_
  
  - [x] 0.2 Create environment configuration files
    - Create .env.example with ENDEE_URL, GROQ_API_KEY, EMBEDDING_MODEL
    - Create .gitignore excluding .env, __pycache__, .pytest_cache, *.pyc
    - _Requirements: 12.1, 12.2, 12.5_
  
  - [x] 0.3 Create requirements.txt with dependencies
    - Add fastapi, uvicorn, streamlit, sentence-transformers, requests, python-dotenv, pydantic, groq
    - Pin versions for reproducibility
    - _Requirements: 12.1_
  
  - [x] 0.4 Create docker-compose.yml
    - Define services: endee (port 8080), backend (port 8000), frontend (port 8501)
    - Configure networking and volume mounts
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ]* 0.5 Write unit tests for environment configuration
    - Test .env loading with default values
    - Test missing GROQ_API_KEY warning
    - _Requirements: 12.3, 12.4_
  
  - [x] 0.6 Checkpoint - Verify project structure
    - Ensure all directories created, docker-compose validates, ask user if questions arise

- [x] Phase 1: Log Parser Implementation
  - [x] 1.1 Implement LogEntry dataclass
    - Create backend/models.py with LogEntry dataclass
    - Add to_embedding_text() and to_metadata() methods
    - _Requirements: 1.1, 1.6_
  
  - [x] 1.2 Implement LogParser class with standard format parsing
    - Create backend/log_parser.py with LogParser class
    - Implement _parse_standard_format() with regex patterns for common log formats
    - Implement parse_line() with fallback to UNKNOWN severity
    - _Requirements: 1.1, 1.4, 1.5, 1.6_
  
  - [x] 1.3 Add JSON log format parsing
    - Implement _parse_json_format() method
    - Handle JSON parsing errors gracefully
    - _Requirements: 1.3, 1.4_
  
  - [x] 1.4 Implement parse_file() method
    - Add file parsing with line-by-line processing
    - Support .log, .txt, .json file extensions
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x]* 1.5 Write property test for log parsing information preservation
    - **Property 1: Log Parsing Information Preservation**
    - **Validates: Requirements 1.1, 1.6**
  
  - [x]* 1.6 Write property test for JSON log parsing correctness
    - **Property 2: JSON Log Parsing Correctness**
    - **Validates: Requirements 1.3**
  
  - [x]* 1.7 Write property test for malformed log graceful handling
    - **Property 3: Malformed Log Graceful Handling**
    - **Validates: Requirements 1.4**
  
  - [x]* 1.8 Write unit tests for LogParser
    - Test standard format parsing with various patterns
    - Test JSON format parsing
    - Test malformed line handling
    - Test file parsing with mixed formats
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 1.9 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [-] Phase 2: Embedder Implementation
  - [x] 2.1 Implement Embedder class initialization
    - Create backend/embedder.py with Embedder class
    - Load sentence-transformers model (all-MiniLM-L6-v2)
    - Implement model caching
    - _Requirements: 2.1, 2.5_
  
  - [x] 2.2 Implement single text embedding
    - Implement embed() method with vector normalization
    - Ensure 384-dimensional output
    - _Requirements: 2.1, 2.3_
  
  - [x] 2.3 Implement batch embedding
    - Implement embed_batch() method using batch encoding
    - _Requirements: 2.4_
  
  - [x] 2.4 Implement embed_log_entry() method
    - Combine severity, service, message fields into embedding text
    - _Requirements: 2.2_
  
  - [ ]* 2.5 Write property test for embedding dimension invariant
    - **Property 4: Embedding Dimension Invariant**
    - **Validates: Requirements 2.1**
  
  - [ ]* 2.6 Write property test for embedding text composition
    - **Property 5: Embedding Text Composition**
    - **Validates: Requirements 2.2**
  
  - [ ]* 2.7 Write property test for vector normalization invariant
    - **Property 6: Vector Normalization Invariant**
    - **Validates: Requirements 2.3**
  
  - [ ]* 2.8 Write property test for batch embedding consistency
    - **Property 7: Batch Embedding Consistency**
    - **Validates: Requirements 2.4**
  
  - [x]* 2.9 Write unit tests for Embedder
    - Test model loading and caching
    - Test single embedding generation
    - Test batch embedding
    - Test embed_log_entry with LogEntry objects
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 2.10 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [ ] Phase 3: Endee Client Implementation
  - [x] 3.1 Implement EndeeClient class initialization
    - Create backend/endee_client.py with EndeeClient class
    - Configure base URL from environment
    - _Requirements: 3.4_
  
  - [x] 3.2 Implement collection management methods
    - Implement create_collection() with dimension 384 and cosine metric
    - Implement collection_exists() method
    - Implement delete_collection() method
    - _Requirements: 3.1, 3.5, 3.6_
  
  - [x] 3.3 Implement vector upsert method
    - Implement upsert_vectors() with metadata schema
    - Generate vector IDs as log_<timestamp>_<line_number>
    - _Requirements: 3.2_
  
  - [x] 3.4 Implement search method
    - Implement search() with query vector and top_k parameter
    - Apply similarity threshold filtering (>0.3)
    - _Requirements: 3.3_
  
  - [x] 3.5 Implement get_stats() method
    - Query Endee for collection statistics
    - _Requirements: 9.2_
  
  - [x]* 3.6 Write unit tests for EndeeClient
    - Mock HTTP requests using pytest-mock or responses library
    - Test collection creation, upsert, search, delete
    - Test error handling for connection failures
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [x] 3.7 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [ ] Phase 4: RAG Engine Implementation
  - [x] 4.1 Implement RAGEngine class initialization
    - Create backend/rag_engine.py with RAGEngine class
    - Initialize with EndeeClient, Embedder, and Groq API key
    - _Requirements: 6.1_
  
  - [x] 4.2 Implement _build_prompt() method
    - Construct LLM prompt with query and retrieved logs
    - Include severity, service, message, and similarity scores
    - _Requirements: 6.2_
  
  - [x] 4.3 Implement _call_groq() method
    - Call Groq API with llama3-8b-8192 model
    - Handle timeouts (30 seconds) and retries
    - Graceful degradation when API unavailable
    - _Requirements: 6.3, 6.5_
  
  - [x] 4.4 Implement analyze() method
    - Retrieve top-5 similar logs from Endee
    - Build prompt and call Groq
    - Parse and structure response
    - _Requirements: 6.1, 6.4, 6.6_
  
  - [ ]* 4.5 Write property test for RAG prompt construction completeness
    - **Property 12: RAG Prompt Construction Completeness**
    - **Validates: Requirements 6.2**
  
  - [ ]* 4.6 Write property test for RAG response structure completeness
    - **Property 13: RAG Response Structure Completeness**
    - **Validates: Requirements 6.4**
  
  - [ ]* 4.7 Write property test for RAG context inclusion
    - **Property 14: RAG Context Inclusion**
    - **Validates: Requirements 6.6**
  
  - [x]* 4.8 Write unit tests for RAGEngine
    - Mock Groq API responses
    - Test prompt construction
    - Test graceful degradation
    - Test response parsing
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 4.9 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [ ] Phase 5: Backend API Implementation
  - [ ] 5.1 Create FastAPI application and Pydantic models
    - Create backend/main.py with FastAPI app
    - Define SearchRequest, SearchResponse, SearchResult, IngestionStats models in backend/models.py
    - _Requirements: 7.1, 8.1_
  
  - [ ] 5.2 Implement POST /ingest endpoint
    - Accept multipart file upload
    - Validate file size (<50MB)
    - Parse, embed, and upsert logs in batches of 100
    - Return ingestion statistics
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ] 5.3 Implement POST /search endpoint
    - Accept query, top_k, rag_enabled parameters
    - Validate query not empty and top_k in range 1-100
    - Embed query and search Endee
    - Optionally call RAG engine
    - Return search results with similarity scores
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 5.4 Implement GET /health endpoint
    - Check Endee connectivity
    - Check model loaded status
    - Return HTTP 200 when healthy, 503 when Endee unreachable
    - _Requirements: 9.1, 9.3_
  
  - [ ] 5.5 Implement GET /stats endpoint
    - Query Endee for collection statistics
    - Return vector count, dimension, collection name
    - _Requirements: 9.2_
  
  - [ ] 5.6 Implement DELETE /reset endpoint
    - Delete and recreate error_logs collection
    - _Requirements: 9.4_
  
  - [ ] 5.7 Add error handling and logging
    - Implement HTTPException handlers for 400, 503, 500 errors
    - Configure Python logging with INFO, WARNING, ERROR levels
    - _Requirements: 7.4, 8.5_
  
  - [ ]* 5.8 Write property test for search results sorting
    - **Property 8: Search Results Sorting**
    - **Validates: Requirements 4.2**
  
  - [ ]* 5.9 Write property test for top-k result constraint
    - **Property 9: Top-K Result Constraint**
    - **Validates: Requirements 4.3**
  
  - [ ]* 5.10 Write property test for search response schema completeness
    - **Property 10: Search Response Schema Completeness**
    - **Validates: Requirements 4.4**
  
  - [ ]* 5.11 Write property test for top-k parameter validation
    - **Property 16: Top-K Parameter Validation**
    - **Validates: Requirements 8.4**
  
  - [ ]* 5.12 Write property test for ingestion statistics completeness
    - **Property 15: Ingestion Statistics Completeness**
    - **Validates: Requirements 7.3**
  
  - [ ]* 5.13 Write unit tests for API endpoints
    - Use FastAPI TestClient
    - Test /ingest with valid and invalid files
    - Test /search with various parameters
    - Test /health, /stats, /reset endpoints
    - Test validation errors (400), service errors (503)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 9.4_
  
  - [ ] 5.14 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [ ] Phase 6: Frontend UI Implementation
  - [ ] 6.1 Create Streamlit main entry point
    - Create frontend/streamlit_app.py with page configuration
    - Configure API URL from environment
    - _Requirements: 10.1_
  
  - [ ] 6.2 Implement Dashboard page
    - Create frontend/pages/1_📊_Dashboard.py
    - Display KPI cards: total errors, unique services
    - Create bar chart for errors by severity
    - Create pie chart for errors by service
    - Call GET /stats endpoint
    - _Requirements: 10.1_
  
  - [ ] 6.3 Implement Ingest page
    - Create frontend/pages/2_📤_Ingest.py
    - Add file uploader for .log, .txt, .json files
    - Validate file size (<50MB)
    - Call POST /ingest endpoint
    - Display ingestion statistics table
    - _Requirements: 10.2_
  
  - [ ] 6.4 Implement Search page
    - Create frontend/pages/3_🔍_Search.py
    - Add query text input
    - Add top_k slider (1-100, default 10)
    - Add RAG toggle
    - Call POST /search endpoint
    - Display results table with severity, service, message, similarity %
    - Add expandable raw log view
    - _Requirements: 10.3, 10.5_
  
  - [ ] 6.5 Implement Root Cause page
    - Create frontend/pages/4_🧠_Root_Cause.py
    - Display query input (pre-filled from search)
    - Show retrieved logs context
    - Display root cause, fix suggestions, prevention sections
    - Show similarity scores for retrieved logs
    - _Requirements: 10.4_
  
  - [ ] 6.6 Add error handling to all pages
    - Handle connection errors with st.error()
    - Handle HTTP errors with detail messages
    - _Requirements: 10.6_
  
  - [ ]* 6.7 Write property test for similarity score percentage formatting
    - **Property 17: Similarity Score Percentage Formatting**
    - **Validates: Requirements 10.5**
  
  - [ ] 6.8 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [ ] Phase 7: Demo Data Generation
  - [ ] 7.1 Create synthetic log generator script
    - Create scripts/generate_demo_data.py
    - Generate 500 log entries across 3 services: auth_service, payment_service, api_gateway
    - Include severity levels: ERROR, WARN, INFO, DEBUG
    - Generate realistic error messages (auth failures, payment errors, API timeouts)
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [ ] 7.2 Output demo log files
    - Write three separate log files to data/sample_logs/
    - Create auth_service.log, payment_service.log, api_gateway.log
    - _Requirements: 11.5_
  
  - [ ]* 7.3 Write unit tests for demo data generator
    - Test log generation produces correct count
    - Test all services and severities represented
    - Test output file creation
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 7.4 Checkpoint - Verify demo data generated
    - Ensure demo files created, ask user if questions arise

- [ ] Phase 8: Integration and Documentation
  - [ ] 8.1 Create comprehensive README.md
    - Add project overview and architecture diagram
    - Document setup instructions (Docker Compose, local development)
    - Document all 9 development phases with estimated time
    - Document REST API endpoints with request/response examples
    - Add troubleshooting section
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_
  
  - [ ] 8.2 Create Dockerfile for backend
    - Create backend/Dockerfile with Python base image
    - Install dependencies from requirements.txt
    - Configure uvicorn startup
    - _Requirements: 13.1_
  
  - [ ] 8.3 Create Dockerfile for frontend
    - Create frontend/Dockerfile with Python base image
    - Install streamlit and dependencies
    - Configure streamlit startup
    - _Requirements: 13.1_
  
  - [ ] 8.4 Update docker-compose.yml with build contexts
    - Add build configurations for backend and frontend services
    - Configure environment variables
    - _Requirements: 13.1, 13.2_
  
  - [ ]* 8.5 Write integration tests
    - Test end-to-end ingestion flow
    - Test end-to-end search flow
    - Test RAG pipeline
    - Use Docker Compose test stack
    - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_
  
  - [ ] 8.6 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask user if questions arise

- [ ] Phase 9: Final Testing and Deployment Preparation
  - [ ] 9.1 Perform manual testing checklist
    - Test file upload for .log, .txt, .json formats
    - Test semantic search with various natural language queries
    - Test RAG analysis quality
    - Test duplicate detection (similarity >0.85)
    - Test error handling (invalid files, empty queries)
    - Test health endpoint
    - Test reset functionality
    - Verify UI responsiveness
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 9.2 Run full Docker Compose stack
    - Execute docker-compose up
    - Verify all services start successfully
    - Test backend on port 8000
    - Test frontend on port 8501
    - Verify Endee connectivity on port 8080
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [ ] 9.3 Ingest demo data and verify system
    - Upload all three demo log files via UI
    - Verify ingestion statistics
    - Perform sample searches
    - Test RAG analysis
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ]* 9.4 Run performance benchmarks
    - Test ingestion speed (target: >100 logs/second)
    - Test search latency (target: <500ms for top-10)
    - Test embedding generation (target: <100ms single entry)
    - Test RAG analysis (target: <5 seconds end-to-end)
  
  - [ ] 9.5 Final checkpoint - System ready for deployment
    - Ensure all tests pass, all documentation complete, ask user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each phase should end with a git commit after successful testing
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The implementation uses Python throughout (FastAPI, Streamlit, sentence-transformers)
- Endee vector database runs as a Docker container
- Groq API requires API key in .env file
