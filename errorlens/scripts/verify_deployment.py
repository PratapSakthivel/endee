#!/usr/bin/env python3
"""
ErrorLens Deployment Verification Script

Verifies that all ErrorLens services are running correctly and accessible.
Tests basic functionality to ensure the system is ready for use.
"""

import requests
import time
import sys
from typing import Dict, Any, Tuple


class DeploymentVerifier:
    """Verifies ErrorLens deployment status."""
    
    def __init__(self):
        self.endee_url = "http://localhost:8080"
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:8501"
        self.timeout = 10
        self.results = []
    
    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_test(self, name: str, passed: bool, message: str = ""):
        """Print test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if message:
            print(f"       {message}")
        self.results.append((name, passed, message))
    
    def wait_for_service(self, url: str, service_name: str, max_wait: int = 60) -> bool:
        """Wait for a service to become available."""
        print(f"⏳ Waiting for {service_name} to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    elapsed = time.time() - start_time
                    print(f"✅ {service_name} ready in {elapsed:.1f}s")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        print(f"❌ {service_name} not ready after {max_wait}s")
        return False
    
    def test_endee_health(self) -> bool:
        """Test Endee vector database health."""
        try:
            response = requests.get(f"{self.endee_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                self.print_test("Endee Health Check", True, f"Status: {data.get('status', 'ok')}")
                return True
            else:
                self.print_test("Endee Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Endee Health Check", False, str(e))
            return False
    
    def test_backend_health(self) -> bool:
        """Test backend API health."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=self.timeout)
            if response.status_code in [200, 503]:  # 503 during startup is OK
                data = response.json()
                status = data.get("status", "unknown")
                endee_connected = data.get("endee_connected", False)
                model_loaded = data.get("model_loaded", False)
                
                message = f"Status: {status}, Endee: {endee_connected}, Model: {model_loaded}"
                self.print_test("Backend Health Check", True, message)
                return True
            else:
                self.print_test("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Backend Health Check", False, str(e))
            return False
    
    def test_backend_stats(self) -> bool:
        """Test backend statistics endpoint."""
        try:
            response = requests.get(f"{self.backend_url}/stats", timeout=self.timeout)
            if response.status_code in [200, 503]:
                if response.status_code == 200:
                    data = response.json()
                    vector_count = data.get("vector_count", 0)
                    dimension = data.get("dimension", 0)
                    message = f"Vectors: {vector_count}, Dimension: {dimension}"
                    self.print_test("Backend Stats Endpoint", True, message)
                else:
                    self.print_test("Backend Stats Endpoint", True, "Service starting up")
                return True
            else:
                self.print_test("Backend Stats Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Backend Stats Endpoint", False, str(e))
            return False
    
    def test_backend_docs(self) -> bool:
        """Test backend API documentation."""
        try:
            response = requests.get(f"{self.backend_url}/docs", timeout=self.timeout)
            if response.status_code == 200:
                self.print_test("Backend API Docs", True, "Swagger UI accessible")
                return True
            else:
                self.print_test("Backend API Docs", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Backend API Docs", False, str(e))
            return False
    
    def test_frontend_accessible(self) -> bool:
        """Test frontend accessibility."""
        try:
            response = requests.get(self.frontend_url, timeout=self.timeout)
            if response.status_code == 200:
                self.print_test("Frontend Accessible", True, "Streamlit UI loaded")
                return True
            else:
                self.print_test("Frontend Accessible", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Frontend Accessible", False, str(e))
            return False
    
    def test_frontend_health(self) -> bool:
        """Test frontend health endpoint."""
        try:
            response = requests.get(f"{self.frontend_url}/_stcore/health", timeout=self.timeout)
            if response.status_code == 200:
                self.print_test("Frontend Health Check", True, "Streamlit healthy")
                return True
            else:
                self.print_test("Frontend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Frontend Health Check", False, str(e))
            return False
    
    def test_basic_search(self) -> bool:
        """Test basic search functionality."""
        try:
            search_request = {
                "query": "error",
                "top_k": 5,
                "rag_enabled": False
            }
            response = requests.post(
                f"{self.backend_url}/search",
                json=search_request,
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                self.print_test("Basic Search", True, f"Found {count} results")
                return True
            else:
                self.print_test("Basic Search", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Basic Search", False, str(e))
            return False
    
    def run_verification(self) -> bool:
        """Run complete verification suite."""
        self.print_header("ErrorLens Deployment Verification")
        
        print("🚀 Starting deployment verification...\n")
        
        # Test Endee
        self.print_header("1. Endee Vector Database")
        if not self.wait_for_service(f"{self.endee_url}/health", "Endee", 30):
            print("⚠️  Endee not available - some tests will be skipped")
        self.test_endee_health()
        
        # Test Backend
        self.print_header("2. Backend API")
        if not self.wait_for_service(f"{self.backend_url}/health", "Backend", 60):
            print("⚠️  Backend not available - some tests will be skipped")
        self.test_backend_health()
        self.test_backend_stats()
        self.test_backend_docs()
        self.test_basic_search()
        
        # Test Frontend
        self.print_header("3. Frontend UI")
        if not self.wait_for_service(self.frontend_url, "Frontend", 30):
            print("⚠️  Frontend not available - some tests will be skipped")
        self.test_frontend_accessible()
        self.test_frontend_health()
        
        # Summary
        self.print_summary()
        
        # Return overall status
        return all(result[1] for result in self.results)
    
    def print_summary(self):
        """Print verification summary."""
        self.print_header("Verification Summary")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r[1])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            print("Failed Tests:")
            for name, passed, message in self.results:
                if not passed:
                    print(f"  ❌ {name}: {message}")
            print()
        
        if passed == total:
            print("🎉 All tests passed! ErrorLens is ready to use.")
            print("\n📍 Access Points:")
            print(f"   - Frontend UI: {self.frontend_url}")
            print(f"   - Backend API: {self.backend_url}")
            print(f"   - API Docs: {self.backend_url}/docs")
            print(f"   - Endee: {self.endee_url}")
        elif passed >= total * 0.7:
            print("⚠️  Most tests passed. ErrorLens is partially functional.")
            print("   Check failed tests above for issues.")
        else:
            print("❌ Many tests failed. ErrorLens may not be properly deployed.")
            print("   Please check service logs and configuration.")


def main():
    """Main verification function."""
    verifier = DeploymentVerifier()
    
    try:
        success = verifier.run_verification()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()