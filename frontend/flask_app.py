"""
ErrorLens Flask Frontend

Simple web interface for the ErrorLens system using Flask.
Provides the same functionality as Streamlit but without pandas/pyarrow dependencies.
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
MAX_FILE_SIZE_MB = 50
SUPPORTED_EXTENSIONS = {'.log', '.txt', '.json'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           '.' + filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in SUPPORTED_EXTENSIONS]

def get_system_health():
    """Get system health status from backend API."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code in [200, 503]:
            return response.json()
        else:
            return {"status": "error", "endee_connected": False, "model_loaded": False}
    except requests.exceptions.RequestException:
        return {"status": "error", "endee_connected": False, "model_loaded": False}

def get_system_stats():
    """Get system statistics from backend API."""
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except requests.exceptions.RequestException:
        return {}

@app.route('/')
def index():
    """Main dashboard page."""
    health = get_system_health()
    stats = get_system_stats()
    
    return render_template('index.html', 
                         health=health, 
                         stats=stats, 
                         api_url=API_URL)

@app.route('/ingest')
def ingest():
    """Log ingestion page."""
    health = get_system_health()
    stats = get_system_stats()
    
    return render_template('ingest.html', 
                         health=health, 
                         stats=stats,
                         max_size_mb=MAX_FILE_SIZE_MB,
                         supported_extensions=SUPPORTED_EXTENSIONS)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('ingest'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('ingest'))
    
    if not allowed_file(file.filename):
        flash(f'File type not supported. Allowed: {", ".join(SUPPORTED_EXTENSIONS)}', 'error')
        return redirect(url_for('ingest'))
    
    try:
        # Prepare file for upload
        files = {'file': (file.filename, file.read(), file.content_type)}
        
        # Upload to backend
        response = requests.post(f"{API_URL}/ingest", files=files, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            flash('File processed successfully!', 'success')
            return render_template('ingest_result.html', result=result)
        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("error", error_data.get("detail", str(error_data)))
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            
            flash(f'Upload failed: {error_detail}', 'error')
            return redirect(url_for('ingest'))
    
    except requests.exceptions.Timeout:
        flash('Upload timeout - file processing took too long', 'error')
        return redirect(url_for('ingest'))
    except requests.exceptions.RequestException as e:
        flash(f'Connection error: {str(e)}', 'error')
        return redirect(url_for('ingest'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('ingest'))

@app.route('/search')
def search():
    """Search page."""
    health = get_system_health()
    stats = get_system_stats()
    
    return render_template('search.html', 
                         health=health, 
                         stats=stats)

@app.route('/api/search', methods=['POST'])
def api_search():
    """Handle search API requests."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        rag_enabled = data.get('rag_enabled', True)
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Forward to backend API
        payload = {
            'query': query,
            'top_k': top_k,
            'rag_enabled': rag_enabled
        }
        
        response = requests.post(f"{API_URL}/search", json=payload, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("error", error_data.get("detail", str(error_data)))
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            
            return jsonify({'error': error_detail}), response.status_code
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Search timeout'}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/root_cause')
def root_cause():
    """Root cause analysis page."""
    health = get_system_health()
    stats = get_system_stats()
    
    # Get query from URL parameters if coming from search
    query = request.args.get('query', '')
    
    return render_template('root_cause.html', 
                         health=health, 
                         stats=stats,
                         initial_query=query)

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    health = get_system_health()
    return jsonify(health)

@app.route('/api/stats')
def api_stats():
    """Statistics endpoint."""
    stats = get_system_stats()
    return jsonify(stats)

@app.route('/api/reset', methods=['DELETE'])
def api_reset():
    """Reset collection endpoint."""
    try:
        response = requests.delete(f"{API_URL}/reset", timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("error", error_data.get("detail", str(error_data)))
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            
            return jsonify({'error': error_detail}), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

# Template filters
@app.template_filter('format_similarity')
def format_similarity(score):
    """Format similarity score as percentage."""
    return f"{score * 100:.1f}%"

@app.template_filter('get_severity_color')
def get_severity_color(severity):
    """Get color class for severity level."""
    colors = {
        "ERROR": "text-danger",
        "WARN": "text-warning", 
        "WARNING": "text-warning",
        "INFO": "text-info",
        "DEBUG": "text-secondary",
        "UNKNOWN": "text-muted"
    }
    return colors.get(severity.upper(), "text-muted")

@app.template_filter('get_severity_icon')
def get_severity_icon(severity):
    """Get icon for severity level."""
    icons = {
        "ERROR": "🔴",
        "WARN": "🟡", 
        "WARNING": "🟡",
        "INFO": "🔵",
        "DEBUG": "⚪",
        "UNKNOWN": "⚫"
    }
    return icons.get(severity.upper(), "⚫")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('frontend/templates', exist_ok=True)
    os.makedirs('frontend/static', exist_ok=True)
    
    app.run(host='0.0.0.0', port=8501, debug=True)