#!/usr/bin/env python3
"""
Integration tests for the keyword management API endpoints
These tests require a running firewall server on localhost:5001
"""

import pytest
import requests
import json

# API base URL
BASE_URL = "http://localhost:5001"


def is_server_running():
    """Check if the firewall server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


# Skip all tests in this module if server is not running
pytestmark = pytest.mark.skipif(
    not is_server_running(), reason="Firewall server not running on localhost:5001"
)


class TestKeywordManagementAPI:
    """Integration tests for keyword management API"""

    def test_get_keywords(self):
        """Test GET /keywords endpoint"""
        response = requests.get(f"{BASE_URL}/keywords")

        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert "regex_patterns" in data
        assert isinstance(data["keywords"], list)
        assert isinstance(data["regex_patterns"], list)

    def test_update_keywords(self):
        """Test PUT /keywords endpoint"""
        test_data = {
            "keywords": ["test_keyword", "malicious", "exploit"],
            "regex_patterns": [r"\bpassword\b", r"\bapi[_-]key\b"],
        }

        response = requests.put(
            f"{BASE_URL}/keywords", json=test_data, headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data.get("keywords_count") == 3
        assert data.get("regex_patterns_count") == 2

    def test_invalid_regex(self):
        """Test PUT /keywords with invalid regex"""
        test_data = {
            "keywords": ["test"],
            "regex_patterns": ["[invalid regex"],  # Missing closing bracket
        }

        response = requests.put(
            f"{BASE_URL}/keywords", json=test_data, headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Invalid regex pattern" in data["error"]

    def test_firewall_with_updated_keywords(self):
        """Test that the firewall uses the updated keywords"""
        # First update keywords with a test keyword
        test_data = {
            "keywords": ["test_keyword_unique", "malicious", "exploit"],
            "regex_patterns": [r"\bpassword\b", r"\bapi[_-]key\b"],
        }

        update_response = requests.put(
            f"{BASE_URL}/keywords", json=test_data, headers={"Content-Type": "application/json"}
        )
        assert update_response.status_code == 200

        # Now test that the firewall detects the new keyword
        test_text = "This contains test_keyword_unique which should be blocked"

        response = requests.post(
            f"{BASE_URL}/check",
            json={"text": test_text},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        result = response.json()

        # Should be flagged as unsafe because of our test keyword
        assert result.get("is_safe") is False

        # Check that keyword filter detected it
        analysis = result.get("analysis", {})
        if analysis:
            # New response format
            kw_filter = analysis.get("keyword_filter", {})
            if kw_filter:
                assert kw_filter.get("status") == "flagged"
        else:
            # Old response format fallback
            kw_result = result.get("keyword_filter_result", {})
            if kw_result:
                assert kw_result.get("is_safe") is False
