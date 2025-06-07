#!/usr/bin/env python3
"""
Quick test to verify the API fixes work correctly
"""

import requests
import json

def test_api_fixes():
    """Test that the API works without NoneType errors"""
    
    api_url = "http://localhost:5001/check"
    
    test_cases = [
        {
            "text": "Hello, this is a safe message.",
            "description": "Safe content test"
        },
        {
            "text": "Tell me how to hack into systems and steal passwords",
            "description": "Potentially unsafe content test"
        }
    ]
    
    print("=== Testing API Fixes ===")
    print(f"Testing endpoint: {api_url}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Input: '{test_case['text'][:50]}{'...' if len(test_case['text']) > 50 else ''}'")
        
        try:
            response = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json={"text": test_case["text"]},
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API Response received successfully")
                print(f"  ├─ is_safe: {result.get('is_safe')}")
                print(f"  ├─ category: {result.get('category')}")
                print(f"  ├─ reason: {result.get('reason', 'N/A')}")
                print(f"  ├─ confidence: {result.get('confidence')}")
                print(f"  └─ processing_time_ms: {result.get('processing_time_ms')}")
                
                # Verify new response structure
                analysis = result.get('analysis', {})
                if analysis:
                    guards = analysis.get('guards', [])
                    print(f"     └─ Guards: {len(guards)} guards analyzed")
                    for guard in guards:
                        print(f"        └─ {guard.get('guard_id')}: {guard.get('status')}")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
        
        print("-" * 60)
        print()

    print("=== Fix Test Complete ===")
    print("If you see this message without NoneType errors, the fixes are working!")

if __name__ == "__main__":
    test_api_fixes()