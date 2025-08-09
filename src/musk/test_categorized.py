#!/usr/bin/env python3
"""
Test script for categorized PII masking
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.musk import PIIMasker


def test_categorized_masking():
    """Test the categorized PII masking system."""
    print("🏷️  Testing Categorized PII Masking System")
    print("=" * 60)
    
    masker = PIIMasker(model_name="llama3.2")
    
    test_cases = [
        "Call me at 555-123-4567 or email john@example.com",
        "My SSN is 123-45-6789 and credit card is 1234-5678-9012-3456",
        "Payment info: Phone (555) 987-6543, Email: sarah@company.org",
        "Account details: SSN 987-65-4321, Card 4567-8901-2345-6789",
        "Support contact: Call 1-800-555-0199 or email support@service.com"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Original: {text}")
        
        # Use regex-only masking to show categories clearly
        masked = masker.mask_text(text, use_ai=False)
        print(f"Masked:   {masked}")
        
        # Show the different categories
        categories_found = []
        if "**phone**" in masked:
            categories_found.append("📞 phone")
        if "**email**" in masked:
            categories_found.append("📧 email")
        if "**ssn**" in masked:
            categories_found.append("🆔 ssn")
        if "**credit_card**" in masked:
            categories_found.append("💳 credit_card")
        
        if categories_found:
            print(f"Categories: {', '.join(categories_found)}")
        else:
            print("Categories: None detected")
        
        print("-" * 40)


if __name__ == "__main__":
    test_categorized_masking()