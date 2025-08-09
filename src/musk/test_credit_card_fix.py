#!/usr/bin/env python3
"""
Test script to verify the credit card detection fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.musk import PIIMasker


def test_credit_card_fix():
    """Test the credit card regex fix."""
    print("🔧 Testing Credit Card Detection Fix")
    print("=" * 60)
    
    masker = PIIMasker(model_name="llama3.2")
    
    test_cases = [
        # The original problematic case
        {
            'text': 'May I know if your credit card number is 4022251134152518?',
            'expected_type': 'credit_card',
            'description': 'Original problematic case'
        },
        # Various credit card formats
        {
            'text': 'Credit card: 4022-2511-3415-2518',
            'expected_type': 'credit_card',
            'description': 'Hyphenated format'
        },
        {
            'text': 'Card: 4022 2511 3415 2518',
            'expected_type': 'credit_card',
            'description': 'Spaced format'
        },
        {
            'text': 'Amex: 378282246310005',
            'expected_type': 'credit_card',
            'description': '15-digit Amex'
        },
        {
            'text': 'Visa: 4111111111111111',
            'expected_type': 'credit_card',
            'description': '16-digit Visa'
        },
        # Phone numbers that should not conflict
        {
            'text': 'Phone: 555-123-4567',
            'expected_type': 'phone',
            'description': 'Standard phone'
        },
        {
            'text': 'Call: 5551234567',
            'expected_type': 'phone',
            'description': '10-digit phone'
        },
        {
            'text': 'Mobile: 123456789012',
            'expected_type': 'phone',
            'description': '12-digit phone'
        },
        # SSN
        {
            'text': 'SSN: 123-45-6789',
            'expected_type': 'ssn',
            'description': 'Standard SSN'
        },
        # Email
        {
            'text': 'Email: user@example.com',
            'expected_type': 'email',
            'description': 'Standard email'
        }
    ]
    
    all_passed = True
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['description']}")
        print(f"Original: {case['text']}")
        
        result = masker.mask_text(case['text'], use_ai=False)
        print(f"Masked:   {result}")
        
        expected_mask = f"**{case['expected_type']}**"
        if expected_mask in result:
            print(f"✅ PASS - Correctly detected as {case['expected_type']}")
        else:
            print(f"❌ FAIL - Expected {case['expected_type']}, but got: {result}")
            all_passed = False
        
        print("-" * 40)
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")


if __name__ == "__main__":
    test_credit_card_fix()