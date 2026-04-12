# 🔍 ErrorLens

**Intelligent Semantic Error Log Analyzer & Root Cause Suggester**

ErrorLens is a production-style AI-powered log analysis system that uses **Endee** as the core vector database to store, search, and analyze application error logs semantically. Instead of grep or regex-based keyword search, ErrorLens uses vector embeddings to understand the *meaning* of errors — so you can find similar bugs even if they use completely different words.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![Endee](https://img.shields.io/badge/Vector_DB-Endee-purple.svg)](https://github.com/endeeio/endee)

## 🎯 Problem It Solves

Every software engineering team deals with thousands of log lines daily. Finding:

- **Duplicate Detection** — Duplicate errors across services
- **Root Cause Analysis** — Root cause of a new error quickly  
- **Historical Similarity** — Similar past incidents to a current one

...is painful with traditional tools like ELK Stack or Splunk. ErrorLens brings semantic intelligence to log analysis using Endee vector search.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Log Ingestion** | Upload .log, .txt, or .json log files |
| **Semantic Search** | Natural language query → find similar errors |
| **Duplicate Detection** | Group similar/identical error entries using cosine similarity |
| **Root Cause AI** | RAG pipeline: Endee retrieval + Groq LLM suggestion |
| **Dashboard** | Visual overview of error clusters and severity distribution |

## 🏗️ System Architecture

### High-Level Flow

```
Log File Upload → Parse → Embed → Store in Endee
User Query → Embed Query → Endee Cosine Search → Top-K Results → Groq LLM → Root Cause
```

### Data Flow - Ingestion

1. **Parse** each log line → extract severity, service, message, timestamp
2. **Combine** fields into embedding text string  
3. **Generate** 384-dim embedding via sentence-transformers
4. **Store** in Endee with full metadata (severity, service, timestamp, raw_log, line_number)

### Data Flow - Search

1. **User** types natural language query
2. **Generate** embedding for query text
3. **Send** to Endee → cosine similarity search → top-k results
4. **Display** results with similarity scores
5. **(RAG mode)** Top-k results fed to Groq LLM → returns root cause + fix suggestion

## 🛠️ Tech Stack

| Layer | Technology | Why? |
|-------|------------|------|
| **Vector Database** | Endee (Docker) | Core of project — high-performance vector storage + cosine search |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Free, local, 384-dim, fast and accurate |
| **Backend API** | FastAPI (Python) | Clean REST API, auto docs, async support |
| **LLM (RAG)** | Groq API — llama3-8b-8192 | Free API, ultra-fast inference for root cause suggestions |
| **UI** | Streamlit | Build impressive UI in pure Python — no frontend needed |
| **Log Parsing** | Python (regex + json) | Handles plain text, JSON, stack traces |
| **Containerization** | Docker + Docker Compose | One command to run Endee locally |

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (64-bit required)
- **Docker Desktop** 
- **8GB+ RAM** (16GB preferred)
- **Groq API Key** (free at https://console.groq.com)

### 1. Clone & Setup

```bash
git clone https://github.com/PratapSakthivel/endee.git
cd endee

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Start Endee Vector Database

```bash
docker compose up -d
```

Verify Endee is running:
```bash
curl http://localhost:8080/health
# Should return: {"status": "ok"}
```

### 4. Start ErrorLens

**Terminal 1 - Backend API:**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend UI:**
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

### 5. Access ErrorLens

- **Frontend UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📖 Usage Guide

### 1. Dashboard 📊
- View system health (Vector DB, AI Model, Service Status)
- Monitor collection statistics and storage metrics
- Quick navigation to other features

### 2. Ingest Logs 📤
- Upload .log, .txt, or .json files (max 50MB)
- Automatic parsing and embedding generation
- Batch processing (100 logs/batch) with progress tracking
- **Try the demo data**: Upload files from `data/sample_logs/`

### 3. Semantic Search 🔍
- Type natural language queries:
  - "authentication failures"
  - "payment processing errors" 
  - "database connection timeouts"
- Adjust top-k results (1-100)
- View similarity scores and raw logs
- **Enable RAG** for AI-powered analysis

### 4. Root Cause Analysis 🧠
- Describe your error in plain English
- Get AI-powered insights:
  - **Root Cause**: What likely caused the issue
  - **Fix Suggestions**: Specific steps to resolve
  - **Prevention**: How to avoid similar issues
- View retrieved similar logs with similarity scores

## 🎯 Demo Workflow (2 minutes)

```bash
# 1. Start the system
docker compose up -d
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
streamlit run frontend/streamlit_app.py --server.port 8501

# 2. Upload demo data
# Go to http://localhost:8501 → Ingest → Upload data/sample_logs/auth_service.log

# 3. Search semantically  
# Go to Search → Type "login failed" → Enable RAG → Search

# 4. Get AI analysis
# Go to Root Cause → Type "users cannot authenticate" → Analyze
```

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check if API is running |
| `/ingest` | POST | Upload log file → embed → store in Endee |
| `/search` | POST | Semantic search over stored logs + optional RAG |
| `/stats` | GET | Collection stats (vector count, dimension) |
| `/reset` | DELETE | Clear all vectors, recreate collection |

### Example API Usage

**Ingest Logs:**
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_logs/auth_service.log"
```

**Search Logs:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication failed",
    "top_k": 10,
    "rag_enabled": true
  }'
```

**Get Statistics:**
```bash
curl http://localhost:8000/stats
```

## 🗂️ Project Structure

```
errorlens/
├── backend/                  # FastAPI backend
│   ├── main.py              # API entry point
│   ├── log_parser.py        # Log file parsing logic
│   ├── embedder.py          # sentence-transformers wrapper
│   ├── endee_client.py      # All Endee API calls
│   ├── rag_engine.py        # Groq LLM root cause suggestion
│   └── models.py            # Pydantic data models
├── frontend/                 # Streamlit UI
│   ├── streamlit_app.py     # Main entry point
│   └── pages/               # Individual pages
│       ├── 1_📊_Dashboard.py
│       ├── 2_📤_Ingest.py
│       ├── 3_🔍_Search.py
│       └── 4_🧠_Root_Cause.py
├── data/sample_logs/         # Demo log files
│   ├── auth_service.log     # Authentication errors
│   ├── payment_service.log  # Payment processing errors
│   └── api_gateway.log      # API gateway errors
├── scripts/
│   └── generate_demo_data.py # Synthetic log generator
├── tests/                    # Comprehensive test suite
├── docker-compose.yml        # Endee configuration
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🧪 Demo Data

ErrorLens includes **500 realistic synthetic log entries** across 3 services:

- **auth_service** (167 logs): Authentication failures, JWT errors, LDAP issues
- **payment_service** (167 logs): Card declines, fraud detection, transaction errors  
- **api_gateway** (166 logs): Rate limits, timeouts, circuit breakers

**Severity Distribution:**
- **ERROR** (~30%): Critical failures requiring immediate attention
- **WARN** (~25%): Warning conditions that may lead to errors
- **INFO** (~35%): Normal operational messages
- **DEBUG** (~10%): Detailed trace information

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_log_parser.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

### Development Phases

ErrorLens was built in 9 phases following a systematic approach:

| Phase | Component | Status | Description |
|-------|-----------|--------|-------------|
| 0 | Project Setup | ✅ | Environment, dependencies, structure |
| 1 | Log Parser | ✅ | Multi-format log parsing (.log, .txt, .json) |
| 2 | Embedder | ✅ | sentence-transformers integration |
| 3 | Endee Client | ✅ | Vector database operations |
| 4 | RAG Engine | ✅ | Groq LLM integration |
| 5 | Backend API | ✅ | FastAPI REST endpoints |
| 6 | Frontend UI | ✅ | Streamlit multi-page application |
| 7 | Demo Data | ✅ | Synthetic log generation |
| 8 | Integration | 🔄 | Docker, documentation |
| 9 | Final Testing | ⏳ | End-to-end validation |

### Adding New Log Formats

1. **Extend LogParser** in `backend/log_parser.py`
2. **Add regex patterns** for your format
3. **Update tests** in `tests/test_log_parser.py`
4. **Test with sample files**

### Customizing Embeddings

1. **Change model** in `backend/embedder.py`
2. **Update dimension** in `backend/endee_client.py`
3. **Retrain/reindex** existing data

## 🚀 Deployment

### Option 1: Render.com (Recommended, Free)

1. Push code to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your repository
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. **Environment Variables**:
   - `GROQ_API_KEY`: Your Groq API key
   - `ENDEE_URL`: Your hosted Endee instance URL

### Option 2: Docker Compose (Full Stack)

```bash
# Build and run all services
docker compose up --build

# Services will be available at:
# - Endee: http://localhost:8080
# - Backend: http://localhost:8000  
# - Frontend: http://localhost:8501
```

### Option 3: Railway.app

1. New Project → Deploy from GitHub
2. Add environment variables
3. Railway auto-detects Python + starts FastAPI

## 🔍 How Endee Powers ErrorLens

ErrorLens uses **Endee** as its core vector database for several key reasons:

### Why Endee?

- **High Performance**: Optimized for similarity search with cosine distance
- **Simple API**: RESTful interface that's easy to integrate
- **Docker Ready**: One command deployment with `docker compose up -d`
- **Scalable**: Handles thousands of log vectors efficiently
- **Memory Efficient**: 5GB RAM configuration for development

### Endee Integration

```python
# Collection Creation
POST /collections
{
  "name": "error_logs",
  "dimension": 384,
  "metric": "cosine"
}

# Vector Upsert
POST /collections/error_logs/upsert
{
  "vectors": [
    {
      "id": "log_20240412_001",
      "vector": [0.1, 0.2, ...],  # 384 dimensions
      "metadata": {
        "severity": "ERROR",
        "service": "auth_service", 
        "message": "Authentication failed",
        "timestamp": "2024-04-12 10:30:00"
      }
    }
  ]
}

# Similarity Search
POST /collections/error_logs/search
{
  "vector": [0.1, 0.2, ...],  # Query embedding
  "top_k": 10,
  "threshold": 0.3
}
```

### Vector Storage Schema

Each log entry is stored as a vector with rich metadata:

```json
{
  "id": "log_20240412_001",
  "vector": [384 float values],
  "metadata": {
    "severity": "ERROR|WARN|INFO|DEBUG",
    "service": "service_name", 
    "message": "original_log_message",
    "timestamp": "2024-04-12 10:30:00",
    "raw_log": "full_original_log_line",
    "line_number": 1
  }
}
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Endee Team** - For the excellent vector database
- **Groq** - For fast LLM inference API
- **Hugging Face** - For sentence-transformers
- **FastAPI & Streamlit** - For excellent Python frameworks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/PratapSakthivel/endee/issues)
- **Documentation**: [API Docs](http://localhost:8000/docs) (when running)
- **Endee Docs**: [Endee Documentation](https://github.com/endeeio/endee)

---

**Built with ❤️ by [Pratap Sakthivel](https://github.com/PratapSakthivel) | VSB Engineering College | Endee Internship 2026**

*ErrorLens - Making error analysis intelligent, one log at a time.* 🔍✨