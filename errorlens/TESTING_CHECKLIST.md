# ErrorLens Manual Testing Checklist

## Phase 9: Final Testing and Deployment Preparation

This document provides a comprehensive manual testing checklist for ErrorLens to ensure all features work correctly before deployment.

---

## ✅ Pre-Testing Setup

- [ ] Endee vector database running on http://localhost:8080
- [ ] Backend API running on http://localhost:8000
- [ ] Frontend UI running on http://localhost:8501
- [ ] Demo data files available in `data/sample_logs/`
- [ ] Groq API key configured in `.env`

**Quick Start Commands:**
```bash
# 1. Start Endee
docker compose up endee -d

# 2. Start Backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 3. Start Frontend
streamlit run frontend/streamlit_app.py --server.port 8501
```

---

## 🧪 Test Suite 1: File Upload & Ingestion

### Test 1.1: Upload .log file
- [ ] Navigate to http://localhost:8501 → Ingest page
- [ ] Upload `data/sample_logs/auth_service.log`
- [ ] **Expected**: File uploads successfully
- [ ] **Expected**: Processing statistics displayed (167 logs processed)
- [ ] **Expected**: Success message shown
- [ ] **Expected**: Processing time < 30 seconds

### Test 1.2: Upload .txt file
- [ ] Upload `data/sample_logs/payment_service.log` (rename to .txt if needed)
- [ ] **Expected**: File uploads successfully
- [ ] **Expected**: 167 logs processed

### Test 1.3: Upload .json file
- [ ] Upload `data/sample_logs/test_api_gateway.json`
- [ ] **Expected**: JSON format parsed correctly
- [ ] **Expected**: Logs ingested successfully

### Test 1.4: Invalid file handling
- [ ] Try uploading a non-log file (e.g., image, PDF)
- [ ] **Expected**: Error message about unsupported file type
- [ ] **Expected**: No system crash

### Test 1.5: Large file handling
- [ ] Try uploading a file > 50MB (if available)
- [ ] **Expected**: Error message about file size limit
- [ ] **Expected**: Clear error message displayed

### Test 1.6: Empty file handling
- [ ] Create and upload an empty .log file
- [ ] **Expected**: Error message about no valid log entries
- [ ] **Expected**: Graceful error handling

---

## 🔍 Test Suite 2: Semantic Search

### Test 2.1: Basic search - Authentication errors
- [ ] Navigate to Search page
- [ ] Enter query: "authentication failed"
- [ ] Set top_k: 10
- [ ] RAG: Disabled
- [ ] Click Search
- [ ] **Expected**: Results displayed with similarity scores
- [ ] **Expected**: Results sorted by similarity (highest first)
- [ ] **Expected**: Search time < 2 seconds

### Test 2.2: Natural language search
- [ ] Query: "users cannot login to the system"
- [ ] **Expected**: Relevant authentication errors returned
- [ ] **Expected**: Similarity scores > 0.3

### Test 2.3: Payment processing search
- [ ] Query: "payment processing errors"
- [ ] **Expected**: Payment service errors returned
- [ ] **Expected**: Results include card declines, transaction failures

### Test 2.4: Database connection search
- [ ] Query: "database connection issues"
- [ ] **Expected**: Database-related errors returned
- [ ] **Expected**: Timeout and connection errors shown

### Test 2.5: API gateway search
- [ ] Query: "API timeout and rate limit"
- [ ] **Expected**: API gateway errors returned
- [ ] **Expected**: Rate limit and timeout messages shown

### Test 2.6: Top-K parameter validation
- [ ] Set top_k: 1
- [ ] **Expected**: Only 1 result returned
- [ ] Set top_k: 50
- [ ] **Expected**: Up to 50 results returned
- [ ] Set top_k: 100
- [ ] **Expected**: Up to 100 results returned

### Test 2.7: Empty query handling
- [ ] Leave query empty and click Search
- [ ] **Expected**: Validation error message
- [ ] **Expected**: No system crash

### Test 2.8: Special characters in query
- [ ] Query: "error: [CRITICAL] @user #123"
- [ ] **Expected**: Search handles special characters gracefully
- [ ] **Expected**: Results returned or appropriate message

---

## 🧠 Test Suite 3: RAG Analysis

### Test 3.1: Basic RAG analysis
- [ ] Navigate to Root Cause page
- [ ] Enter: "users cannot authenticate"
- [ ] Click Analyze
- [ ] **Expected**: Root cause explanation provided
- [ ] **Expected**: Fix suggestions listed
- [ ] **Expected**: Prevention strategies shown
- [ ] **Expected**: Analysis time < 10 seconds

