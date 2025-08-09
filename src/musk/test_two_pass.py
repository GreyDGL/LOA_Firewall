#!/usr/bin/env python3
"""
Test script for the new two-pass PII masking system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.musk import PIIMasker


def test_two_pass_system():
    """Test the two-pass PII masking system."""
    print("🔒 Testing Two-Pass PII Masking System")
    print("=" * 60)
    
    masker = PIIMasker(model_name="llama3.2")
    
    test_cases = [
        "My phone number is 555-123-4567 for account verification",
        "Email me at john@example.com with credit card 4567-1234-8901-2345",
        "Account info: SSN 123-45-6789, Phone (555) 987-6543",
        "Support at Microsoft Corporation: call 1-800-555-0199",
        "Payment details: Card 9876-5432-1098-7654, Email billing@company.org"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Original: {text}")
        
        # Get detailed masking results
        details = masker.mask_text_with_details(text, use_ai=True)
        
        print(f"Final:    {details['masked_text']}")
        print(f"Method:   {details['method_used']}")
        print(f"Regex masked: {details['regex_masked_count']} items")
        print(f"AI masked:    {details['ai_masked_count']} items")
        
        if details['ai_extracted_pii']:
            print(f"AI found:     {', '.join([f'\"{item}\"' for item in details['ai_extracted_pii']])}")
        
        print("-" * 40)


if __name__ == "__main__":
    test_two_pass_system()