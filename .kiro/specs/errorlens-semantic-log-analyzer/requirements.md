# Requirements Document

## Introduction

ErrorLens is an intelligent semantic error log analyzer that uses vector embeddings and the Endee vector database to enable natural language search, duplicate detection, and AI-powered root cause analysis of application error logs. Unlike traditional grep/regex-based log analysis, ErrorLens understands the semantic meaning of errors to provide more intelligent insights.

## Glossary

- **ErrorLens_System**: The complete log analysis application including backend API, frontend UI, and integration with Endee vector database
- **Log_Parser**: Component responsible for parsing log files and extracting structured information
- **Embedder**: Component that generates 384-dimensional vector embeddings from text using sentence-transformers
- **Endee_Client**: Component that interfaces with the Endee vector database REST API
- **RAG_Engine**: Retrieval-Augmented Generation component that combines Endee search results with Groq LLM for root cause suggestions
- **Backend_API**: FastAPI REST service providing log ingestion, search, and statistics endpoints
- **Frontend_UI**: Streamlit-based user interface for interacting with the system
- **Log_Entry**: A single parsed log line containing severity, service, message, timestamp, and raw text
- **Embedding_Vector**: A 384-dimensional numerical vector representing the semantic meaning of text
- **Similarity_Score**: Cosine similarity value between 0 and 1 indicating semantic closeness
- **Collection**: An Endee database collection storing vectors with associated metadata

## Requirements

### Requirement 1: Log File Parsing

**User Story:** As a developer, I want to upload log files in multiple formats, so that I can analyze errors from different services and logging frameworks.

#### Acceptance Criteria

1. WHEN a .log file is uploaded, THE Log_Parser SHALL extract severity, service, message, and timestamp from each line
2. WHEN a .txt file is uploaded, THE Log_Parser SHALL parse it using the same logic as .log files
3. WHEN a .json file is uploaded, THE Log_Parser SHALL parse JSON-formatted log entries
4. WHEN a log line cannot be parsed, THE Log_Parser SHALL store it with severity "UNKNOWN" and preserve the raw text
5. THE Log_Parser SHALL support common log formats including standard syslog and application-specific formats
6. FOR ALL parsed log entries, THE Log_Parser SHALL preserve the original raw log text in metadata

### Requirement 2: Vector Embedding Generation

**User Story:** As a system, I want to convert log text into semantic vectors, so that I can perform similarity-based search and clustering.

#### Acceptance Criteria

1. THE Embedder SHALL generate 384-dimensional vectors using the all-MiniLM-L6-v2 model
2. WHEN a Log_Entry is provided, THE Embedder SHALL combine severity, service, and message fields into embedding text
3. THE Embedder SHALL normalize vectors to unit length for cosine similarity computation
4. WHEN multiple log entries are provided, THE Embedder SHALL support batch embedding generation
5. THE Embedder SHALL cache the sentence-transformers model after first load

### Requirement 3: Endee Vector Database Integration

**User Story:** As a system, I want to store and retrieve log embeddings efficiently, so that I can perform fast semantic search over large log volumes.

#### Acceptance Criteria

1. WHEN the ErrorLens_System starts, THE Endee_Client SHALL create a collection named "error_logs" with dimension 384 and cosine metric
2. WHEN a Log_Entry is embedded, THE Endee_Client SHALL upsert the vector with metadata including severity, service, timestamp, raw_log, and line_number
3. WHEN a search query is received, THE Endee_Client SHALL query Endee with the query embedding and return top-k results
4. THE Endee_Client SHALL communicate with Endee at http://localhost:8080
5. WHEN the collection already exists, THE Endee_Client SHALL reuse it without error
6. WHEN a reset is requested, THE Endee_Client SHALL delete the collection and recreate it

### Requirement 4: Semantic Log Search

**User Story:** As a developer, I want to search logs using natural language queries, so that I can find relevant errors without knowing exact keywords.

#### Acceptance Criteria

1. WHEN a natural language query is provided, THE Backend_API SHALL generate an embedding and search Endee for similar log entries
2. THE Backend_API SHALL return results ranked by Similarity_Score in descending order
3. WHEN top_k parameter is provided, THE Backend_API SHALL return at most top_k results
4. THE Backend_API SHALL include Similarity_Score, severity, service, timestamp, and raw_log in each result
5. WHEN no similar logs are found above threshold 0.3, THE Backend_API SHALL return an empty result set

### Requirement 5: Duplicate Error Detection

**User Story:** As a developer, I want to identify duplicate or similar errors, so that I can understand error patterns and reduce noise.

#### Acceptance Criteria

1. WHEN logs are ingested, THE ErrorLens_System SHALL compute pairwise similarity between new entries and existing entries
2. WHEN two log entries have Similarity_Score above 0.85, THE ErrorLens_System SHALL mark them as potential duplicates
3. THE Frontend_UI SHALL display duplicate groups with count and representative example
4. THE Frontend_UI SHALL allow filtering by duplicate status

### Requirement 6: AI-Powered Root Cause Analysis

**User Story:** As a developer, I want AI-generated root cause suggestions for errors, so that I can resolve issues faster.

#### Acceptance Criteria