### Test 3.2: RAG with search results
- [ ] Navigate to Search page
- [ ] Query: "payment processing failed"
- [ ] Enable RAG toggle
- [ ] Click Search
- [ ] **Expected**: Search results + RAG analysis displayed
- [ ] **Expected**: Root cause section populated
- [ ] **Expected**: Fix suggestions relevant to payment errors

### Test 3.3: Complex error scenario
- [ ] Root Cause query: "database connection timeout causing authentication failures"
- [ ] **Expected**: Comprehensive analysis of cascading failures
- [ ] **Expected**: Multiple fix suggestions
- [ ] **Expected**: Prevention strategies for both issues

### Test 3.4: RAG without Groq API key
- [ ] Temporarily remove GROQ_API_KEY from .env
- [ ] Restart backend
- [ ] Try RAG analysis
- [ ] **Expected**: Error message about missing API key
- [ ] **Expected**: Graceful degradation (search still works)

---

## 📊 Test Suite 4: Dashboard & Statistics

### Test 4.1: Dashboard health check
- [ ] Navigate to Dashboard page
- [ ] **Expected**: System health displayed (Overall Status, Vector DB, AI Model)
- [ ] **Expected**: All components show green status
- [ ] **Expected**: Service status indicators accurate

### Test 4.2: Collection statistics
- [ ] Check Collection Statistics section
- [ ] **Expected**: Total log entries count displayed
- [ ] **Expected**: Collection name shown (error_logs)
- [ ] **Expected**: Vector dimension shown (384D)
- [ ] **Expected**: Similarity metric shown (Cosine)

### Test 4.3: Storage information
- [ ] Check Storage Information section
- [ ] **Expected**: Estimated vector storage size calculated
- [ ] **Expected**: Storage density metric shown
- [ ] **Expected**: Values are reasonable (not negative or extreme)

### Test 4.4: Quick actions
- [ ] Click "Refresh Data" button
- [ ] **Expected**: Dashboard reloads with updated data
- [ ] Click "Go to Ingest" button
- [ ] **Expected**: Navigates to Ingest page
- [ ] Click "Go to Search" button
- [ ] **Expected**: Navigates to Search page

---

## 🔧 Test Suite 5: Error Handling

### Test 5.1: Backend unavailable
- [ ] Stop backend server
- [ ] Try to access Dashboard
- [ ] **Expected**: Error message about backend unavailable
- [ ] **Expected**: Clear instructions to start backend

### Test 5.2: Endee unavailable
- [ ] Stop Endee container: `docker stop endee-server`
- [ ] Try to ingest logs
- [ ] **Expected**: Error message about vector database unavailable
- [ ] **Expected**: No system crash
- [ ] Restart Endee: `docker start endee-server`

### Test 5.3: Invalid API responses
- [ ] Try accessing /stats when Endee is starting
- [ ] **Expected**: Graceful error handling
- [ ] **Expected**: Retry or helpful error message

### Test 5.4: Network timeout
- [ ] Simulate slow network (if possible)
- [ ] Try large file upload
- [ ] **Expected**: Timeout handled gracefully
- [ ] **Expected**: Clear error message

---

## 🚀 Test Suite 6: Performance Benchmarks

### Test 6.1: Ingestion speed
- [ ] Upload auth_service.log (167 logs)
- [ ] Record processing time
- [ ] **Target**: > 100 logs/second
- [ ] **Expected**: Processing completes in < 5 seconds

### Test 6.2: Search latency
- [ ] Perform search with top_k=10
- [ ] Record search time
- [ ] **Target**: < 500ms for top-10 search
- [ ] **Expected**: Results appear quickly

### Test 6.3: Embedding generation
- [ ] Check backend logs for embedding time
- [ ] **Target**: < 100ms per single entry
- [ ] **Expected**: Batch processing efficient

### Test 6.4: RAG analysis time
- [ ] Perform RAG analysis
- [ ] Record total time
- [ ] **Target**: < 5 seconds end-to-end
- [ ] **Expected**: Analysis completes reasonably fast

### Test 6.5: Concurrent requests
- [ ] Open multiple browser tabs
- [ ] Perform searches simultaneously
- [ ] **Expected**: All requests handled correctly
- [ ] **Expected**: No crashes or errors

---

## 🔄 Test Suite 7: System Integration

