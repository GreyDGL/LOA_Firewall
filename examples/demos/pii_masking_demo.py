#!/usr/bin/env python3
"""
PII Masking Demo Script

This script demonstrates the PII masking functionality using local Ollama models.
It shows how to detect and mask various types of personally identifiable information.
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from musk import PIIMasker
from musk.utils import PIIDetector, PIIMaskingUtils


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demo_basic_masking():
    """Demonstrate basic PII masking functionality."""
    print("=" * 60)
    print("Basic PII Masking Demo")
    print("=" * 60)
    
    # Initialize the PII masker
    masker = PIIMasker(model_name="llama3.2")
    
    # Test texts with various PII
    test_texts = [
        "Hi, my name is John Smith and you can reach me at 555-123-4567.",
        "Please contact Jane Doe at jane.doe@email.com or call (555) 987-6543.",
        "My SSN is 123-45-6789 and my address is 123 Main Street, Anytown, CA 90210.",
        "Contact information: Dr. Michael Johnson, phone: +1-555-444-3333, email: m.johnson@hospital.org",
        "Employee ID: EMP001, SSN: 987-65-4321, Personal phone: 555.111.2222"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}:")
        print(f"Original: {text}")
        
        # Try AI-based masking first
        try:
            masked_ai = masker.mask_text(text, use_ai=True)
            print(f"AI Masked: {masked_ai}")
        except Exception as e:
            print(f"AI Masking failed: {e}")
            
        # Fallback to regex masking
        masked_regex = masker.mask_text(text, use_ai=False)
        print(f"Regex Masked: {masked_regex}")
        
        # Show PII statistics
        try:
            stats = masker.get_pii_statistics(text)
            if stats['total_entities'] > 0:
                print(f"PII Stats: {stats['total_entities']} entities detected")
                for entity_type, count in stats['entity_types'].items():
                    print(f"  - {entity_type}: {count}")
        except Exception as e:
            print(f"Statistics failed: {e}")


def demo_regex_detection():
    """Demonstrate regex-based PII detection."""
    print("\n" + "=" * 60)
    print("Regex-based PII Detection Demo")
    print("=" * 60)
    
    detector = PIIDetector()
    
    test_text = """
    John Smith works at ABC Corp. His contact information is:
    Phone: (555) 123-4567
    Email: john.smith@abc.com
    SSN: 123-45-6789
    Address: 456 Oak Street, Somewhere, NY 12345
    Credit Card: 4532 1234 5678 9012
    """
    
    print(f"Test text:\n{test_text}")
    print("\nDetected PII entities:")
    
    # Detect all PII
    entities = detector.detect_all_pii(test_text)
    
    for entity in entities:
        print(f"- {entity['type'].upper()}: '{entity['value']}' "
              f"(confidence: {entity['confidence']:.2f}) "
              f"at position {entity['start']}-{entity['end']}")
    
    # Demonstrate masking with detected entities
    masked_text = PIIMaskingUtils.mask_entities(test_text, entities)
    print(f"\nMasked text:\n{masked_text}")


def demo_batch_processing():
    """Demonstrate batch processing of multiple texts."""
    print("\n" + "=" * 60)
    print("Batch Processing Demo")
    print("=" * 60)
    
    masker = PIIMasker(model_name="llama3.2")
    
    batch_texts = [
        "Customer: Alice Johnson, Phone: 555-0001, Email: alice@example.com",
        "Employee: Bob Wilson, SSN: 111-22-3333, Address: 789 Pine St",
        "Contact: Carol Davis at (555) 444-5555 or carol.davis@company.org",
        "User registration: Name=David Brown, Phone=555.777.8888, ID=987654321"
    ]
    
    print("Processing batch of texts:")
    for i, text in enumerate(batch_texts, 1):
        print(f"{i}. {text}")
    
    print("\nProcessing with AI masking (if available)...")
    try:
        masked_batch = masker.process_batch(batch_texts, use_ai=True)
        for i, masked in enumerate(masked_batch, 1):
            print(f"{i}. {masked}")
    except Exception as e:
        print(f"Batch processing failed: {e}")
        
        print("\nFalling back to regex masking...")
        masked_batch = masker.process_batch(batch_texts, use_ai=False)
        for i, masked in enumerate(masked_batch, 1):
            print(f"{i}. {masked}")


def demo_validation():
    """Demonstrate PII validation utilities."""
    print("\n" + "=" * 60)
    print("PII Validation Demo")
    print("=" * 60)
    
    # Test phone number validation
    phone_tests = ["555-123-4567", "(555) 123-4567", "15551234567", "123", "555-CALL-NOW"]
    print("Phone number validation:")
    for phone in phone_tests:
        is_valid = PIIMaskingUtils.validate_phone_number(phone)
        print(f"  {phone}: {'Valid' if is_valid else 'Invalid'}")
    
    # Test SSN validation
    ssn_tests = ["123-45-6789", "000-00-0000", "666-12-3456", "900-12-3456", "123456789"]
    print("\nSSN validation:")
    for ssn in ssn_tests:
        is_valid = PIIMaskingUtils.validate_ssn(ssn)
        print(f"  {ssn}: {'Valid' if is_valid else 'Invalid'}")


def main():
    """Main demo function."""
    setup_logging()
    
    print("PII Masking System Demo")
    print("Using Ollama with llama3.2 model")
    print("Note: Make sure Ollama is running locally on port 11434")
    print()
    
    try:
        demo_basic_masking()
        demo_regex_detection()
        demo_batch_processing()
        demo_validation()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()