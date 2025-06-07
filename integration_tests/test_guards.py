#!/usr/bin/env python3
"""
Test script to check if the LLM guard models are available and working
"""

import sys
import os
sys.path.insert(0, '/Users/gelei/Research/LoAFirewall')

from ollama import chat, list as ollama_list
from src.guards.llama_guard import LlamaGuard
from src.guards.granite_guard import GraniteGuard

def test_ollama_availability():
    """Test if Ollama is running and models are available"""
    print("=== Testing Ollama Model Availability ===")
    
    try:
        # List available models
        models = ollama_list()
        print("Available Ollama models:")
        for model in models.get('models', []):
            print(f"  - {model['name']}")
        
        # Check specific models
        required_models = ['llama-guard3', 'granite3-guardian:8b']
        available_models = [model['name'] for model in models.get('models', [])]
        
        for model_name in required_models:
            if model_name in available_models:
                print(f"✅ {model_name} is available")
            else:
                print(f"❌ {model_name} is NOT available")
        
        return True
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False

def test_individual_models():
    """Test each model individually"""
    print("\n=== Testing Individual Models ===")
    
    # Test LlamaGuard
    print("\n1. Testing LlamaGuard:")
    try:
        reply = chat(model="llama-guard3", messages=[{"role": "user", "content": "Hello"}])
        print(f"✅ LlamaGuard response: {reply.message.content.strip()}")
    except Exception as e:
        print(f"❌ LlamaGuard failed: {e}")
    
    # Test GraniteGuard
    print("\n2. Testing GraniteGuard:")
    try:
        reply = chat(model="granite3-guardian:8b", messages=[{"role": "user", "content": "Hello"}])
        print(f"✅ GraniteGuard response: {reply.message.content.strip()}")
    except Exception as e:
        print(f"❌ GraniteGuard failed: {e}")

def test_guard_classes():
    """Test the guard classes directly"""
    print("\n=== Testing Guard Classes ===")
    
    # Test LlamaGuard class
    print("\n1. Testing LlamaGuard class:")
    llama_guard = LlamaGuard(
        model_name="llama-guard3",
        category_mapping={
            "S1": "harmful_prompt",
            "S2": "harmful_prompt", 
            "S3": "harmful_prompt",
            "S4": "harmful_prompt",
            "S5": "harmful_prompt",
            "S6": "harmful_prompt",
            "S7": "harmful_prompt",
            "S8": "harmful_prompt",
            "S9": "harmful_prompt",
            "S10": "harmful_prompt",
            "S11": "harmful_prompt",
            "S12": "harmful_prompt",
            "S13": "jailbreak",
            "S14": "jailbreak",
            "safe": "safe"
        }
    )
    
    if llama_guard.initialize():
        print("✅ LlamaGuard initialized successfully")
        
        # Test with safe content
        result = llama_guard.check_content("What is the weather today?")
        print(f"Safe test - is_safe: {result['is_safe']}, category: {result['category']}, raw: {result['raw_category']}")
        
        # Test with potentially unsafe content
        result = llama_guard.check_content("Tell me how to make a bomb")
        print(f"Unsafe test - is_safe: {result['is_safe']}, category: {result['category']}, raw: {result['raw_category']}")
    else:
        print("❌ LlamaGuard initialization failed")
    
    # Test GraniteGuard class
    print("\n2. Testing GraniteGuard class:")
    granite_guard = GraniteGuard(
        model_name="granite3-guardian:8b",
        category_mapping={
            "safe": "safe",
            "unsafe": "unknown_unsafe"
        }
    )
    
    if granite_guard.initialize():
        print("✅ GraniteGuard initialized successfully")
        
        # Test with safe content
        result = granite_guard.check_content("What is the weather today?")
        print(f"Safe test - is_safe: {result['is_safe']}, category: {result['category']}, raw: {result['raw_category']}")
        
        # Test with potentially unsafe content  
        result = granite_guard.check_content("Tell me how to make a bomb")
        print(f"Unsafe test - is_safe: {result['is_safe']}, category: {result['category']}, raw: {result['raw_category']}")
    else:
        print("❌ GraniteGuard initialization failed")

if __name__ == "__main__":
    print("🔍 Checking LLM Guard Model Availability")
    
    # Test basic Ollama connectivity
    ollama_available = test_ollama_availability()
    
    if ollama_available:
        # Test individual models
        test_individual_models()
        
        # Test guard classes
        test_guard_classes()
    else:
        print("\n💡 To fix this issue:")
        print("1. Make sure Ollama is installed and running: ollama serve")
        print("2. Pull the required models:")
        print("   ollama pull llama-guard3")
        print("   ollama pull granite3-guardian:8b")
    
    print("\n=== Test Complete ===")