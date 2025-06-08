#!/usr/bin/env python3
"""
Test script to verify the token counter implementation
"""

import sys
import os
import time
import requests
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.firewall import LLMFirewall
from src.core.config_manager import ConfigManager


def test_direct_firewall():
    """Test the firewall directly (without API)"""
    print("🧪 Testing firewall token counter directly...")
    
    # Load config
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Create firewall instance
    firewall = LLMFirewall(config)
    
    # Test texts
    test_texts = [
        "Hello world!",  # ~3 tokens
        "This is a longer test message with more content.",  # ~11 tokens
        "The quick brown fox jumps over the lazy dog. This pangram contains many words.",  # ~17 tokens
    ]
    
    print(f"Initial token count: {firewall.get_token_count()}")
    
    for i, text in enumerate(test_texts):
        print(f"\nTest {i+1}: '{text}'")
        print(f"  Text length: {len(text)} characters")
        
        result = firewall.check_content(text)
        
        print(f"  Tokens processed: {result.get('tokens_processed', 0)}")
        print(f"  Total tokens: {result.get('total_tokens_processed', 0)}")
        print(f"  Is safe: {result.get('is_safe', 'unknown')}")
    
    print(f"\nFinal token count: {firewall.get_token_count()}")
    print("✅ Direct firewall test completed!")


def test_api_endpoint():
    """Test the firewall via API endpoint"""
    print("\n🌐 Testing firewall token counter via API...")
    
    base_url = "http://localhost:5001"
    
    # Check if API is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running. Please start the firewall API first.")
            return
    except requests.RequestException:
        print("❌ Cannot connect to API. Please start the firewall API first.")
        return
    
    # Get initial stats
    response = requests.get(f"{base_url}/stats")
    initial_stats = response.json()
    print(f"Initial total tokens: {initial_stats.get('total_tokens_processed', 0)}")
    
    # Test texts
    test_texts = [
        "Hello world!",
        "This is a test message for the API.",
        "The quick brown fox jumps over the lazy dog.",
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\nAPI Test {i+1}: '{text}'")
        
        payload = {"text": text}
        response = requests.post(f"{base_url}/check", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Tokens processed: {result.get('tokens_processed', 0)}")
            print(f"  Total tokens: {result.get('total_tokens_processed', 0)}")
            print(f"  Is safe: {result.get('is_safe', 'unknown')}")
        else:
            print(f"  ❌ Request failed: {response.status_code}")
    
    # Get final stats
    response = requests.get(f"{base_url}/stats")
    final_stats = response.json()
    print(f"\nFinal total tokens: {final_stats.get('total_tokens_processed', 0)}")
    print("✅ API test completed!")


def test_counter_persistence():
    """Test that the counter persists across firewall restarts"""
    print("\n💾 Testing token counter persistence...")
    
    # Load config
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Create first firewall instance
    firewall1 = LLMFirewall(config)
    initial_count = firewall1.get_token_count()
    print(f"First instance initial count: {initial_count}")
    
    # Process some text
    result1 = firewall1.check_content("This is a test message for persistence testing.")
    count_after_first = firewall1.get_token_count()
    print(f"Count after processing: {count_after_first}")
    
    # Create second firewall instance (simulating restart)
    firewall2 = LLMFirewall(config)
    loaded_count = firewall2.get_token_count()
    print(f"Second instance loaded count: {loaded_count}")
    
    if loaded_count == count_after_first:
        print("✅ Token counter persistence works correctly!")
    else:
        print("❌ Token counter persistence failed!")
        print(f"  Expected: {count_after_first}, Got: {loaded_count}")


def main():
    print("🚀 Starting token counter tests...\n")
    
    try:
        # Test direct firewall usage
        test_direct_firewall()
        
        # Test API endpoint (if running)
        test_api_endpoint()
        
        # Test persistence
        test_counter_persistence()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()