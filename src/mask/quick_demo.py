#!/usr/bin/env python3
"""
Quick PII Masking Demo - Focused demonstration of key capabilities
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.musk import PIIMasker


def print_demo_result(test_name: str, original: str, masked: str):
    """Print formatted demo result."""
    success = masked != original and "*******" in masked
    status = "✅" if success else "❌"
    print(f"\n{status} {test_name}")
    print(f"Original:  {original}")
    print(f"Masked:    {masked}")


def main():
    """Quick demo of key PII masking capabilities."""
    print("🔒 PII MASKING SYSTEM - QUICK DEMO")
    print("=" * 50)
    
    # Initialize masker
    masker = PIIMasker(model_name="llama3.2")
    print("✅ PIIMasker initialized with llama3.2")
    
    # Demo cases covering the most important scenarios
    demo_cases = [
        ("Basic Name & Phone", "Hi, I'm John Smith and my phone is 555-123-4567."),
        ("Conversational Query", "May I know if your phone number is 84030341?"),
        ("Email Address", "Please contact me at john.doe@example.com for details."),
        ("SSN", "My social security number is 123-45-6789."),
        ("Multiple PII", "John Doe, phone: (555) 123-4567, email: john@example.com"),
        ("No PII Text", "This is just regular text with no personal information."),
    ]
    
    print(f"\nDemonstrating {len(demo_cases)} key scenarios:")
    
    for demo_name, text in demo_cases:
        try:
            masked = masker.mask_text(text)
            print_demo_result(demo_name, text, masked)
        except Exception as e:
            print(f"\n❌ {demo_name} - ERROR: {e}")
    
    # Demo regex fallback
    print(f"\n{'='*50}")
    print("🔧 REGEX FALLBACK DEMO (AI disabled)")
    
    fallback_text = "Call 555-123-4567 or email contact@example.com"
    masked_regex = masker.mask_text(fallback_text, use_ai=False)
    print_demo_result("Regex Fallback", fallback_text, masked_regex)
    
    # Summary
    print(f"\n{'='*50}")
    print("✅ Quick demo completed!")
    print("💡 Key features demonstrated:")
    print("  • AI-powered PII masking with llama3.2")
    print("  • Conversational text handling") 
    print("  • Multiple PII types (names, phones, emails, SSN)")
    print("  • Regex fallback for reliability")
    print("  • Graceful error handling")


if __name__ == "__main__":
    main()