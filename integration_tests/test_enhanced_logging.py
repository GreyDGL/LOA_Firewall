#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced firewall logging capabilities
"""

import sys
import os
import json
import time

# Add the project root to the path
sys.path.insert(0, '/Users/gelei/Research/LoAFirewall')

from src.core.firewall import LLMFirewall
from config.config import default_config

def test_enhanced_logging():
    """Test the enhanced logging functionality"""
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Setup basic logging to see the enhanced logs
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/firewall_test.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create dedicated firewall analysis logger
    firewall_handler = logging.FileHandler("logs/firewall_analysis_test.log")
    firewall_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    firewall_logger = logging.getLogger('firewall_analysis')
    firewall_logger.setLevel(logging.INFO)
    firewall_logger.addHandler(firewall_handler)
    firewall_logger.propagate = False
    
    print("=== Testing Enhanced Firewall Logging ===")
    
    # Initialize firewall with a minimal config for testing
    test_config = {
        "keyword_filter": {
            "enabled": True,
            "blacklist_file": None,
            "short_circuit": False
        },
        "guards": [],  # No LLM guards for this test to avoid model dependencies
        "categories": default_config["categories"]
    }
    
    firewall = LLMFirewall(test_config)
    
    # Test cases with different types of content
    test_cases = [
        {
            "text": "Hello, how are you today?",
            "description": "Safe content test",
            "metadata": {
                "client_ip": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "request_id": "test-001"
            }
        },
        {
            "text": "What is the weather like?",
            "description": "Another safe content test",
            "metadata": {
                "client_ip": "10.0.0.50",
                "user_agent": "curl/7.68.0",
                "request_id": "test-002"
            }
        },
        {
            "text": "Can you help me with my homework?",
            "description": "Educational request",
            "metadata": {
                "client_ip": "172.16.0.25",
                "user_agent": "PostmanRuntime/7.28.4",
                "request_id": "test-003"
            }
        }
    ]
    
    print(f"\nTesting {len(test_cases)} different requests...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"  Text: '{test_case['text'][:50]}{'...' if len(test_case['text']) > 50 else ''}'")
        print(f"  IP: {test_case['metadata']['client_ip']}")
        
        start_time = time.time()
        result = firewall.check_content(
            text=test_case['text'],
            request_metadata=test_case['metadata']
        )
        processing_time = time.time() - start_time
        
        print(f"  Result: {'SAFE' if result['is_safe'] else 'UNSAFE'}")
        print(f"  Processing time: {processing_time:.3f}s")
        if result.get('fallback_used'):
            print(f"  Fallback used: {result['fallback_used']}")
    
    print(f"\n=== Logging Test Complete ===")
    print(f"Check the following log files for detailed output:")
    print(f"  - logs/firewall_test.log (general application logs)")
    print(f"  - logs/firewall_analysis_test.log (detailed firewall analysis logs)")
    
    # Show sample log entries
    try:
        with open("logs/firewall_analysis_test.log", 'r') as f:
            log_content = f.read()
        print(f"\nSample firewall analysis log entries:")
        print("=" * 60)
        print(log_content)
        print("=" * 60)
    except Exception as e:
        print(f"Could not read log file: {e}")

if __name__ == "__main__":
    test_enhanced_logging()