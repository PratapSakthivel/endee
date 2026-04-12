"""
ErrorLens Ingest Page

Handles log file uploads and displays ingestion statistics.
"""

import streamlit as st
import requests
import time
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="Ingest - ErrorLens",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Log Ingestion")
st.markdown("Upload and process log files for semantic analysis")

# Get API URL from session state
api_url = st.session_state.get("api_url", "http://localhost:8000")

# File upload configuration
MAX_FILE_SIZE_MB = 50
SUPPORTED_EXTENSIONS = ['.log', '.txt', '.json']

def validate_file(uploaded_file) -> tuple[bool, str]:
    """Validate uploaded file."""
    if uploaded_file is None:
        return False, "No file selected"
    
    # Check file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if f'.{file_extension}' not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: .{file_extension}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File too large: {uploaded_file.size / (1024*1024):.1f}MB. Maximum: {MAX_FILE_SIZE_MB}MB"
    
    return True, "File is valid"

def upload_file(uploaded_file) -> Dict[str, Any]:
    """Upload file to backend API."""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
        with st.spinner(f"Uploading and processing {uploaded_file.name}..."):
            response = requests.post(
                f"{api_url}/ingest",
                files=files,
                timeout=300  # 5 minutes timeout for large files
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
        return {"success": False, "error": "Upload timeout - file processing took too long"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Main interface
st.subheader("📁 File Upload")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a log file",
    type=['log', 'txt', 'json'],
    help=f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)} | Maximum size: {MAX_FILE_SIZE_MB}MB"
)

# Display file information
if uploaded_file is not None:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Filename", uploaded_file.name)
    
    with col2:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.metric("File Size", f"{file_size_mb:.2f} MB")
    
    with col3:
        file_type = uploaded_file.type or "Unknown"
        st.metric("File Type", file_type)
    
    # Validate file
    is_valid, validation_message = validate_file(uploaded_file)
    
    if is_valid:
        st.success(f"✅ {validation_message}")
        
        # Upload button
        if st.button("🚀 Process File", type="primary", use_container_width=True):
            # Upload and process
            result = upload_file(uploaded_file)
            
            if result["success"]:
                st.success("🎉 File processed successfully!")
                
                # Display ingestion statistics
                data = result["data"]
                stats = data.get("stats", {})
                
                st.subheader("📊 Ingestion Results")
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_lines = stats.get("total_lines", 0)
                    st.metric("Total Lines", f"{total_lines:,}")
                
                with col2:
                    processed = stats.get("processed_successfully", 0)
                    st.metric("Processed", f"{processed:,}")
                
                with col3:
                    errors = stats.get("processing_errors", 0)
                    st.metric("Errors", f"{errors:,}")
                
                with col4:
                    processing_time = stats.get("processing_time_seconds", 0)
                    st.metric("Processing Time", f"{processing_time:.2f}s")
                
                # Additional metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    batches = stats.get("batches_processed", 0)
                    st.metric("Batches Processed", f"{batches:,}")
                
                with col2:
                    logs_per_sec = stats.get("logs_per_second", 0)
                    st.metric("Processing Speed", f"{logs_per_sec:.1f} logs/sec")
                
                with col3:
                    success_rate = (processed / total_lines * 100) if total_lines > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Status indicator
                status = data.get("status", "unknown")
                if status == "success":
                    st.success("🟢 All logs processed successfully")
                elif status == "partial_success":
                    st.warning(f"🟡 Partial success - {errors} logs had processing errors")
                else:
                    st.error(f"🔴 Processing failed with status: {status}")
                
                # Detailed statistics table
                if st.expander("📋 Detailed Statistics"):
                    st.json(stats)
                
                # Next steps
                st.markdown("---")
                st.subheader("🎯 Next Steps")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔍 Search Logs", use_container_width=True):
                        st.switch_page("pages/3_🔍_Search.py")
                
                with col2:
                    if st.button("📊 View Dashboard", use_container_width=True):
                        st.switch_page("pages/1_📊_Dashboard.py")
            
            else:
                st.error(f"❌ Upload failed: {result['error']}")
                
                # Troubleshooting tips
                with st.expander("🔧 Troubleshooting Tips"):
                    st.markdown("""
                    **Common Issues:**
                    - **File too large**: Split large files or compress them
                    - **Unsupported format**: Convert to .log, .txt, or .json
                    - **Connection error**: Check if backend API is running
                    - **Timeout**: Try with smaller files or check server resources
                    - **Invalid JSON**: Validate JSON format if using .json files
                    
                    **Backend API Status**: Check the Dashboard for system health
                    """)
    
    else:
        st.error(f"❌ {validation_message}")

else:
    # Instructions when no file is selected
    st.info("👆 Select a log file to begin processing")
    
    # Help section
    with st.expander("ℹ️ File Format Guidelines"):
        st.markdown("""
        ### Supported Log Formats
        
        **Standard Log Format (.log, .txt)**
        ```
        2024-01-15 10:30:45 ERROR [auth-service] Authentication failed for user john@example.com
        2024-01-15 10:31:02 WARN [payment-service] Payment timeout for transaction tx_12345
        ```
        
        **JSON Log Format (.json)**
        ```json
        {"timestamp": "2024-01-15T10:30:45Z", "level": "ERROR", "service": "auth-service", "message": "Authentication failed"}
        {"timestamp": "2024-01-15T10:31:02Z", "level": "WARN", "service": "payment-service", "message": "Payment timeout"}
        ```
        
        **Syslog Format**
        ```
        Jan 15 10:30:45 server auth-service[1234]: ERROR Authentication failed for user
        ```
        
        ### Processing Details
        - Files are processed in batches of 100 log entries
        - Each log entry is converted to a 384-dimensional embedding vector
        - Malformed lines are skipped with error reporting
        - Processing time depends on file size and system resources
        """)

# System status sidebar
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
    st.subheader("📊 Quick Stats")
    try:
        response = requests.get(f"{api_url}/stats", timeout=5)
        if response.status_code == 200:
            stats_data = response.json()
            vector_count = stats_data.get("vector_count", 0)
            st.metric("Total Logs", f"{vector_count:,}")
        else:
            st.write("Stats unavailable")
    except:
        st.write("Stats unavailable")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    ErrorLens Ingestion - Upload and process log files for intelligent analysis
    </div>
    """,
    unsafe_allow_html=True
)