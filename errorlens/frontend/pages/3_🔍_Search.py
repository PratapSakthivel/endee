"""
ErrorLens Search Page

Provides semantic search interface for log analysis.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="Search - ErrorLens",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Semantic Log Search")
st.markdown("Search logs using natural language queries")

# Get API URL from session state
api_url = st.session_state.get("api_url", "http://localhost:8000")

def perform_search(query: str, top_k: int, rag_enabled: bool) -> Dict[str, Any]:
    """Perform search request to backend API."""
    try:
        payload = {
            "query": query,
            "top_k": top_k,
            "rag_enabled": rag_enabled
        }
        
        with st.spinner("Searching logs..."):
            response = requests.post(
                f"{api_url}/search",
                json=payload,
                timeout=30
            )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("error", error_data.get("detail", str(error_data)))
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            
            return {"success": False, "error": error_detail}
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Search timeout - query took too long"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def format_similarity_score(score: float) -> str:
    """Format similarity score as percentage."""
    return f"{score * 100:.1f}%"

def get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        "ERROR": "🔴",
        "WARN": "🟡", 
        "WARNING": "🟡",
        "INFO": "🔵",
        "DEBUG": "⚪",
        "UNKNOWN": "⚫"
    }
    return colors.get(severity.upper(), "⚫")

# Initialize session state
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# Search interface
st.subheader("🎯 Search Parameters")

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Search Query",
        placeholder="e.g., authentication failures, payment errors, database timeouts...",
        help="Use natural language to describe what you're looking for",
        value=st.session_state.last_query
    )

with col2:
    top_k = st.slider(
        "Max Results",
        min_value=1,
        max_value=100,
        value=10,
        help="Maximum number of results to return"
    )

# Advanced options
with st.expander("⚙️ Advanced Options"):
    col1, col2 = st.columns(2)
    
    with col1:
        rag_enabled = st.checkbox(
            "🧠 Enable AI Analysis",
            value=True,
            help="Get intelligent root cause analysis and fix suggestions"
        )
    
    with col2:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Minimum similarity score for results (backend uses 0.3)"
        )

# Search button
search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

# Perform search
if search_clicked and query.strip():
    st.session_state.last_query = query
    result = perform_search(query, top_k, rag_enabled)
    st.session_state.search_results = result

elif search_clicked and not query.strip():
    st.error("❌ Please enter a search query")

# Display results
if st.session_state.search_results:
    result = st.session_state.search_results
    
    if result["success"]:
        data = result["data"]
        results = data.get("results", [])
        count = data.get("count", 0)
        rag_analysis = data.get("rag_analysis")
        
        st.markdown("---")
        st.subheader(f"📋 Search Results ({count} found)")
        
        if count > 0:
            # Results summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Results Found", f"{count:,}")
            
            with col2:
                if results:
                    avg_similarity = sum(r.get("similarity_score", 0) for r in results) / len(results)
                    st.metric("Avg Similarity", format_similarity_score(avg_similarity))
            
            with col3:
                if results:
                    unique_services = len(set(r.get("service", "unknown") for r in results))
                    st.metric("Services", f"{unique_services}")
            
            # Results table
            st.markdown("### 📊 Results Table")
            
            # Create results data for table
            table_data = []
            for i, result_item in enumerate(results):
                severity = result_item.get("severity", "UNKNOWN")
                service = result_item.get("service", "unknown")
                message = result_item.get("message", "")
                timestamp = result_item.get("timestamp", "unknown")
                similarity = result_item.get("similarity_score", 0)
                
                # Truncate long messages for table display
                display_message = message[:100] + "..." if len(message) > 100 else message
                
                table_data.append({
                    "#": i + 1,
                    "Severity": f"{get_severity_color(severity)} {severity}",
                    "Service": service,
                    "Message": display_message,
                    "Timestamp": timestamp,
                    "Similarity": format_similarity_score(similarity)
                })
            
            # Display table
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )
            
            # Detailed results with expandable raw logs
            st.markdown("### 📝 Detailed Results")
            
            for i, result_item in enumerate(results):
                severity = result_item.get("severity", "UNKNOWN")
                service = result_item.get("service", "unknown")
                message = result_item.get("message", "")
                timestamp = result_item.get("timestamp", "unknown")
                raw_log = result_item.get("raw_log", "")
                similarity = result_item.get("similarity_score", 0)
                
                # Create expandable section for each result
                with st.expander(f"{i+1}. {get_severity_color(severity)} {severity} - {service} ({format_similarity_score(similarity)})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Message:** {message}")
                        st.markdown(f"**Service:** {service}")
                        st.markdown(f"**Timestamp:** {timestamp}")
                    
                    with col2:
                        st.metric("Similarity Score", format_similarity_score(similarity))
                    
                    if raw_log and raw_log != message:
                        st.markdown("**Raw Log Entry:**")
                        st.code(raw_log, language="text")
            
            # RAG Analysis section
            if rag_analysis:
                st.markdown("---")
                st.subheader("🧠 AI Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 🔍 Root Cause")
                    root_cause = rag_analysis.get("root_cause", "No analysis available")
                    st.markdown(root_cause)
                
                with col2:
                    st.markdown("#### 🛠️ Fix Suggestions")
                    fix_suggestions = rag_analysis.get("fix_suggestions", "No suggestions available")
                    st.markdown(fix_suggestions)
                
                with col3:
                    st.markdown("#### 🛡️ Prevention")
                    prevention = rag_analysis.get("prevention", "No prevention tips available")
                    st.markdown(prevention)
                
                # Button to go to detailed RAG analysis
                if st.button("🧠 View Detailed Analysis", use_container_width=True):
                    # Store query in session state for Root Cause page
                    st.session_state.rag_query = query
                    st.session_state.rag_results = results
                    st.session_state.rag_analysis = rag_analysis
                    st.switch_page("pages/4_🧠_Root_Cause.py")
            
            elif rag_enabled:
                st.info("🤖 AI analysis was requested but not available. Check if the Groq API is configured.")
        
        else:
            st.info("🔍 No results found for your query. Try different keywords or check if logs have been ingested.")
            
            # Suggestions for no results
            with st.expander("💡 Search Tips"):
                st.markdown("""
                **Try these search strategies:**
                - Use broader terms (e.g., "error" instead of specific error codes)
                - Search by service names (e.g., "auth-service", "payment-service")
                - Use common error patterns (e.g., "timeout", "connection", "failed")
                - Check severity levels (e.g., "critical errors", "warnings")
                
                **Example queries:**
                - "authentication failures"
                - "database connection errors"
                - "payment processing issues"
                - "API timeout errors"
                """)
    
    else:
        st.error(f"❌ Search failed: {result['error']}")
        
        # Troubleshooting for search errors
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            - **No logs ingested**: Upload log files first in the Ingest page
            - **Backend unavailable**: Check if the API server is running
            - **Query too complex**: Try simpler, more direct queries
            - **Timeout**: Try reducing the number of results or simplifying the query
            """)

