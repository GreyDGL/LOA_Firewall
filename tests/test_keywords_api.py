#!/usr/bin/env python3
"""
Test script for the keyword management API endpoints
"""

import requests
import json
import sys

# API base URL
BASE_URL = "http://localhost:5001"

def test_get_keywords():
    """Test GET /keywords endpoint"""
    print("Testing GET /keywords...")
    try:
        response = requests.get(f"{BASE_URL}/keywords")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_update_keywords():
    """Test PUT /keywords endpoint"""
    print("\nTesting PUT /keywords...")
    test_data = {
        "keywords": ["test_keyword", "malicious", "exploit"],
        "regex_patterns": [r"\bpassword\b", r"\bapi[_-]key\b"]
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/keywords",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_invalid_regex():
    """Test PUT /keywords with invalid regex"""
    print("\nTesting PUT /keywords with invalid regex...")
    test_data = {
        "keywords": ["test"],
        "regex_patterns": ["[invalid regex"]  # Missing closing bracket
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/keywords",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_firewall_with_new_keywords():
    """Test that the firewall uses the updated keywords"""
    print("\nTesting firewall with updated keywords...")
    test_text = "This contains test_keyword which should be blocked"
    
    try:
        response = requests.post(
            f"{BASE_URL}/check",
            json={"text": test_text},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Is safe: {result.get('is_safe')}")
        print(f"Keyword filter result: {json.dumps(result.get('keyword_filter_result'), indent=2)}")
        
        # Should be unsafe because of our test keyword
        return not result.get('is_safe', True)
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Keyword Management API")
    print("=" * 40)
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("API server is not running or not healthy")
            sys.exit(1)
    except:
        print("Cannot connect to API server. Make sure it's running on localhost:5001")
        sys.exit(1)
    
    tests = [
        ("Get current keywords", test_get_keywords),
        ("Update keywords", test_update_keywords),
        ("Get updated keywords", test_get_keywords),
        ("Test invalid regex", test_invalid_regex),
        ("Test firewall with new keywords", test_firewall_with_new_keywords)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        if test_func():
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
    
    print(f"\n\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")