1. WHEN a search query is submitted with RAG mode enabled, THE RAG_Engine SHALL retrieve top-5 similar logs from Endee
2. WHEN similar logs are retrieved, THE RAG_Engine SHALL construct a context prompt with the logs and query
3. THE RAG_Engine SHALL send the prompt to Groq API using llama3-8b-8192 model
4. THE RAG_Engine SHALL return a structured response containing root cause analysis and fix suggestions
5. WHEN Groq API is unavailable, THE RAG_Engine SHALL return an error message without crashing
6. THE RAG_Engine SHALL include retrieved log context in the response for transparency

### Requirement 7: Log Ingestion API

**User Story:** As a developer, I want a REST API to ingest log files programmatically, so that I can integrate ErrorLens into my workflow.

#### Acceptance Criteria

1. THE Backend_API SHALL expose POST /ingest endpoint accepting multipart file upload
2. WHEN a file is uploaded to /ingest, THE Backend_API SHALL parse, embed, and store all log entries in Endee
3. THE Backend_API SHALL return ingestion statistics including total lines, successfully parsed, and failed lines
4. WHEN ingestion fails, THE Backend_API SHALL return HTTP 400 with error details
5. THE Backend_API SHALL support files up to 50MB in size
6. WHEN ingestion is in progress, THE Backend_API SHALL process entries in batches of 100

### Requirement 8: Search API

**User Story:** As a developer, I want a REST API to search logs semantically, so that I can query ErrorLens programmatically.

#### Acceptance Criteria

1. THE Backend_API SHALL expose POST /search endpoint accepting query text, top_k, and rag_enabled parameters
2. WHEN rag_enabled is false, THE Backend_API SHALL return search results without LLM analysis
3. WHEN rag_enabled is true, THE Backend_API SHALL include RAG_Engine root cause analysis in response
4. THE Backend_API SHALL validate top_k is between 1 and 100
5. WHEN query text is empty, THE Backend_API SHALL return HTTP 400 with validation error

### Requirement 9: Statistics and Health Monitoring

**User Story:** As a developer, I want to monitor system health and collection statistics, so that I can verify ErrorLens is functioning correctly.

#### Acceptance Criteria

1. THE Backend_API SHALL expose GET /health endpoint returning HTTP 200 when operational
2. THE Backend_API SHALL expose GET /stats endpoint returning vector count, dimension, and collection name
3. WHEN Endee is unreachable, THE Backend_API SHALL return HTTP 503 from /health endpoint
4. THE Backend_API SHALL expose DELETE /reset endpoint to clear all vectors and recreate collection

### Requirement 10: Interactive Web Interface

**User Story:** As a developer, I want a web UI to interact with ErrorLens, so that I can analyze logs without writing API calls.

#### Acceptance Criteria

1. THE Frontend_UI SHALL provide a Dashboard page showing error distribution by severity and service
2. THE Frontend_UI SHALL provide an Ingest page with file upload capability
3. THE Frontend_UI SHALL provide a Search page with query input, top_k slider, and RAG toggle
4. THE Frontend_UI SHALL provide a Root Cause page displaying AI analysis results
5. WHEN search results are displayed, THE Frontend_UI SHALL show Similarity_Score as percentage
6. THE Frontend_UI SHALL display error messages when backend API calls fail

### Requirement 11: Demo Data Generation

**User Story:** As a developer, I want synthetic demo data, so that I can test ErrorLens without real production logs.

#### Acceptance Criteria

1. THE ErrorLens_System SHALL include a script to generate 500 synthetic log entries
2. THE script SHALL generate logs for three services: auth_service, payment_service, and api_gateway
3. THE script SHALL generate logs with severity levels: ERROR, WARN, INFO, DEBUG
4. THE script SHALL generate realistic error messages including authentication failures, payment errors, and API timeouts
5. THE script SHALL output three separate log files in data/sample_logs/ directory

### Requirement 12: Environment Configuration

**User Story:** As a developer, I want environment-based configuration, so that I can deploy ErrorLens in different environments.

#### Acceptance Criteria

1. THE ErrorLens_System SHALL read configuration from .env file
2. THE ErrorLens_System SHALL support configuration for ENDEE_URL, GROQ_API_KEY, and EMBEDDING_MODEL
3. WHEN .env file is missing, THE ErrorLens_System SHALL use default values for ENDEE_URL and EMBEDDING_MODEL
4. WHEN GROQ_API_KEY is missing, THE RAG_Engine SHALL disable RAG functionality and log a warning
5. THE .gitignore file SHALL exclude .env to prevent credential leakage

### Requirement 13: Docker Deployment

**User Story:** As a developer, I want to deploy ErrorLens using Docker Compose, so that I can run the entire stack with one command.

#### Acceptance Criteria

1. THE ErrorLens_System SHALL provide docker-compose.yml defining services for Endee, backend, and frontend
2. WHEN docker-compose up is executed, THE ErrorLens_System SHALL start all services with proper networking
3. THE docker-compose.yml SHALL expose backend on port 8000 and frontend on port 8501
4. THE docker-compose.yml SHALL configure Endee on port 8080
5. THE docker-compose.yml SHALL mount data/sample_logs as volume for easy access

### Requirement 14: Project Documentation

**User Story:** As a developer, I want comprehensive documentation, so that I can understand, deploy, and extend ErrorLens.

#### Acceptance Criteria

1. THE ErrorLens_System SHALL include README.md with project overview, setup instructions, and API documentation
2. THE README.md SHALL document all 9 development phases with estimated time per phase
3. THE README.md SHALL include architecture diagram showing data flow
4. THE README.md SHALL document all REST API endpoints with request/response examples
5. THE README.md SHALL include troubleshooting section for common issues
