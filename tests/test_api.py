#!/usr/bin/env python3
"""
Comprehensive API Test Suite for LLM Firewall and PII Masking APIs

This script tests all endpoints on port 5001:
- POST /check - Content safety analysis
- POST /mask-pii - PII masking 
- GET /health - Health check
- GET /stats - Usage statistics

Usage:
    # Test locally
    python tests/test_api.py
    
    # Test remote server
    python tests/test_api.py --host 192.168.1.100
    python tests/test_api.py --host example.com --port 5001
    
    # Run specific test categories
    python tests/test_api.py --test-category firewall
    python tests/test_api.py --test-category pii
    python tests/test_api.py --test-category health
"""

import argparse
import json
import requests
import time
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TestCategory(Enum):
    ALL = "all"
    FIREWALL = "firewall"
    PII = "pii"
    HEALTH = "health"
    STATS = "stats"

@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    response_data: Optional[Dict[Any, Any]] = None

class APITester:
    """Comprehensive API test suite"""
    
    def __init__(self, host: str = "localhost", port: int = 5001, timeout: int = 30):
        """
        Initialize the API tester
        
        Args:
            host: API server host (default: localhost)
            port: API server port (default: 5001) 
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.results: List[TestResult] = []
        
        print(f"🔧 API Test Suite")
        print(f"📡 Testing API at: {self.base_url}")
        print(f"⏱️  Request timeout: {timeout}s")
        print("=" * 60)

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"} if data else {}
        
        if method.upper() == "GET":
            return requests.get(url, timeout=self.timeout, headers=headers)
        elif method.upper() == "POST":
            return requests.post(url, json=data, timeout=self.timeout, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

    def _run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test and capture results"""
        print(f"  🧪 {test_name}...", end=" ")
        start_time = time.time()
        
        try:
            response_data = test_func()
            duration_ms = (time.time() - start_time) * 1000
            result = TestResult(
                name=test_name,
                passed=True,
                duration_ms=duration_ms,
                response_data=response_data
            )
            print(f"✅ PASS ({duration_ms:.1f}ms)")
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = TestResult(
                name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
            print(f"❌ FAIL ({duration_ms:.1f}ms) - {str(e)}")
        
        self.results.append(result)
        return result

    # Health Check Tests
    def test_health_endpoint(self):
        """Test the /health endpoint"""
        response = self._make_request("GET", "/health")
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "version", "services"]
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")
        
        # Validate services structure
        if "firewall" not in data["services"]:
            raise AssertionError("Missing firewall service in health response")
        
        if "pii_masking" not in data["services"]:
            raise AssertionError("Missing pii_masking service in health response")
        
        return data

    def test_stats_endpoint(self):
        """Test the /stats endpoint"""
        response = self._make_request("GET", "/stats")
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "firewall", "pii_masking"]
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")
        
        # Validate firewall stats
        firewall_stats = data["firewall"]
        firewall_fields = ["total_tokens_processed", "requests_processed"]
        for field in firewall_fields:
            if field not in firewall_stats:
                raise AssertionError(f"Missing firewall stat: {field}")
        
        # Validate PII stats
        pii_stats = data["pii_masking"]
        pii_fields = ["requests_processed", "total_pii_items_masked", "service_available"]
        for field in pii_fields:
            if field not in pii_stats:
                raise AssertionError(f"Missing PII stat: {field}")
        
        return data

    # Firewall Tests
    def test_firewall_safe_content(self):
        """Test firewall with safe content"""
        test_data = {"text": "Hello, how are you today?"}
        response = self._make_request("POST", "/check", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["request_id", "is_safe", "category", "confidence", "reason"]
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")
        
        # Should be safe
        if not data["is_safe"]:
            raise AssertionError(f"Safe content marked as unsafe: {data['reason']}")
        
        if data["category"] != "safe":
            raise AssertionError(f"Expected 'safe' category, got '{data['category']}'")
        
        return data

    def test_firewall_potentially_unsafe_content(self):
        """Test firewall with potentially unsafe content"""
        test_data = {"text": "How to hack into a computer system"}
        response = self._make_request("POST", "/check", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Should have proper structure regardless of safety
        required_fields = ["request_id", "is_safe", "category", "confidence", "reason"]
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")
        
        return data

    def test_firewall_missing_text(self):
        """Test firewall with missing text field"""
        test_data = {"not_text": "This should fail"}
        response = self._make_request("POST", "/check", test_data)
        
        if response.status_code != 400:
            raise AssertionError(f"Expected 400, got {response.status_code}")
        
        data = response.json()
        if "error" not in data:
            raise AssertionError("Missing error field in error response")
        
        return data

    def test_firewall_empty_text(self):
        """Test firewall with empty text"""
        test_data = {"text": ""}
        response = self._make_request("POST", "/check", test_data)
        
        if response.status_code != 400:
            raise AssertionError(f"Expected 400, got {response.status_code}")
        
        data = response.json()
        if "error" not in data:
            raise AssertionError("Missing error field in error response")
        
        return data

    # PII Masking Tests
    def test_pii_masking_with_pii(self):
        """Test PII masking with text containing PII"""
        test_data = {
            "text": "Contact me at john.doe@example.com or call 555-123-4567",
            "use_ai": True
        }
        response = self._make_request("POST", "/mask-pii", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["request_id", "pii_detected", "masked_text", "status", "confidence"]
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")
        
        # Should detect PII
        if not data["pii_detected"]:
            raise AssertionError("PII not detected in text containing obvious PII")
        
        # Masked text should be different from original
        if data["masked_text"] == test_data["text"]:
            raise AssertionError("Masked text is identical to original text")
        
        # Should contain masked placeholders
        masked_text = data["masked_text"].lower()
        if "**email**" not in masked_text and "**phone**" not in masked_text:
            raise AssertionError(f"Expected PII placeholders in masked text: {data['masked_text']}")
        
        return data

    def test_pii_masking_without_pii(self):
        """Test PII masking with text containing no PII"""
        test_data = {
            "text": "Hello, this is a simple message without any personal information.",
            "use_ai": True
        }
        response = self._make_request("POST", "/mask-pii", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Should not detect PII
        if data["pii_detected"]:
            raise AssertionError(f"False positive: PII detected in clean text: {data['masked_text']}")
        
        # Masked text should be same as original for clean text
        if data["masked_text"] != test_data["text"]:
            raise AssertionError("Clean text was modified when it shouldn't be")
        
        return data

    def test_pii_masking_multiple_types(self):
        """Test PII masking with multiple PII types"""
        test_data = {
            "text": "My SSN is 123-45-6789, credit card 4567-1234-8901-2345, email test@example.com",
            "use_ai": True
        }
        response = self._make_request("POST", "/mask-pii", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Should detect PII
        if not data["pii_detected"]:
            raise AssertionError("Multiple PII types not detected")
        
        # Check analysis for multiple detections
        if "analysis" in data and "total_pii_found" in data["analysis"]:
            if data["analysis"]["total_pii_found"] < 2:
                print(f"Warning: Expected multiple PII items, found {data['analysis']['total_pii_found']}")
        
        return data

    def test_pii_masking_missing_text(self):
        """Test PII masking with missing text field"""
        test_data = {"use_ai": True}  # Missing text field
        response = self._make_request("POST", "/mask-pii", test_data)
        
        if response.status_code != 400:
            raise AssertionError(f"Expected 400, got {response.status_code}")
        
        data = response.json()
        if "error" not in data:
            raise AssertionError("Missing error field in error response")
        
        return data

    def test_pii_masking_without_ai(self):
        """Test PII masking with AI disabled"""
        test_data = {
            "text": "Call me at (555) 123-4567 for more info",
            "use_ai": False
        }
        response = self._make_request("POST", "/mask-pii", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Expected 200, got {response.status_code}")
        
        data = response.json()
        
        # Should still work with regex-only detection
        required_fields = ["request_id", "pii_detected", "masked_text", "method_used"]
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")
        
        return data

    # Edge Case Tests
    def test_large_text_firewall(self):
        """Test firewall with large text input"""
        large_text = "This is a very long text. " * 1000  # ~25KB text
        test_data = {"text": large_text}
        response = self._make_request("POST", "/check", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Large text failed: {response.status_code}")
        
        data = response.json()
        if "request_id" not in data:
            raise AssertionError("Missing request_id in large text response")
        
        return data

    def test_large_text_pii(self):
        """Test PII masking with large text input"""
        large_text = "Contact info: test@example.com. " + "This is filler text. " * 500
        test_data = {"text": large_text, "use_ai": True}
        response = self._make_request("POST", "/mask-pii", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Large PII text failed: {response.status_code}")
        
        data = response.json()
        if "request_id" not in data:
            raise AssertionError("Missing request_id in large PII text response")
        
        return data

    def test_special_characters(self):
        """Test with special characters and unicode"""
        test_data = {"text": "Hello 世界! Contact: tëst@éxample.com 📧"}
        response = self._make_request("POST", "/check", test_data)
        
        if response.status_code != 200:
            raise AssertionError(f"Special characters failed firewall: {response.status_code}")
        
        # Also test PII masking with special chars
        pii_data = {"text": "Email with émojis: tëst@éxample.com 📧", "use_ai": True}
        pii_response = self._make_request("POST", "/mask-pii", pii_data)
        
        if pii_response.status_code != 200:
            raise AssertionError(f"Special characters failed PII: {pii_response.status_code}")
        
        return {"firewall": response.json(), "pii": pii_response.json()}

    # Server Connection Tests
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        try:
            response = self._make_request("GET", "/health")
            if response.status_code == 200:
                return {"status": "connected", "server_info": response.json()}
            else:
                raise AssertionError(f"Server responded with {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise AssertionError(f"Cannot connect to server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise AssertionError(f"Server timeout after {self.timeout}s")

    # Test Runners
    def run_health_tests(self):
        """Run all health-related tests"""
        print("🏥 Health & Status Tests")
        print("-" * 30)
        
        self._run_test("Server Connectivity", self.test_server_connectivity)
        self._run_test("Health Endpoint", self.test_health_endpoint)
        self._run_test("Stats Endpoint", self.test_stats_endpoint)
        
        print()

    def run_firewall_tests(self):
        """Run all firewall-related tests"""
        print("🛡️  Firewall Content Analysis Tests")
        print("-" * 40)
        
        self._run_test("Safe Content Detection", self.test_firewall_safe_content)
        self._run_test("Unsafe Content Detection", self.test_firewall_potentially_unsafe_content)
        self._run_test("Missing Text Error", self.test_firewall_missing_text)
        self._run_test("Empty Text Error", self.test_firewall_empty_text)
        self._run_test("Large Text Processing", self.test_large_text_firewall)
        
        print()

    def run_pii_tests(self):
        """Run all PII masking tests"""
        print("🔒 PII Masking Tests")
        print("-" * 25)
        
        self._run_test("PII Detection & Masking", self.test_pii_masking_with_pii)
        self._run_test("No PII (Clean Text)", self.test_pii_masking_without_pii)
        self._run_test("Multiple PII Types", self.test_pii_masking_multiple_types)
        self._run_test("PII Without AI", self.test_pii_masking_without_ai)
        self._run_test("Missing Text Error", self.test_pii_masking_missing_text)
        self._run_test("Large Text PII Processing", self.test_large_text_pii)
        
        print()

    def run_edge_case_tests(self):
        """Run edge case and robustness tests"""
        print("⚡ Edge Cases & Robustness Tests")
        print("-" * 35)
        
        self._run_test("Special Characters & Unicode", self.test_special_characters)
        
        print()

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Running Complete API Test Suite")
        print("=" * 60)
        print()
        
        self.run_health_tests()
        self.run_firewall_tests()
        self.run_pii_tests()
        self.run_edge_case_tests()

    def run_tests_by_category(self, category: TestCategory):
        """Run tests for specific category"""
        if category == TestCategory.ALL:
            self.run_all_tests()
        elif category == TestCategory.HEALTH:
            self.run_health_tests()
        elif category == TestCategory.FIREWALL:
            self.run_firewall_tests()
        elif category == TestCategory.PII:
            self.run_pii_tests()
        elif category == TestCategory.STATS:
            print("📊 Stats Tests")
            print("-" * 15)
            self._run_test("Stats Endpoint", self.test_stats_endpoint)
            print()

    def print_summary(self):
        """Print test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        total_time = sum(r.duration_ms for r in self.results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️  Total Time: {total_time:.1f}ms")
        print(f"📈 Average Time: {avg_time:.1f}ms/test")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 20)
            for result in self.results:
                if not result.passed:
                    print(f"  • {result.name}: {result.error}")
            print()
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100.0:
            print("🎉 All tests passed! API is working correctly.")
        elif success_rate >= 80.0:
            print("⚠️  Most tests passed, but some issues detected.")
        else:
            print("🚨 Multiple test failures detected. API may have issues.")
        
        return success_rate >= 80.0

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="LLM Firewall API Test Suite")
    
    parser.add_argument("--host", default="localhost", 
                       help="API server host (default: localhost)")
    parser.add_argument("--port", type=int, default=5001,
                       help="API server port (default: 5001)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    parser.add_argument("--test-category", 
                       choices=[cat.value for cat in TestCategory],
                       default=TestCategory.ALL.value,
                       help="Test category to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = APITester(host=args.host, port=args.port, timeout=args.timeout)
    
    try:
        # Run tests based on category
        category = TestCategory(args.test_category)
        tester.run_tests_by_category(category)
        
        # Print summary
        success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()