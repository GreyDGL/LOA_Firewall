#!/usr/bin/env python3
"""
Comprehensive PII Masking Demo Script

This script demonstrates the robustness of the PII masking system with various test cases
including edge cases, different PII types, and error handling scenarios.
"""

import sys
import os
import logging
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.musk import PIIMasker


def setup_logging():
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def print_section_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_demo_result(demo_name: str, original: str, masked: str, success: bool = True):
    """Print formatted demo results."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} {demo_name}")
    print(f"Original:  {original}")
    print(f"Masked:    {masked}")
    if not success:
        print("❗ Expected masking but got original text back")


def demo_basic_pii_masking(masker: PIIMasker):
    """Demonstrate basic PII masking scenarios."""
    print_section_header("BASIC PII MASKING EXAMPLES")
    
    demo_cases = [
        ("Simple name and phone", "Hi, I'm John Smith and my phone is 555-123-4567."),
        ("Email address", "Contact me at john.doe@example.com for more info."),
        ("SSN", "My social security number is 123-45-6789."),
        ("Multiple PII types", "John Doe, SSN: 123-45-6789, Phone: (555) 123-4567, Email: john@example.com"),
        ("Address", "I live at 123 Main Street, Anytown, CA 90210."),
    ]
    
    for demo_name, text in demo_cases:
        try:
            masked = masker.mask_text(text)
            success = masked != text and "*******" in masked
            print_demo_result(demo_name, text, masked, success)
        except Exception as e:
            print_demo_result(demo_name, text, f"ERROR: {e}", False)


def demo_conversational_scenarios(masker: PIIMasker):
    """Demonstrate conversational and question-based scenarios."""
    print_section_header("CONVERSATIONAL SCENARIOS")
    
    demo_cases = [
        ("Question with phone", "May I know if your phone number is 84030341?"),
        ("Question with name", "Is your name Sarah Johnson by any chance?"),
        ("Indirect reference", "Could you call me back at 555-987-6543 later?"),
        ("Email question", "Did you send that to admin@company.org already?"),
        ("Multiple questions", "What's your email? Mine is contact@example.com. Call me at 555-0123."),
    ]
    
    for demo_name, text in demo_cases:
        try:
            masked = masker.mask_text(text)
            success = masked != text and "*******" in masked
            print_demo_result(demo_name, text, masked, success)
        except Exception as e:
            print_demo_result(demo_name, text, f"ERROR: {e}", False)


def demo_edge_cases(masker: PIIMasker):
    """Demonstrate edge cases and challenging scenarios."""
    print_section_header("EDGE CASES")
    
    demo_cases = [
        ("Empty string", ""),
        ("Only spaces", "   "),
        ("No PII", "This is just regular text with no personal information."),
        ("Phone without separators", "Call me at 5551234567 today."),
        ("International phone", "My number is +1-555-123-4567 or +44-20-1234-5678."),
        ("Partial SSN", "Last 4 digits: 6789"),
        ("Email in sentence", "Send reports to data-analysis@tech-company.co.uk please."),
        ("Mixed formats", "John Smith (john.smith@email.com) - Tel: 555.123.4567"),
    ]
    
    for demo_name, text in demo_cases:
        try:
            masked = masker.mask_text(text)
            # For empty/no-PII cases, success means no change
            if not text.strip() or demo_name == "No PII" or demo_name == "Partial SSN":
                success = masked == text
            else:
                success = "*******" in masked
            print_demo_result(demo_name, text, masked, success)
        except Exception as e:
            print_demo_result(demo_name, text, f"ERROR: {e}", False)


def demo_batch_processing(masker: PIIMasker):
    """Demonstrate batch processing capabilities."""
    print_section_header("BATCH PROCESSING")
    
    texts = [
        "Customer: Alice Johnson, Phone: 555-0001",
        "Employee: Bob Wilson, SSN: 111-22-3333", 
        "Contact: carol.davis@company.org",
        "User: David Brown, ID: 987654321",
        "No PII in this text at all"
    ]
    
    print("Processing batch of 5 texts...")
    start_time = time.time()
    
    try:
        masked_batch = masker.process_batch(texts, use_ai=True)
        end_time = time.time()
        
        print(f"✅ Batch processed in {end_time - start_time:.2f} seconds")
        for i, (original, masked) in enumerate(zip(texts, masked_batch), 1):
            has_pii = any(keyword in original.lower() for keyword in ['phone', 'ssn', '@', 'contact', 'customer', 'employee'])
            success = ("*******" in masked) if has_pii and "No PII" not in original else (masked == original)
            status = "✅" if success else "❌"
            print(f"{status} {i}. {original} → {masked}")
            
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")


def demo_pii_statistics(masker: PIIMasker):
    """Demonstrate PII detection statistics."""
    print_section_header("PII DETECTION STATISTICS")
    
    example_text = """
    John Smith works at ABC Corp. Contact information:
    Phone: (555) 123-4567
    Email: john.smith@abc.com  
    SSN: 123-45-6789
    Address: 456 Oak Street, Somewhere, NY 12345
    """
    
    try:
        stats = masker.get_pii_statistics(example_text)
        print(f"Text analyzed: {example_text.strip()}")
        print(f"✅ Total PII entities detected: {stats['total_entities']}")
        
        if stats['entity_types']:
            print("Entity breakdown:")
            for entity_type, count in stats['entity_types'].items():
                print(f"  - {entity_type}: {count}")
        else:
            print("❌ No entities detected by AI (falling back to regex)")
            
    except Exception as e:
        print(f"❌ Statistics generation failed: {e}")


def demo_regex_fallback(masker: PIIMasker):
    """Demonstrate regex fallback functionality."""
    print_section_header("REGEX FALLBACK EXAMPLES")
    
    demo_cases = [
        ("Phone masking", "Call 555-123-4567 or 5551234567"),
        ("Email masking", "Send to contact@example.com and admin@site.org"),
        ("SSN masking", "SSN: 123-45-6789 or 123456789"),
    ]
    
    print("Examples with AI disabled (regex only):")
    for demo_name, text in demo_cases:
        try:
            masked = masker.mask_text(text, use_ai=False)
            success = "*******" in masked
            print_demo_result(demo_name, text, masked, success)
        except Exception as e:
            print_demo_result(demo_name, text, f"ERROR: {e}", False)


def demo_performance(masker: PIIMasker):
    """Demonstrate performance with various text sizes."""
    print_section_header("PERFORMANCE EXAMPLES")
    
    # Small text
    small_text = "Contact John at 555-1234 or john@email.com"
    
    # Medium text  
    medium_text = """
    Dear Customer Service,
    
    My name is Sarah Johnson and I'm writing to report an issue with my account.
    You can reach me at (555) 987-6543 or sarah.johnson@email.com.
    My account details: SSN 123-45-6789, Customer ID: CX-789456.
    
    Please call me back at your earliest convenience.
    
    Best regards,
    Sarah
    """ * 3
    
    # Large text
    large_text = medium_text * 10
    
    demo_cases = [
        ("Small text", small_text),
        ("Medium text", medium_text),
        ("Large text", large_text),
    ]
    
    for demo_name, text in demo_cases:
        try:
            start_time = time.time()
            masked = masker.mask_text(text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            chars_processed = len(text) 
            success = "*******" in masked
            
            print(f"✅ {demo_name}: {chars_processed} chars in {processing_time:.3f}s "
                  f"({'MASKED' if success else 'NO MASKING'})")
                  
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")


def check_model_availability(masker: PIIMasker):
    """Check model availability and setup."""
    print_section_header("MODEL AVAILABILITY CHECK")
    
    try:
        is_available = masker.ollama_client.is_model_available()
        print(f"Model '{masker.ollama_client.model_name}' available: {'✅ YES' if is_available else '❌ NO'}")
        
        if not is_available:
            print("Attempting to pull model...")
            pull_success = masker.ollama_client.pull_model()
            print(f"Model pull result: {'✅ SUCCESS' if pull_success else '❌ FAILED'}")
            
    except Exception as e:
        print(f"❌ Model check failed: {e}")


def main():
    """Main demo function."""
    setup_logging()
    
    print("🔒 COMPREHENSIVE PII MASKING SYSTEM DEMO")
    print("🤖 Using Ollama with llama3.2 model")
    print("📝 Testing defensive security PII masking capabilities")
    
    # Initialize masker
    try:
        masker = PIIMasker(model_name="llama3.2")
        print("✅ PIIMasker initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PIIMasker: {e}")
        return
    
    # Run all demo functions
    demo_functions = [
        check_model_availability,
        demo_basic_pii_masking,
        demo_conversational_scenarios,
        demo_edge_cases,
        demo_batch_processing,
        demo_pii_statistics,
        demo_regex_fallback,
        demo_performance,
    ]
    
    total_demos = len(demo_functions)
    completed_demos = 0
    
    for demo_func in demo_functions:
        try:
            demo_func(masker)
            completed_demos += 1
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Demo section '{demo_func.__name__}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print_section_header("DEMO SUMMARY")
    print(f"✅ Completed {completed_demos}/{total_demos} demo sections")
    print("🔒 PII Masking System demo completed")
    print("\n💡 Key Features Demonstrated:")
    print("  • AI-powered PII detection and masking")
    print("  • Regex fallback for reliability") 
    print("  • Batch processing capabilities")
    print("  • Conversational text handling")
    print("  • Performance across different text sizes")
    print("  • Robust error handling")


if __name__ == "__main__":
    main()