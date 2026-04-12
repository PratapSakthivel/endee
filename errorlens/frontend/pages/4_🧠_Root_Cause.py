"""
ErrorLens Root Cause Analysis Page

Provides detailed AI-powered root cause analysis and fix suggestions.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="Root Cause Analysis - ErrorLens",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Root Cause Analysis")
st.markdown("AI-powered intelligent analysis for error resolution")

# Get API URL from session state
api_url = st.session_state.get("api_url", "http://localhost:8000")

def perform_rag_analysis(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Perform RAG analysis request to backend API."""
    try:
        payload = {
            "query": query,
            "top_k": top_k,
            "rag_enabled": True
        }
        
        with st.spinner("Analyzing logs with AI..."):
            response = requests.post(
                f"{api_url}/search",
                json=payload,
                timeout=60  # Longer timeout for RAG analysis
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
        return {"success": False, "error": "Analysis timeout - query took too long"}
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
if "rag_query" not in st.session_state:
    st.session_state.rag_query = ""
if "rag_results" not in st.session_state:
    st.session_state.rag_results = []
if "rag_analysis" not in st.session_state:
    st.session_state.rag_analysis = None

# Query input section
st.subheader("🎯 Analysis Query")

col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "Describe the issue you want to analyze",
        placeholder="e.g., users cannot login, payment processing fails, database connection errors...",
        value=st.session_state.rag_query,
        help="Describe the problem in natural language for AI analysis"
    )

with col2:
    analyze_button = st.button("🧠 Analyze", type="primary", use_container_width=True)

# Perform analysis
if analyze_button and query.strip():
    st.session_state.rag_query = query
    result = perform_rag_analysis(query)
    
    if result["success"]:
        data = result["data"]
        st.session_state.rag_results = data.get("results", [])
        st.session_state.rag_analysis = data.get("rag_analysis")
    else:
        st.error(f"❌ Analysis failed: {result['error']}")
        st.session_state.rag_analysis = None

elif analyze_button and not query.strip():
    st.error("❌ Please enter a query for analysis")

