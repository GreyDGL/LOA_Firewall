#!/usr/bin/env python3
"""
Unit tests for the demo.py FirewallDemo class
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the project root to the path so we can import the demo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from examples.demos.demo import FirewallDemo


class TestFirewallDemo(unittest.TestCase):
    """Test cases for FirewallDemo class"""

    def setUp(self):
        """Set up test fixtures"""
        self.demo = FirewallDemo("http://test:5001")
        self.demo.session = Mock()

    def test_init(self):
        """Test FirewallDemo initialization"""
        demo = FirewallDemo()
        self.assertEqual(demo.base_url, "http://localhost:5001")
        self.assertEqual(demo.demo_keywords, [])
        self.assertEqual(demo.demo_patterns, [])

        demo_custom = FirewallDemo("http://custom:8080")
        self.assertEqual(demo_custom.base_url, "http://custom:8080")

    def test_print_header(self):
        """Test print_header method"""
        with patch("builtins.print") as mock_print:
            self.demo.print_header("Test Title")

            # Verify the print calls
            self.assertEqual(mock_print.call_count, 3)
            mock_print.assert_any_call("\n" + "=" * 60)
            mock_print.assert_any_call("🔥 Test Title")
            mock_print.assert_any_call("=" * 60)

    def test_print_step(self):
        """Test print_step method"""
        with patch("builtins.print") as mock_print:
            self.demo.print_step("Test Step")

            self.assertEqual(mock_print.call_count, 2)
            mock_print.assert_any_call("\n📋 Test Step")
            mock_print.assert_any_call("-" * 50)

    def test_print_response_success(self):
        """Test print_response with successful response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "message": "success"}

        with patch("builtins.print") as mock_print:
            self.demo.print_response(mock_response)

            mock_print.assert_any_call("Status: 200")
            # Should print formatted JSON
            printed_args = [call.args[0] for call in mock_print.call_args_list]
            self.assertTrue(any("Response:" in arg for arg in printed_args))

    def test_print_response_with_is_safe_field(self):
        """Test print_response with is_safe field (show_full=False)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "is_safe": False,
            "reason": "malicious content detected",
            "processing_time_ms": 150,
        }

        with patch("builtins.print") as mock_print:
            self.demo.print_response(mock_response, show_full=False)

            printed_args = [call.args[0] for call in mock_print.call_args_list]
            self.assertTrue(any("Is Safe: False" in arg for arg in printed_args))
            self.assertTrue(
                any("Reason: malicious content detected" in arg for arg in printed_args)
            )
            self.assertTrue(any("Processing Time: 150ms" in arg for arg in printed_args))

    def test_print_response_json_error(self):
        """Test print_response when JSON parsing fails"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "Internal Server Error"

        with patch("builtins.print") as mock_print:
            self.demo.print_response(mock_response)

            mock_print.assert_any_call("Status: 500")
            mock_print.assert_any_call("Response: Internal Server Error")

    def test_check_server_status_success(self):
        """Test successful server status check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}

        self.demo.session.get.return_value = mock_response

        with patch("builtins.print"):
            result = self.demo.check_server_status()

        self.assertTrue(result)
        self.demo.session.get.assert_called_once_with("http://test:5001/health", timeout=5)

    def test_check_server_status_failure(self):
        """Test failed server status check"""
        mock_response = Mock()
        mock_response.status_code = 500

        self.demo.session.get.return_value = mock_response

        with patch("builtins.print"):
            result = self.demo.check_server_status()

        self.assertFalse(result)

    def test_check_server_status_connection_error(self):
        """Test server status check with connection error"""
        import requests

        self.demo.session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with patch("builtins.print") as mock_print:
            result = self.demo.check_server_status()

        self.assertFalse(result)
        # Should print error message
        printed_args = [call.args[0] for call in mock_print.call_args_list]
        self.assertTrue(any("Cannot connect to server" in arg for arg in printed_args))

    def test_demo_health_check_success(self):
        """Test successful health check demo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "guards_available": 2,
            "keyword_filter_enabled": True,
        }

        self.demo.session.get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            self.demo.demo_health_check()

        # Verify correct endpoint was called
        self.demo.session.get.assert_called_once_with("http://test:5001/health")

        # Verify success message was printed
        printed_args = [call.args[0] for call in mock_print.call_args_list]
        self.assertTrue(any("Server is healthy!" in arg for arg in printed_args))

    def test_demo_get_keywords_success(self):
        """Test successful get keywords demo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "keywords": ["malicious", "exploit"],
            "regex_patterns": [r"\bpassword\b", r"\bapi_key\b"],
        }

        self.demo.session.get.return_value = mock_response

        with patch("builtins.print"):
            result = self.demo.demo_get_keywords()

        # Verify data was stored in demo instance
        self.assertEqual(self.demo.demo_keywords, ["malicious", "exploit"])
        self.assertEqual(self.demo.demo_patterns, [r"\bpassword\b", r"\bapi_key\b"])

        # Verify return value
        expected_data = {
            "keywords": ["malicious", "exploit"],
            "regex_patterns": [r"\bpassword\b", r"\bapi_key\b"],
        }
        self.assertEqual(result, expected_data)

    def test_demo_get_keywords_failure(self):
        """Test failed get keywords demo"""
        mock_response = Mock()
        mock_response.status_code = 500

        self.demo.session.get.return_value = mock_response

        with patch("builtins.print"):
            result = self.demo.demo_get_keywords()

        self.assertEqual(result, {})

    @patch("time.time")
    def test_demo_performance_testing(self, mock_time):
        """Test performance testing demo"""
        # Mock time.time() to return predictable values (need more values for all calls)
        # 4 test cases * 3 iterations * 2 calls per iteration = 24 calls
        time_values = []
        for i in range(50):  # Provide enough time values
            time_values.extend([i, i + 0.1])
        mock_time.side_effect = time_values

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"is_safe": True, "processing_time_ms": 50}

        self.demo.session.post.return_value = mock_response

        with patch("builtins.print"):
            self.demo.demo_performance_testing()

        # Verify multiple requests were made (3 requests per test case, 4 test cases)
        self.assertEqual(self.demo.session.post.call_count, 12)

    def test_demo_error_scenarios(self):
        """Test error scenarios demo"""
        # Mock different responses for different error scenarios
        responses = [
            Mock(status_code=400, json=lambda: {"error": "Invalid JSON"}),  # Invalid JSON
            Mock(status_code=400, json=lambda: {"error": "Missing text field"}),  # Missing field
            Mock(status_code=404),  # Invalid endpoint
        ]

        # Set up the session mock to return different responses
        self.demo.session.post.side_effect = responses[:2]
        self.demo.session.get.return_value = responses[2]

        with patch("builtins.print"):
            self.demo.demo_error_scenarios()

        # Verify all endpoints were called
        self.assertEqual(self.demo.session.post.call_count, 2)
        self.assertEqual(self.demo.session.get.call_count, 1)

    @patch.object(FirewallDemo, "check_server_status")
    @patch.object(FirewallDemo, "demo_health_check")
    @patch.object(FirewallDemo, "demo_content_checking")
    @patch.object(FirewallDemo, "demo_keyword_management")
    @patch.object(FirewallDemo, "demo_performance_testing")
    @patch.object(FirewallDemo, "demo_error_scenarios")
    def test_run_full_demo_success(
        self,
        mock_error_scenarios,
        mock_performance,
        mock_keyword_mgmt,
        mock_content_check,
        mock_health_check,
        mock_server_status,
    ):
        """Test successful full demo run"""
        mock_server_status.return_value = True

        with patch("builtins.print"):
            result = self.demo.run_full_demo()

        self.assertTrue(result)

        # Verify all demo methods were called
        mock_server_status.assert_called_once()
        mock_health_check.assert_called_once()
        mock_content_check.assert_called_once()
        mock_keyword_mgmt.assert_called_once()
        mock_performance.assert_called_once()
        mock_error_scenarios.assert_called_once()

    @patch.object(FirewallDemo, "check_server_status")
    def test_run_full_demo_server_unavailable(self, mock_server_status):
        """Test full demo when server is unavailable"""
        mock_server_status.return_value = False

        with patch("builtins.print"):
            result = self.demo.run_full_demo()

        self.assertFalse(result)
        mock_server_status.assert_called_once()

    @patch.object(FirewallDemo, "check_server_status")
    @patch.object(FirewallDemo, "demo_health_check")
    def test_run_full_demo_keyboard_interrupt(self, mock_health_check, mock_server_status):
        """Test full demo with keyboard interrupt"""
        mock_server_status.return_value = True
        mock_health_check.side_effect = KeyboardInterrupt()

        with patch("builtins.print"):
            result = self.demo.run_full_demo()

        self.assertFalse(result)

    @patch.object(FirewallDemo, "check_server_status")
    @patch.object(FirewallDemo, "demo_health_check")
    def test_run_full_demo_exception(self, mock_health_check, mock_server_status):
        """Test full demo with general exception"""
        mock_server_status.return_value = True
        mock_health_check.side_effect = Exception("Test error")

        with patch("builtins.print"):
            result = self.demo.run_full_demo()

        self.assertFalse(result)


class TestDemoContentChecking(unittest.TestCase):
    """Test cases for content checking functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.demo = FirewallDemo("http://test:5001")
        self.demo.session = Mock()

    def test_demo_content_checking_all_pass(self):
        """Test content checking when all tests pass as expected"""
        # Mock responses for different test cases
        responses = [
            # Safe content - should be safe
            Mock(status_code=200, json=lambda: {"is_safe": True, "processing_time_ms": 50}),
            # Keyword detection - should be unsafe
            Mock(
                status_code=200,
                json=lambda: {
                    "is_safe": False,
                    "processing_time_ms": 75,
                    "analysis": {"keyword_filter": {"status": "flagged", "matches_found": 2}},
                },
            ),
            # Regex pattern - should be unsafe
            Mock(status_code=200, json=lambda: {"is_safe": False, "processing_time_ms": 60}),
            # Credit card - should be unsafe
            Mock(status_code=200, json=lambda: {"is_safe": False, "processing_time_ms": 80}),
            # API key - should be unsafe
            Mock(status_code=200, json=lambda: {"is_safe": False, "processing_time_ms": 70}),
            # Complex malicious - should be unsafe
            Mock(status_code=200, json=lambda: {"is_safe": False, "processing_time_ms": 90}),
        ]

        self.demo.session.post.side_effect = responses

        with patch("builtins.print"):
            self.demo.demo_content_checking()

        # Verify all test cases were called
        self.assertEqual(self.demo.session.post.call_count, 6)

    def test_demo_content_checking_with_old_format_response(self):
        """Test content checking with old format API responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "is_safe": False,
            "overall_reason": "keyword match",
            "processing_times": {"total": 0.075},
            "keyword_filter_result": {"is_safe": False, "matches": ["hack", "exploit"]},
            "category_analysis": {
                "final_category": "malicious",
                "resolution_method": "keyword_filter",
            },
            "guard_results": [{"model": "LLM-Guard-1", "category": "unsafe"}],
        }

        self.demo.session.post.return_value = mock_response

        with patch("builtins.print"):
            self.demo.demo_content_checking()

        # Should handle old format without errors
        self.assertEqual(self.demo.session.post.call_count, 6)


class TestDemoKeywordManagement(unittest.TestCase):
    """Test cases for keyword management functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.demo = FirewallDemo("http://test:5001")
        self.demo.session = Mock()
        # Set up some initial demo data
        self.demo.demo_keywords = ["existing_keyword"]
        self.demo.demo_patterns = [r"\bexisting_pattern\b"]

    def test_demo_keyword_management_success(self):
        """Test successful keyword management demo"""
        # Mock responses for the keyword management sequence
        get_response = Mock()
        get_response.status_code = 200
        get_response.json.return_value = {
            "keywords": ["existing_keyword"],
            "regex_patterns": [r"\bexisting_pattern\b"],
        }

        put_response = Mock()
        put_response.status_code = 200
        put_response.json.return_value = {"message": "Keywords updated successfully"}

        check_responses = [
            Mock(
                status_code=200,
                json=lambda: {
                    "is_safe": False,
                    "analysis": {"keyword_filter": {"status": "flagged", "matches_found": 1}},
                },
            ),
            Mock(status_code=200, json=lambda: {"is_safe": False}),
            Mock(status_code=200, json=lambda: {"is_safe": True}),
        ]

        error_response = Mock()
        error_response.status_code = 400
        error_response.json.return_value = {"error": "Invalid regex pattern"}

        restore_response = Mock()
        restore_response.status_code = 200
        restore_response.json.return_value = {"message": "Keywords restored"}

        # Set up the session mock responses
        self.demo.session.get.side_effect = [get_response, get_response]  # For GET calls
        self.demo.session.post.side_effect = check_responses  # For POST calls
        self.demo.session.put.side_effect = [
            put_response,
            error_response,
            restore_response,
        ]  # For PUT calls

        with patch("builtins.print"):
            with patch.object(
                self.demo,
                "demo_get_keywords",
                side_effect=[get_response.json(), get_response.json()],
            ):
                self.demo.demo_keyword_management()

        # Verify PUT requests were made for update, error test, and restore
        self.assertEqual(self.demo.session.put.call_count, 3)


class TestDemoMain(unittest.TestCase):
    """Test cases for main function and command line argument parsing"""

    @patch("sys.argv", ["demo.py"])
    @patch.object(FirewallDemo, "run_full_demo")
    def test_main_default_url(self, mock_run_demo):
        """Test main function with default URL"""
        mock_run_demo.return_value = True

        with patch("builtins.print"):
            with patch("sys.exit") as mock_exit:
                from examples.demos.demo import main

                main()

        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["demo.py", "http://custom:8080"])
    @patch.object(FirewallDemo, "run_full_demo")
    def test_main_custom_url(self, mock_run_demo):
        """Test main function with custom URL"""
        mock_run_demo.return_value = True

        with patch("builtins.print"):
            with patch("sys.exit") as mock_exit:
                from examples.demos.demo import main

                main()

        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["demo.py"])
    @patch.object(FirewallDemo, "run_full_demo")
    def test_main_demo_failure(self, mock_run_demo):
        """Test main function when demo fails"""
        mock_run_demo.return_value = False

        with patch("builtins.print"):
            with patch("sys.exit") as mock_exit:
                from examples.demos.demo import main

                main()

        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