### Test 7.1: Full workflow test
- [ ] Reset collection: `curl -X DELETE http://localhost:8000/reset`
- [ ] Upload all 3 demo files (auth, payment, api_gateway)
- [ ] Verify 500 total logs ingested
- [ ] Perform 5 different searches
- [ ] Run 2 RAG analyses
- [ ] Check dashboard statistics
- [ ] **Expected**: All operations complete successfully

### Test 7.2: Health endpoint
- [ ] Access http://localhost:8000/health
- [ ] **Expected**: JSON response with status
- [ ] **Expected**: endee_connected: true
- [ ] **Expected**: model_loaded: true

### Test 7.3: Stats endpoint
- [ ] Access http://localhost:8000/stats
- [ ] **Expected**: Collection statistics returned
- [ ] **Expected**: vector_count matches ingested logs

### Test 7.4: API documentation
- [ ] Access http://localhost:8000/docs
- [ ] **Expected**: Swagger UI loads
- [ ] **Expected**: All endpoints documented
- [ ] Try "Try it out" for /health endpoint
- [ ] **Expected**: Interactive API testing works

### Test 7.5: Reset functionality
- [ ] Note current vector count
- [ ] Access http://localhost:8000/reset (DELETE)
- [ ] Check stats again
- [ ] **Expected**: vector_count = 0
- [ ] **Expected**: Collection recreated successfully

---

## 🎨 Test Suite 8: UI/UX Validation

### Test 8.1: Responsive design
- [ ] Resize browser window
- [ ] **Expected**: UI adapts to different sizes
- [ ] **Expected**: No broken layouts

### Test 8.2: Navigation
- [ ] Test all sidebar navigation links
- [ ] **Expected**: All pages accessible
- [ ] **Expected**: Active page highlighted

### Test 8.3: Error messages
- [ ] Trigger various errors
- [ ] **Expected**: Error messages are clear and helpful
- [ ] **Expected**: Red color for errors, yellow for warnings

### Test 8.4: Success messages
- [ ] Complete successful operations
- [ ] **Expected**: Green success messages displayed
- [ ] **Expected**: Confirmation of actions

### Test 8.5: Loading indicators
- [ ] Perform long operations (file upload, RAG analysis)
- [ ] **Expected**: Loading spinners shown
- [ ] **Expected**: Progress indicators where applicable

---

## 🐛 Test Suite 9: Edge Cases

### Test 9.1: Duplicate detection
- [ ] Upload same file twice
- [ ] Search for specific error
- [ ] **Expected**: Similar logs grouped (similarity > 0.85)
- [ ] **Expected**: Duplicates identified

### Test 9.2: Mixed severity levels
- [ ] Search across all severity levels
- [ ] **Expected**: Results include ERROR, WARN, INFO, DEBUG
- [ ] **Expected**: Severity displayed correctly

### Test 9.3: Long log messages
- [ ] Search for logs with very long messages
- [ ] **Expected**: Messages displayed properly (truncated if needed)
- [ ] **Expected**: Expandable view for full message

### Test 9.4: Special characters in logs
- [ ] Search for logs with special characters
- [ ] **Expected**: Special characters handled correctly
- [ ] **Expected**: No encoding issues

### Test 9.5: Timestamp parsing
- [ ] Verify timestamps in search results
- [ ] **Expected**: Timestamps parsed correctly
- [ ] **Expected**: Chronological ordering available

---

## 📋 Final Verification Checklist

### System Readiness
- [ ] All 500 demo logs can be ingested successfully
- [ ] Semantic search returns relevant results
- [ ] RAG analysis provides meaningful insights
- [ ] Dashboard displays accurate statistics
- [ ] All error handling works correctly
- [ ] Performance meets target benchmarks
- [ ] API documentation is complete and accurate
- [ ] UI is responsive and user-friendly

### Documentation
- [ ] README.md is comprehensive and accurate
- [ ] API endpoints documented in /docs
- [ ] Setup instructions are clear
- [ ] Troubleshooting guide is helpful
- [ ] Architecture diagram is accurate

### Deployment Readiness
- [ ] Docker Compose configuration works
- [ ] Environment variables properly configured
- [ ] Health checks functioning
- [ ] Logging is appropriate
- [ ] Security best practices followed

---

## 🎯 Test Results Summary

**Date**: _________________

**Tester**: _________________

**Total Tests**: 95

**Passed**: _____

**Failed**: _____

**Skipped**: _____

**Critical Issues**: _____

**Minor Issues**: _____

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## ✅ Sign-Off

- [ ] All critical tests passed
- [ ] All major features working
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Ready for deployment

**Approved by**: _________________

**Date**: _________________

---

**ErrorLens Testing Checklist v1.0**
*Comprehensive manual testing for production readiness*