# Display analysis results
if st.session_state.rag_analysis:
    analysis = st.session_state.rag_analysis
    results = st.session_state.rag_results
    
    st.markdown("---")
    
    # Analysis overview
    st.subheader("📊 Analysis Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Query Analyzed", f'"{st.session_state.rag_query}"')
    
    with col2:
        st.metric("Logs Analyzed", f"{len(results)}")
    
    with col3:
        if results:
            avg_similarity = sum(r.get("similarity_score", 0) for r in results) / len(results)
            st.metric("Avg Relevance", format_similarity_score(avg_similarity))
    
    # Main analysis sections
    st.markdown("---")
    
    # Root Cause Analysis
    st.subheader("🔍 Root Cause Analysis")
    root_cause = analysis.get("root_cause", "No root cause analysis available")
    
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff6b6b;">
                <h4 style="color: #ff6b6b; margin-top: 0;">🎯 Identified Root Cause</h4>
                <p style="margin-bottom: 0; font-size: 16px;">{root_cause}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("")
    
    # Fix Suggestions
    st.subheader("🛠️ Recommended Fixes")
    fix_suggestions = analysis.get("fix_suggestions", "No fix suggestions available")
    
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4ecdc4;">
                <h4 style="color: #4ecdc4; margin-top: 0;">🔧 Action Items</h4>
                <p style="margin-bottom: 0; font-size: 16px;">{fix_suggestions}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("")
    
    # Prevention Strategies
    st.subheader("🛡️ Prevention Strategies")
    prevention = analysis.get("prevention", "No prevention strategies available")
    
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #45b7d1;">
                <h4 style="color: #45b7d1; margin-top: 0;">🛡️ Future Prevention</h4>
                <p style="margin-bottom: 0; font-size: 16px;">{prevention}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Supporting Evidence
    if results:
        st.markdown("---")
        st.subheader("📋 Supporting Evidence")
        st.markdown("Log entries that contributed to this analysis:")
        
        # Create evidence table
        evidence_data = []
        for i, result_item in enumerate(results):
            severity = result_item.get("severity", "UNKNOWN")
            service = result_item.get("service", "unknown")
            message = result_item.get("message", "")
            timestamp = result_item.get("timestamp", "unknown")
            similarity = result_item.get("similarity_score", 0)
            
            # Truncate long messages
            display_message = message[:80] + "..." if len(message) > 80 else message
            
            evidence_data.append({
                "Rank": i + 1,
                "Severity": f"{get_severity_color(severity)} {severity}",
                "Service": service,
                "Message": display_message,
                "Relevance": format_similarity_score(similarity),
                "Timestamp": timestamp
            })
        
        st.dataframe(
            evidence_data,
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed evidence with expandable sections
        with st.expander("🔍 Detailed Evidence"):
            for i, result_item in enumerate(results):
                severity = result_item.get("severity", "UNKNOWN")
                service = result_item.get("service", "unknown")
                message = result_item.get("message", "")
                timestamp = result_item.get("timestamp", "unknown")
                raw_log = result_item.get("raw_log", "")
                similarity = result_item.get("similarity_score", 0)
                
                st.markdown(f"**Evidence #{i+1}** - {get_severity_color(severity)} {severity} ({format_similarity_score(similarity)} relevance)")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Service:** {service}")
                    st.markdown(f"**Message:** {message}")
                    st.markdown(f"**Timestamp:** {timestamp}")
                
                with col2:
                    st.metric("Relevance", format_similarity_score(similarity))
                
                if raw_log and raw_log != message:
                    st.code(raw_log, language="text")
                
                if i < len(results) - 1:
                    st.markdown("---")
    
    # Action buttons
    st.markdown("---")
    st.subheader("⚡ Next Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 New Search", use_container_width=True):
            st.switch_page("pages/3_🔍_Search.py")
    
    with col2:
        if st.button("📤 Upload More Logs", use_container_width=True):
            st.switch_page("pages/2_📤_Ingest.py")
    
    with col3:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/1_📊_Dashboard.py")

elif st.session_state.rag_query:
    # Show message if query was entered but no analysis available
    st.info("🤖 Enter a query above and click 'Analyze' to get AI-powered root cause analysis")

else:
    # Initial state - show examples and instructions
    st.markdown("---")
    st.subheader("💡 How Root Cause Analysis Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔍 Analysis Process
        
        1. **Query Processing**: Your natural language query is converted to semantic vectors
        2. **Log Retrieval**: Most relevant log entries are found using similarity search
        3. **AI Analysis**: Advanced language model analyzes patterns and context
        4. **Insights Generation**: Root cause, fixes, and prevention strategies are generated
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 Best Practices
        
        - **Be specific**: Describe symptoms clearly (e.g., "users can't login after password reset")
        - **Include context**: Mention timeframes, affected services, or user groups
        - **Use keywords**: Include relevant technical terms and error types
        - **Iterate**: Try different phrasings if initial results aren't helpful
        """)
    
    # Example queries
    st.markdown("---")
    st.subheader("📝 Example Analysis Queries")
    
    examples = [
        {
            "title": "Authentication Issues",
            "query": "users cannot login after password reset",
            "description": "Analyze login failures and authentication problems"
        },
        {
            "title": "Payment Processing",
            "query": "payment transactions are failing with timeout errors",
            "description": "Investigate payment service issues and timeouts"
        },
        {
            "title": "Database Problems",
            "query": "application is slow and database connections are timing out",
            "description": "Analyze database connectivity and performance issues"
        },
        {
            "title": "API Gateway Issues",
            "query": "API requests are returning 500 errors intermittently",
            "description": "Investigate API gateway failures and service errors"
        }
    ]
    
    for i, example in enumerate(examples):
        with st.expander(f"💡 {example['title']}"):
            st.markdown(f"**Query:** `{example['query']}`")
            st.markdown(f"**Purpose:** {example['description']}")
            
            if st.button(f"Try this query", key=f"example_{i}"):
                st.session_state.rag_query = example['query']
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
            
            # RAG availability check
            if status == "healthy":
                st.write("**RAG Analysis**: ✅ Available")
            else:
                st.write("**RAG Analysis**: ❌ Limited")
        
        else:
            st.error("❌ API Unreachable")
    
    except:
        st.error("❌ Connection Failed")
    
    st.markdown("---")
    
    # Analysis tips
    st.subheader("💡 Analysis Tips")
    st.markdown("""
    **For better results:**
    - Use descriptive queries
    - Include error symptoms
    - Mention affected services
    - Be specific about timing
    
    **AI Analysis requires:**
    - Groq API configuration
    - Ingested log data
    - Healthy system status
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    ErrorLens Root Cause Analysis - AI-powered intelligent error resolution
    </div>
    """,
    unsafe_allow_html=True
)