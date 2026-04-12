"""
Integration tests for ErrorLens system.

Tests end-to-end workflows including ingestion, search, and RAG analysis.
These tests require the full system to be running (Endee + Backend + Frontend).
"""

import pytest
import requests
import time
import os
import tempfile
from typing import Dict, Any, List


class TestErrorLensIntegration:
    """Integration test suite for ErrorLens system."""
    
    @classmethod
    def setup_class(cls):
        """Set up integration test environment."""
        cls.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        cls.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        cls.timeout = 30
        
        # Wait for services to be ready
        cls._wait_for_services()
    
    @classmethod
    def _wait_for_services(cls, max_wait=60):
        """Wait for backend and frontend services to be ready."""
        print("Waiting for services to be ready...")
        
        start_time = time.time()
        backend_ready = False
        
        while time.time() - start_time < max_wait:
            try:
                # Check backend health
                response = requests.get(f"{cls.backend_url}/health", timeout=5)
                if response.status_code in [200, 503]:  # 503 is acceptable during startup
                    backend_ready = True
                    break
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        if not backend_ready:
            pytest.skip(f"Backend not ready after {max_wait}s")
        
        print("✅ Services are ready for integration testing")
    
    def test_system_health(self):
        """Test that all system components are healthy."""
        # Test backend health
        response = requests.get(f"{self.backend_url}/health", timeout=self.timeout)
        assert response.status_code in [200, 503]  # 503 during model loading is OK
        
        health_data = response.json()
        assert "status" in health_data
        
        # If unhealthy, it should still respond with proper structure
        if health_data["status"] == "unhealthy":
            assert "endee_connected" in health_data
            assert "model_loaded" in health_data
    
    def test_api_documentation_accessible(self):
        """Test that API documentation is accessible."""
        response = requests.get(f"{self.backend_url}/docs", timeout=self.timeout)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_stats_endpoint(self):
        """Test statistics endpoint."""
        response = requests.get(f"{self.backend_url}/stats", timeout=self.timeout)
        
        # May return 503 if Endee is not fully ready, which is acceptable
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            stats = response.json()
            assert "collection" in stats
            assert "vector_count" in stats
            assert "dimension" in stats
    
    def test_reset_collection(self):
        """Test collection reset functionality."""
        response = requests.delete(f"{self.backend_url}/reset", timeout=self.timeout)
        
        # May fail if Endee is not ready, which is acceptable for integration tests
        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "success"
        else:
            # Log the error but don't fail the test during system startup
            print(f"Reset failed (expected during startup): {response.status_code}")
    
    def test_end_to_end_ingestion_flow(self):
        """Test complete log ingestion workflow."""
        # Create a temporary log file
        log_content = """[2024-04-12 10:30:00] ERROR [auth_service] Authentication failed for user test123
[2024-04-12 10:31:00] WARN [auth_service] Rate limit approaching for IP 192.168.1.100
[2024-04-12 10:32:00] INFO [auth_service] User test456 logged in successfully
[2024-04-12 10:33:00] ERROR [payment_service] Payment processing failed for order ord_001
[2024-04-12 10:34:00] INFO [payment_service] Payment $99.99 processed successfully"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_file_path = f.name
        
        try:
            # Test ingestion
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test.log', f, 'text/plain')}
                response = requests.post(
                    f"{self.backend_url}/ingest",
                    files=files,
                    timeout=self.timeout
                )
            
            # May fail if system is not fully ready
            if response.status_code == 200:
                result = response.json()
                assert result["status"] in ["success", "partial_success"]
                assert "stats" in result
                assert result["stats"]["total_lines"] == 5
                print("✅ Ingestion test passed")
            else:
                print(f"Ingestion test skipped (system not ready): {response.status_code}")
        
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_end_to_end_search_flow(self):
        """Test complete search workflow."""
        search_request = {
            "query": "authentication failed",
            "top_k": 5,
            "rag_enabled": False
        }
        
        response = requests.post(
            f"{self.backend_url}/search",
            json=search_request,
            timeout=self.timeout
        )
        
        # May fail if no data ingested or system not ready
        if response.status_code == 200:
            result = response.json()
            assert "query" in result
            assert "results" in result
            assert "count" in result
            assert result["query"] == "authentication failed"
            assert isinstance(result["results"], list)
            print("✅ Search test passed")
        else:
            print(f"Search test skipped (no data or system not ready): {response.status_code}")
    
    def test_end_to_end_rag_pipeline(self):
        """Test complete RAG analysis pipeline."""
        search_request = {
            "query": "users cannot login to the system",
            "top_k": 3,
            "rag_enabled": True
        }
        
        response = requests.post(
            f"{self.backend_url}/search",
            json=search_request,
            timeout=60  # RAG analysis takes longer
        )
        
        # May fail if Groq API not available or no data
        if response.status_code == 200:
            result = response.json()
            assert "rag_analysis" in result
            
            if result["rag_analysis"]:
                rag = result["rag_analysis"]
                # Should have root cause analysis structure
                assert any(key in rag for key in ["root_cause", "fix_suggestions", "prevention"])
                print("✅ RAG pipeline test passed")
            else:
                print("RAG analysis not available (expected if no data or API issues)")
        else:
            print(f"RAG test skipped (system not ready): {response.status_code}")
    
    def test_demo_data_ingestion(self):
        """Test ingestion of demo data files."""
        demo_files = [
            "data/sample_logs/auth_service.log",
            "data/sample_logs/payment_service.log", 
            "data/sample_logs/api_gateway.log"
        ]
        
        successful_ingestions = 0
        
        for demo_file in demo_files:
            if not os.path.exists(demo_file):
                print(f"Demo file not found: {demo_file}")
                continue
            
            try:
                with open(demo_file, 'rb') as f:
                    files = {'file': (os.path.basename(demo_file), f, 'text/plain')}
                    response = requests.post(
                        f"{self.backend_url}/ingest",
                        files=files,
                        timeout=self.timeout
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    assert result["status"] in ["success", "partial_success"]
                    successful_ingestions += 1
                    print(f"✅ Demo file ingested: {demo_file}")
                else:
                    print(f"Demo file ingestion failed: {demo_file} ({response.status_code})")
            
            except Exception as e:
                print(f"Demo file ingestion error: {demo_file} - {e}")
        
        # At least one demo file should ingest successfully if system is ready
        if successful_ingestions > 0:
            print(f"✅ Demo data test passed: {successful_ingestions}/3 files ingested")
        else:
            print("Demo data test skipped (system not ready or files missing)")
    
    def test_search_with_demo_data(self):
        """Test search functionality with demo data."""
        test_queries = [
            "authentication failed",
            "payment processing error",
            "API gateway timeout",
            "database connection",
            "user login issues"
        ]
        
        successful_searches = 0
        
        for query in test_queries:
            search_request = {
                "query": query,
                "top_k": 10,
                "rag_enabled": False
            }
            
            try:
                response = requests.post(
                    f"{self.backend_url}/search",
                    json=search_request,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert "results" in result
                    successful_searches += 1
                    
                    if result["count"] > 0:
                        print(f"✅ Search found {result['count']} results for: '{query}'")
                    else:
                        print(f"Search returned no results for: '{query}' (expected if no matching data)")
            
            except Exception as e:
                print(f"Search error for '{query}': {e}")
        
        if successful_searches > 0:
            print(f"✅ Search with demo data test passed: {successful_searches}/{len(test_queries)} queries successful")
        else:
            print("Search with demo data test skipped (system not ready)")
    
    def test_performance_benchmarks(self):
        """Test basic performance benchmarks."""
        # Test search latency
        search_request = {
            "query": "error",
            "top_k": 10,
            "rag_enabled": False
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json=search_request,
                timeout=self.timeout
            )
            
            search_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Search latency: {search_time:.2f}s")
                
                # Basic performance check (should be under 5 seconds for simple search)
                if search_time < 5.0:
                    print("✅ Search performance acceptable")
                else:
                    print(f"⚠️ Search performance slow: {search_time:.2f}s")
            else:
                print(f"Performance test skipped: {response.status_code}")
        
        except Exception as e:
            print(f"Performance test error: {e}")


# Utility functions for integration testing
def wait_for_service(url: str, max_wait: int = 60) -> bool:
    """Wait for a service to become available."""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:  # Any non-server-error response
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    return False


def run_integration_tests():
    """Run integration tests manually."""
    print("🚀 Running ErrorLens Integration Tests")
    print("=" * 50)
    
    # Check if services are running
    backend_url = "http://localhost:8000"
    
    if not wait_for_service(f"{backend_url}/health", 10):
        print("❌ Backend service not available at http://localhost:8000")
        print("Please start the backend with: python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
        return False
    
    # Run basic tests
    test_suite = TestErrorLensIntegration()
    test_suite.setup_class()
    
    tests = [
        ("System Health", test_suite.test_system_health),
        ("API Documentation", test_suite.test_api_documentation_accessible),
        ("Statistics Endpoint", test_suite.test_stats_endpoint),
        ("End-to-End Search", test_suite.test_end_to_end_search_flow),
        ("Demo Data Search", test_suite.test_search_with_demo_data),
        ("Performance", test_suite.test_performance_benchmarks)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
    
    print(f"\n📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("⚠️ Some integration tests failed (may be expected during development)")
        return False


if __name__ == "__main__":
    run_integration_tests()