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

# Get API URL from environment
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Store API URL in session state for pages to access
if "api_url" not in st.session_state:
    st.session_state.api_url = API_URL

# Main page content
st.title("🔍 ErrorLens - Semantic Log Analyzer")
st.markdown("---")

st.markdown("""
## Welcome to ErrorLens

ErrorLens is an intelligent semantic error log analyzer that helps you:

- **📤 Ingest** log files from various formats (.log, .txt, .json)
- **🔍 Search** logs using natural language queries
- **🧠 Analyze** root causes with AI-powered insights
- **📊 Monitor** error patterns and statistics

### Getting Started

1. **📊 Dashboard** - View system statistics and error patterns
2. **📤 Ingest** - Upload your log files for analysis
3. **🔍 Search** - Find relevant logs using semantic search
4. **🧠 Root Cause** - Get AI-powered analysis and fix suggestions

### Navigation

Use the sidebar to navigate between different pages. Each page provides specific functionality for log analysis and monitoring.

### System Status
""")

# Display system status
try:
    import requests
    
    with st.spinner("Checking system status..."):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_color = "🟢" if health_data.get("status") == "healthy" else "🔴"
                    st.metric("System Status", f"{status_color} {health_data.get('status', 'unknown').title()}")
                
                with col2:
                    endee_status = "🟢 Connected" if health_data.get("endee_connected") else "🔴 Disconnected"
                    st.metric("Vector Database", endee_status)
                
                with col3:
                    model_status = "🟢 Loaded" if health_data.get("model_loaded") else "🔴 Not Loaded"
                    st.metric("AI Model", model_status)
                
                if health_data.get("status") != "healthy":
                    st.warning("⚠️ Some system components are not fully operational. Check the health status above.")
            else:
                st.error(f"❌ Backend API not responding (HTTP {response.status_code})")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Cannot connect to backend API at {API_URL}")
            st.info("Make sure the backend server is running on the correct port.")

except ImportError:
    st.error("❌ Required dependencies not installed. Please install 'requests' package.")

st.markdown("---")
st.markdown("""
### Quick Tips

- **Upload logs**: Start by uploading your log files in the Ingest page
- **Natural search**: Use plain English to search for errors (e.g., "authentication failures")
- **AI analysis**: Enable RAG analysis for intelligent root cause suggestions
- **Monitor trends**: Check the Dashboard for error patterns and statistics

### Support

For help and documentation, visit the project repository or check the API documentation at `/docs`.
""")