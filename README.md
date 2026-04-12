# ErrorLens - Intelligent Semantic Error Log Analyzer

> AI-powered log analysis using vector embeddings and the Endee vector database

## Overview

ErrorLens transforms traditional keyword-based log searching into an intelligent, meaning-aware experience. Instead of grep/regex, ErrorLens uses vector embeddings to understand the semantic meaning of errors.

**Key Features:**
- 🔍 **Semantic Search**: Natural language queries find relevant errors by meaning
- 🤖 **AI Root Cause Analysis**: RAG-powered suggestions using Groq LLM
- 📊 **Duplicate Detection**: Automatically identifies similar errors
- 📁 **Multi-Format Support**: Parses .log, .txt, and .json files
- 🎨 **Interactive UI**: Streamlit dashboard for visualization

## Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Streamlit
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: Endee (Docker)
- **LLM**: Groq API (llama3-8b-8192)

## Project Structure

```
errorlens/
├── backend/              # FastAPI backend
│   ├── __init__.py
│   ├── main.py          # API entry point (Phase 5)
│   ├── log_parser.py    # Log parsing (Phase 1)
│   ├── embedder.py      # Vector embeddings (Phase 2)
│   ├── endee_client.py  # Endee integration (Phase 3)
│   └── rag_engine.py    # RAG analysis (Phase 4)
├── frontend/            # Streamlit UI
│   ├── __init__.py
│   └── streamlit_app.py # Main UI (Phase 6)
├── tests/               # Test suite
│   └── __init__.py
├── data/sample_logs/    # Demo data (Phase 7)
├── scripts/             # Utility scripts
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Endee configuration
├── .env.example         # Environment template
└── README.md           # This file
```

## Prerequisites

- Python 3.10+
- Docker Desktop
- Groq API Key (free at https://console.groq.com)

## Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd errorlens
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_actual_key_here
```

### 5. Start Endee Vector Database

Endee is already running on your system at http://localhost:8080 with 5GB RAM limit.

To verify:
```bash
curl http://localhost:8080/health
```

## Development Phases

This project is built in 9 phases:

- ✅ **Phase 0**: Project Setup (STRUCTURE COMPLETE - Need 64-bit Python for dependencies)
- ⏳ **Phase 1**: Log Parser Implementation
- ⏳ **Phase 2**: Embedder Implementation
- ⏳ **Phase 3**: Endee Client Implementation
- ⏳ **Phase 4**: RAG Engine Implementation
- ⏳ **Phase 5**: Backend API Implementation
- ⏳ **Phase 6**: Frontend UI Implementation
- ⏳ **Phase 7**: Demo Data Generation
- ⏳ **Phase 8**: Integration and Documentation
- ⏳ **Phase 9**: Final Testing and Deployment

## ⚠️ Important: Python Requirement

**ErrorLens requires 64-bit Python 3.10+**

If you have 32-bit Python, please see `SETUP_INSTRUCTIONS.md` for installation guidance.

## Running the Application

### Backend API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

### Frontend UI

```bash
cd frontend
streamlit run streamlit_app.py
```

UI will be available at: http://localhost:8501

## API Endpoints

- `GET /health` - Health check
- `POST /ingest` - Upload and process log files
- `POST /search` - Semantic search with optional RAG
- `GET /stats` - Collection statistics
- `DELETE /reset` - Reset vector collection

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=frontend

# Run specific test file
pytest tests/test_log_parser.py
```

## Contributing

This project is part of the Endee Internship Evaluation 2026.

**Author**: Pratap Sakthivel  
**Institution**: VSB Engineering College  
**Email**: pratapssakthivel@gmail.com

## License

MIT License

## Acknowledgments

- Endee Vector Database: https://github.com/PratapSakthivel/endee
- sentence-transformers: https://www.sbert.net/
- Groq: https://groq.com/
