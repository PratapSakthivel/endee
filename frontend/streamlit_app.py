"""
ErrorLens Frontend - Streamlit Application

Main entry point for the ErrorLens Streamlit frontend.
Provides intelligent semantic error log analysis interface.
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="ErrorLens - Semantic Log Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .status-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .status-healthy {
        background-color: #d4edda;
        border: 2px solid #28a745;
        color: #155724;
    }
    .status-unhealthy {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        color: #721c24;
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 10px 0;
    }
    .guide-step {
        background-color: #e7f3ff;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #0066cc;
    }
    .metric-green {
        color: #28a745;
        font-weight: bold;
    }
    .metric-red {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Get API URL from environment
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Store API URL in session state for pages to access
if "api_url" not in st.session_state:
    st.session_state.api_url = API_URL

# Header
st.title("🔍 ErrorLens - Intelligent Semantic Log Analyzer")
st.markdown("### AI-Powered Error Analysis with Vector Search")
st.markdown("---")

# System Status Section
st.header("📊 System Status")

try:
    import requests
    
    with st.spinner("Checking system status..."):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                # Overall system status
                is_healthy = health_data.get("status") == "healthy"
                status_class = "status-healthy" if is_healthy else "status-unhealthy"
                status_icon = "✅" if is_healthy else "❌"
                status_text = "All Systems Operational" if is_healthy else "System Issues Detected"
                
                st.markdown(f"""
                <div class="{status_class}" style="text-align: center;">
                    <h2>{status_icon} {status_text}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Component status
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("### 🖥️ Backend API")
                    st.markdown('<p class="metric-green">● Online</p>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### 🗄️ Vector DB")
                    if health_data.get("endee_connected"):
                        st.markdown('<p class="metric-green">● Connected</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="metric-red">● Disconnected</p>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown("### 🤖 AI Model")
                    if health_data.get("model_loaded"):
                        st.markdown('<p class="metric-green">● Loaded</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="metric-red">● Not Loaded</p>', unsafe_allow_html=True)
                
                with col4:
                    # Check RAG availability
                    try:
                        stats_response = requests.get(f"{API_URL}/stats", timeout=5)
                        st.markdown("### 🧠 RAG Analysis")
                        st.markdown('<p class="metric-green">● Available</p>', unsafe_allow_html=True)
                    except:
                        st.markdown("### 🧠 RAG Analysis")
                        st.markdown('<p class="metric-red">● Unavailable</p>', unsafe_allow_html=True)
                
                if not is_healthy:
                    st.warning("⚠️ Some system components are not fully operational. Please check the status above.")
            else:
                st.error(f"❌ Backend API not responding (HTTP {response.status_code})")
        
        except requests.exceptions.RequestException as e:
            st.markdown(f"""
            <div class="status-unhealthy" style="text-align: center;">
                <h2>❌ Cannot Connect to Backend API</h2>
                <p>Backend URL: {API_URL}</p>
                <p>Make sure the backend server is running on port 8000</p>
            </div>
            """, unsafe_allow_html=True)

except ImportError:
    st.error("❌ Required dependencies not installed. Please install 'requests' package.")

st.markdown("---")

# User Guide Section
st.header("📖 User Guide - How to Use ErrorLens")

st.markdown("""
<div class="guide-step">
    <h3>Step 1: Upload Your Log Files 📤</h3>
    <p><strong>Navigate to:</strong> Ingest page (sidebar)</p>
    <ul>
        <li>Click "Browse files" or drag & drop your log file</li>
        <li>Supported formats: .log, .txt, .json</li>
        <li>Maximum file size: 50MB</li>
        <li>The system will automatically parse and embed your logs</li>
    </ul>
    <p><strong>Sample logs available in:</strong> <code>data/sample_logs/</code></p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="guide-step">
    <h3>Step 2: Monitor Your Dashboard 📊</h3>
    <p><strong>Navigate to:</strong> Dashboard page (sidebar)</p>
    <ul>
        <li>View total number of logs ingested</li>
        <li>Check vector database statistics</li>
        <li>Monitor system health in real-time</li>
        <li>See collection metrics (dimension, metric type)</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="guide-step">
    <h3>Step 3: Search Logs Semantically 🔍</h3>
    <p><strong>Navigate to:</strong> Search page (sidebar)</p>
    <ul>
        <li>Enter a natural language query (e.g., "authentication failures")</li>
        <li>Adjust the number of results (top-k)</li>
        <li>View similar logs ranked by relevance score</li>
        <li>See severity, service, timestamp, and full log message</li>
    </ul>
    <p><strong>Example queries:</strong></p>
    <ul>
        <li>"database connection timeout"</li>
        <li>"payment processing errors"</li>
        <li>"user login failed"</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="guide-step">
    <h3>Step 4: Get AI-Powered Root Cause Analysis 🧠</h3>
    <p><strong>Navigate to:</strong> Root Cause page (sidebar)</p>
    <ul>
        <li>Enter your error description or query</li>
        <li>Enable RAG analysis for intelligent insights</li>
        <li>Get AI-generated root cause analysis</li>
        <li>Receive actionable fix suggestions</li>
        <li>Learn prevention strategies</li>
    </ul>
    <p><strong>Note:</strong> RAG analysis requires Groq API key to be configured</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Features Overview
st.header("✨ Key Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🎯 Semantic Search</h3>
        <p>Find similar errors using natural language queries instead of exact keyword matching. 
        Powered by sentence-transformers embeddings and cosine similarity.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>🤖 AI Root Cause Analysis</h3>
        <p>Get intelligent root cause suggestions and fix recommendations using RAG 
        (Retrieval-Augmented Generation) with Groq LLM.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>⚡ High-Performance Vector Search</h3>
        <p>Powered by Endee vector database for fast and accurate similarity search 
        across millions of log entries.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Real-Time Monitoring</h3>
        <p>Track system health, vector database statistics, and log ingestion metrics 
        in real-time through the dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick Tips
st.header("💡 Quick Tips")

tips_col1, tips_col2 = st.columns(2)

with tips_col1:
    st.markdown("""
    **For Best Results:**
    - Use descriptive queries with error symptoms
    - Include service names in your queries
    - Mention severity levels when relevant
    - Be specific about timing (e.g., "recent login errors")
    """)

with tips_col2:
    st.markdown("""
    **Troubleshooting:**
    - If no results found, try broader queries
    - Check if logs are properly ingested in Dashboard
    - Ensure backend API is running (check status above)
    - Verify Endee vector database is connected
    """)

st.markdown("---")

# Footer
st.markdown("""
### 📚 Additional Resources

- **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs
- **Sample Logs**: Check `data/sample_logs/` directory for example log files
- **GitHub Repository**: [View source code and documentation](https://github.com/PratapSakthivel/endee)

---

**ErrorLens** - Built with ❤️ using Endee Vector Database | Pratap Sakthivel | VSB Engineering College | 2026
""")