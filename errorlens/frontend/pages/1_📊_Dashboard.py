"""
ErrorLens Dashboard Page

Displays system statistics, KPIs, and error analysis charts.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="Dashboard - ErrorLens",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard")
st.markdown("System overview and error analysis statistics")

# Get API URL from session state
api_url = st.session_state.get("api_url", "http://localhost:8000")

def fetch_stats() -> Dict[str, Any]:
    """Fetch statistics from the backend API."""
    try:
        response = requests.get(f"{api_url}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch stats: HTTP {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Cannot connect to backend API: {str(e)}")
        return {}

def fetch_health() -> Dict[str, Any]:
    """Fetch health status from the backend API."""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code in [200, 503]:  # 503 is expected for partial health
            return response.json()
        else:
            return {"status": "error", "endee_connected": False, "model_loaded": False}
    except requests.exceptions.RequestException:
        return {"status": "error", "endee_connected": False, "model_loaded": False}

# Fetch data
with st.spinner("Loading dashboard data..."):
    stats_data = fetch_stats()
    health_data = fetch_health()

# System Health Section
st.subheader("🏥 System Health")

col1, col2, col3, col4 = st.columns(4)

with col1:
    status = health_data.get("status", "unknown")
    status_color = "🟢" if status == "healthy" else "🔴" if status == "unhealthy" else "🟡"
    st.metric(
        label="Overall Status",
        value=f"{status_color} {status.title()}"
    )

with col2:
    endee_connected = health_data.get("endee_connected", False)
    endee_status = "🟢 Connected" if endee_connected else "🔴 Disconnected"
    st.metric(
        label="Vector Database",
        value=endee_status
    )

with col3:
    model_loaded = health_data.get("model_loaded", False)
    model_status = "🟢 Loaded" if model_loaded else "🔴 Not Loaded"
    st.metric(
        label="AI Model",
        value=model_status
    )

with col4:
    # Calculate uptime indicator based on health
    uptime_status = "🟢 Online" if status == "healthy" else "🔴 Issues"
    st.metric(
        label="Service Status",
        value=uptime_status
    )

st.markdown("---")

# Statistics Section
st.subheader("📈 Collection Statistics")

if stats_data:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        vector_count = stats_data.get("vector_count", 0)
        st.metric(
            label="Total Log Entries",
            value=f"{vector_count:,}",
            help="Total number of log entries stored in the vector database"
        )
    
    with col2:
        collection_name = stats_data.get("collection", "error_logs")
        st.metric(
            label="Collection",
            value=collection_name,
            help="Name of the active vector collection"
        )
    
    with col3:
        dimension = stats_data.get("dimension", 384)
        st.metric(
            label="Vector Dimension",
            value=f"{dimension}D",
            help="Dimensionality of the embedding vectors"
        )
    
    with col4:
        metric_type = stats_data.get("metric", "cosine")
        st.metric(
            label="Similarity Metric",
            value=metric_type.title(),
            help="Distance metric used for similarity search"
        )
    
    # Storage efficiency
    if vector_count > 0:
        st.markdown("---")
        st.subheader("💾 Storage Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Estimate storage size (rough calculation)
            estimated_size_mb = (vector_count * dimension * 4) / (1024 * 1024)  # 4 bytes per float
            st.metric(
                label="Estimated Vector Storage",
                value=f"{estimated_size_mb:.1f} MB",
                help="Approximate storage size for embedding vectors"
            )
        
        with col2:
            # Calculate average vectors per MB
            if estimated_size_mb > 0:
                vectors_per_mb = vector_count / estimated_size_mb
                st.metric(
                    label="Density",
                    value=f"{vectors_per_mb:.0f} vectors/MB",
                    help="Storage efficiency metric"
                )

else:
    st.info("📊 No statistics available. Make sure the backend API is running and accessible.")

st.markdown("---")

# Quick Actions Section
st.subheader("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

with col2:
    if st.button("📤 Go to Ingest", use_container_width=True):
        st.switch_page("pages/2_📤_Ingest.py")

with col3:
    if st.button("🔍 Go to Search", use_container_width=True):
        st.switch_page("pages/3_🔍_Search.py")

# System Information
st.markdown("---")
st.subheader("ℹ️ System Information")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.markdown(f"""
    **Backend API**: `{api_url}`
    
    **Supported Formats**: .log, .txt, .json
    
    **Max File Size**: 50 MB
    """)

with info_col2:
    st.markdown(f"""
    **Embedding Model**: all-MiniLM-L6-v2
    
    **Batch Processing**: 100 logs/batch
    
    **Search Threshold**: 0.3 similarity
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    ErrorLens Dashboard - Real-time system monitoring and statistics
    </div>
    """,
    unsafe_allow_html=True
)