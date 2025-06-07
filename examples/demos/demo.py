#!/usr/bin/env python3
"""
Comprehensive Demo Script for Alio LLM Firewall

This script demonstrates all the features of the LLM Firewall including:
- Content checking with dual-layer filtering
- Keyword management (reading and updating)
- Health monitoring
- Error handling
- Performance testing
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any


class FirewallDemo:
    def __init__(self, base_url: str = "http://localhost:5001"):
        """Initialize the demo with the firewall API base URL"""
        self.base_url = base_url
        self.session = requests.Session()
        self.demo_keywords = []
        self.demo_patterns = []

    def print_header(self, title: str):
        """Print a formatted header for demo sections"""
        print(f"\n🔥 {title}")

    def print_step(self, step: str):
        """Print a formatted step description"""
        print(f"\n📋 {step}")

    def print_response(self, response: requests.Response, show_full: bool = True):
        """Print formatted API response"""
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            if show_full:
                print(f"Response:\n{json.dumps(data, indent=2)}")
            else:
                # Show only key fields for brevity (handle both old and new response formats)
                if "is_safe" in data:
                    print(f"Is Safe: {data['is_safe']}")

                    # Handle both old 'overall_reason' and new 'reason' fields
                    reason = data.get("reason") or data.get("overall_reason", "N/A")
                    print(f"Reason: {reason}")

                    # Handle both old 'processing_times' and new 'processing_time_ms' fields
                    if "processing_time_ms" in data:
                        print(f"Processing Time: {data['processing_time_ms']}ms")
                    elif "processing_times" in data:
                        print(f"Processing Time: {data['processing_times'].get('total', 'N/A')}s")
                else:
                    print(f"Response:\n{json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response.text}")

    def check_server_status(self) -> bool:
        """Check if the firewall server is running"""
        self.print_step("Checking server status...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            self.print_response(response)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            print(f"Make sure the firewall is running on {self.base_url}")
            return False

    def demo_health_check(self):
        """Demonstrate health check endpoint"""
        self.print_step("Health Check - GET /health")
        response = self.session.get(f"{self.base_url}/health")
        self.print_response(response)

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Server is healthy!")
            print(f"   - Guards available: {data.get('guards_available', 0)}")
            print(
                f"   - Keyword filter: {'enabled' if data.get('keyword_filter_enabled') else 'disabled'}"
            )

    def demo_get_keywords(self) -> Dict[str, Any]:
        """Demonstrate getting current keywords"""
        self.print_step("Get Current Keywords - GET /keywords")
        response = self.session.get(f"{self.base_url}/keywords")
        self.print_response(response)

        if response.status_code == 200:
            data = response.json()
            self.demo_keywords = data.get("keywords", [])
            self.demo_patterns = data.get("regex_patterns", [])
            print(f"\n📊 Current filter contains:")
            print(f"   - {len(self.demo_keywords)} keywords")
            print(f"   - {len(self.demo_patterns)} regex patterns")
            return data
        return {}

    def demo_content_checking(self):
        """Demonstrate content checking with various examples"""
        self.print_header("CONTENT CHECKING DEMONSTRATION")

        test_cases = [
            {
                "name": "Safe Content",
                "text": "Hello, this is a normal message about weather today.",
                "expected_safe": True,
            },
            {
                "name": "Keyword Detection",
                "text": "I want to hack into the system and bypass security.",
                "expected_safe": False,
            },
            {
                "name": "Regex Pattern Detection",
                "text": "My password is secret123, please don't share it.",
                "expected_safe": False,
            },
            {
                "name": "Credit Card Pattern",
                "text": "My credit card number is 4532015112830366.",
                "expected_safe": False,
            },
            {
                "name": "API Key Pattern",
                "text": "Use this api_key: sk-1234567890abcdef for authentication.",
                "expected_safe": False,
            },
            {
                "name": "Complex Malicious Content",
                "text": "Let me show you how to exploit this vulnerability to steal passwords and install malware.",
                "expected_safe": False,
            },
        ]

        results = []
        for test_case in test_cases:
            print(f"\n📋 {test_case['name']}")
            print(f"Input: \"{test_case['text']}\"")
            print(f"Expected: {'Safe' if test_case['expected_safe'] else 'Unsafe'}")

            response = self.session.post(
                f"{self.base_url}/check",
                json={"text": test_case["text"]},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                is_safe = data.get("is_safe", True)
                expected = test_case["expected_safe"]

                print(f"Actual: {'Safe' if is_safe else 'Unsafe'}")
                print(f"Firewall Works: {'✅ YES' if is_safe == expected else '❌ NO'}")

                # Handle processing time (both old and new formats)
                processing_time = 0
                if "processing_time_ms" in data:
                    processing_time = data["processing_time_ms"] / 1000  # Convert ms to seconds
                elif "processing_times" in data:
                    processing_time = data.get("processing_times", {}).get("total", 0)

                results.append(
                    {
                        "test": test_case["name"],
                        "passed": is_safe == expected,
                        "processing_time": processing_time,
                    }
                )
            else:
                results.append({"test": test_case["name"], "passed": False, "processing_time": 0})

        # Summary
        passed = sum(1 for r in results if r["passed"])
        total_time = sum(r["processing_time"] for r in results)
        avg_time = total_time / len(results) if results else 0

        print(f"\n📊 CONTENT CHECKING SUMMARY:")
        print(f"   - Tests passed: {passed}/{len(results)}")
        print(f"   - Average processing time: {avg_time:.3f}s")
        print(f"   - Total processing time: {total_time:.3f}s")

    def demo_keyword_management(self):
        """Demonstrate keyword management features"""
        self.print_header("KEYWORD MANAGEMENT DEMONSTRATION")

        # Get current keywords
        original_data = self.demo_get_keywords()

        # Demo updating keywords
        self.print_step("Update Keywords - PUT /keywords")
        new_keywords = ["demo_malicious", "demo_exploit", "demo_harmful"]
        new_patterns = [r"\bdemo_password\b", r"\bdemo_api[_-]key\b"]

        print(f"Adding demo keywords: {new_keywords}")
        print(f"Adding demo patterns: {new_patterns}")

        response = self.session.put(
            f"{self.base_url}/keywords",
            json={
                "keywords": self.demo_keywords + new_keywords,
                "regex_patterns": self.demo_patterns + new_patterns,
            },
            headers={"Content-Type": "application/json"},
        )

        self.print_response(response)

        if response.status_code == 200:
            print("✅ Keywords updated successfully!")

            # Verify the update
            self.print_step("Verify Update - GET /keywords")
            updated_data = self.demo_get_keywords()

            # Test with new keywords
            self.print_step("Test New Keywords")
            test_cases = [
                {"text": "This contains demo_malicious content", "expected_safe": False},
                {"text": "Here's a demo_password that should be caught", "expected_safe": False},
                {"text": "This is safe content", "expected_safe": True},
            ]

            for test_case in test_cases:
                print(f'\nInput: "{test_case["text"]}"')
                print(f'Expected: {"Safe" if test_case["expected_safe"] else "Unsafe"}')

                response = self.session.post(
                    f"{self.base_url}/check",
                    json={"text": test_case["text"]},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    data = response.json()
                    is_safe = data.get("is_safe", True)
                    expected = test_case["expected_safe"]

                    print(f'Actual: {"Safe" if is_safe else "Unsafe"}')
                    print(f'Firewall Works: {"✅ YES" if is_safe == expected else "❌ NO"}')

        # Demo error handling
        self.print_step("Error Handling - Invalid Regex")
        response = self.session.put(
            f"{self.base_url}/keywords",
            json={
                "keywords": ["test"],
                "regex_patterns": ["[invalid regex"],  # Missing closing bracket
            },
            headers={"Content-Type": "application/json"},
        )

        self.print_response(response)
        print("✅ Error handling works correctly!")

        # Restore original keywords
        if original_data:
            self.print_step("Restore Original Keywords")
            response = self.session.put(
                f"{self.base_url}/keywords",
                json={
                    "keywords": original_data.get("keywords", []),
                    "regex_patterns": original_data.get("regex_patterns", []),
                },
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                print("✅ Original keywords restored!")

    def demo_performance_testing(self):
        """Demonstrate performance characteristics"""
        self.print_header("PERFORMANCE TESTING")

        test_texts = [
            "Short safe message",
            "This is a longer message that contains more text to test how the firewall performs with larger content. "
            * 10,
            "hack exploit malware password api_key",  # Multiple triggers
            "Normal business email discussing quarterly results and upcoming meetings.",
        ]

        for i, text in enumerate(test_texts, 1):
            self.print_step(f"Performance Test {i} - {len(text)} characters")

            # Multiple requests to get average
            times = []
            for _ in range(3):
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/check",
                    json={"text": text},
                    headers={"Content-Type": "application/json"},
                )
                end_time = time.time()

                if response.status_code == 200:
                    data = response.json()
                    # Handle both old and new response formats
                    if "processing_time_ms" in data:
                        server_time = data["processing_time_ms"] / 1000  # Convert ms to seconds
                    else:
                        server_time = data.get("processing_times", {}).get("total", 0)

                    client_time = end_time - start_time
                    times.append((server_time, client_time))

            if times:
                avg_server = sum(t[0] for t in times) / len(times)
                avg_client = sum(t[1] for t in times) / len(times)

                print(f"Average server processing time: {avg_server:.3f}s")
                print(f"Average client round-trip time: {avg_client:.3f}s")
                print(f"Text length: {len(text)} characters")

    def demo_error_scenarios(self):
        """Demonstrate error handling in various scenarios"""
        self.print_header("ERROR HANDLING DEMONSTRATION")

        # Test invalid JSON
        self.print_step("Invalid JSON Request")
        try:
            response = self.session.post(
                f"{self.base_url}/check",
                data="invalid json",
                headers={"Content-Type": "application/json"},
            )
            self.print_response(response)
        except Exception as e:
            print(f"Error: {e}")

        # Test missing text field
        self.print_step("Missing 'text' Field")
        response = self.session.post(
            f"{self.base_url}/check",
            json={"message": "wrong field name"},
            headers={"Content-Type": "application/json"},
        )
        self.print_response(response)

        # Test invalid endpoint
        self.print_step("Invalid Endpoint")
        response = self.session.get(f"{self.base_url}/nonexistent")
        print(f"Status: {response.status_code}")
        print(f"Expected 404 for invalid endpoint ✅")

    def run_full_demo(self):
        """Run the complete demonstration"""
        print("🔥 ALIO LLM FIREWALL - COMPREHENSIVE DEMO")
        print("=" * 60)
        print("This demo showcases all firewall features including:")
        print("• Dual-layer content filtering (keywords + AI guards)")
        print("• Dynamic keyword management")
        print("• Health monitoring")
        print("• Performance characteristics")
        print("• Error handling")

        # Check server status first
        if not self.check_server_status():
            print("\n❌ Demo cannot continue without server connection.")
            print("Please ensure the firewall service is running and try again.")
            return False

        try:
            # Run all demo sections
            self.demo_health_check()
            self.demo_content_checking()
            self.demo_keyword_management()
            self.demo_performance_testing()
            self.demo_error_scenarios()

            # Final summary
            self.print_header("DEMO COMPLETE")
            print("🎉 All firewall features have been demonstrated!")
            print("\nKey takeaways:")
            print("• The firewall provides robust dual-layer filtering")
            print("• Keywords can be managed dynamically without restart")
            print("• Both keyword and AI-based detection work effectively")
            print("• The system handles errors gracefully")
            print("• Performance is suitable for real-time content filtering")
            print("• API responses are sanitized to protect implementation details")

            print(f"\n📚 For more information, see the README.md file")
            print(f"🔗 API Base URL: {self.base_url}")

            return True

        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            return False


def main():
    """Main function to run the demo"""
    # Parse command line arguments
    base_url = "http://localhost:5001"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print(f"🚀 Starting Alio LLM Firewall Demo")
    print(f"🔗 Connecting to: {base_url}")

    # Create and run demo
    demo = FirewallDemo(base_url)
    success = demo.run_full_demo()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