# Example queries section
if not st.session_state.search_results:
    st.markdown("---")
    st.subheader("💡 Example Queries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Error Types:**
        - "authentication failures"
        - "database connection errors"
        - "payment processing issues"
        - "API timeout errors"
        """)
        
        if st.button("Try: authentication failures"):
            st.session_state.last_query = "authentication failures"
            st.rerun()
    
    with col2:
        st.markdown("""
        **Service-Specific:**
        - "auth-service errors"
        - "payment-service warnings"
        - "api-gateway issues"
        - "database service problems"
        """)
        
        if st.button("Try: payment-service errors"):
            st.session_state.last_query = "payment-service errors"
            st.rerun()

# Sidebar with system info
with st.sidebar:
    st.subheader("🏥 System Status")
    
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code in [200, 503]:
            health_data = response.json()
            
            status = health_data.get("status", "unknown")
            if status == "healthy":
                st.success("🟢 System Healthy")
            else:
                st.warning("🟡 System Issues")
            
            endee_connected = health_data.get("endee_connected", False)
            model_loaded = health_data.get("model_loaded", False)
            
            st.write(f"**Vector DB**: {'✅' if endee_connected else '❌'}")
            st.write(f"**AI Model**: {'✅' if model_loaded else '❌'}")
        
        else:
            st.error("❌ API Unreachable")
    
    except:
        st.error("❌ Connection Failed")
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📊 Collection Stats")
    try:
        response = requests.get(f"{api_url}/stats", timeout=5)
        if response.status_code == 200:
            stats_data = response.json()
            vector_count = stats_data.get("vector_count", 0)
            st.metric("Total Logs", f"{vector_count:,}")
            
            if vector_count == 0:
                st.warning("No logs available. Upload files first!")
        else:
            st.write("Stats unavailable")
    except:
        st.write("Stats unavailable")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("📤 Upload Logs", use_container_width=True):
        st.switch_page("pages/2_📤_Ingest.py")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/1_📊_Dashboard.py")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    ErrorLens Search - Intelligent semantic search for error logs
    </div>
    """,
    unsafe_allow_html=True
)