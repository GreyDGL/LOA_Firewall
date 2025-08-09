"""
Utility functions for PII detection and masking

This module provides additional utility functions for enhanced PII detection
and validation.
"""

import re
from typing import List, Dict, Tuple, Optional


class PIIPatterns:
    """Collection of regex patterns for various PII types."""
    
    # Phone number patterns
    PHONE_PATTERNS = [
        r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
        r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}',  # International
        r'\([0-9]{3}\)\s?[0-9]{3}-[0-9]{4}',  # (123) 456-7890
        r'[0-9]{3}-[0-9]{3}-[0-9]{4}',  # 123-456-7890
        r'[0-9]{10}',  # 1234567890 (10 digits)
    ]
    
    # Personal ID patterns
    PERSONAL_ID_PATTERNS = [
        r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
        r'\b[A-Z]{1,2}[0-9]{6,8}\b',  # Driver's license (varies by state)
        r'\b[A-Z0-9]{9}\b',  # Passport number
        r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card
        r'\b[A-Z]{2}[0-9]{6}[A-Z]?\b',  # Tax ID
    ]
    
    # Email pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Address patterns (basic)
    ADDRESS_PATTERNS = [
        r'\b\d{1,5}\s[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b',
        r'\b\d{5}(-\d{4})?\b',  # ZIP code
    ]
    
    # Name patterns (basic - these are less reliable)
    NAME_PATTERNS = [
        r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # First Last
        r'\b[A-Z][a-z]+\s[A-Z]\.\s[A-Z][a-z]+\b',  # First M. Last
        r'\b[A-Z][a-z]+\s[A-Z][a-z]+\s[A-Z][a-z]+\b',  # First Middle Last
    ]


class PIIDetector:
    """Enhanced PII detection using regex patterns."""
    
    def __init__(self):
        self.patterns = PIIPatterns()
        
    def detect_phones(self, text: str) -> List[Dict]:
        """Detect phone numbers in text."""
        detected = []
        for pattern in self.patterns.PHONE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append({
                    'type': 'phone',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })
        return detected
    
    def detect_personal_ids(self, text: str) -> List[Dict]:
        """Detect personal IDs in text."""
        detected = []
        for pattern in self.patterns.PERSONAL_ID_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append({
                    'type': 'personal_id',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8
                })
        return detected
    
    def detect_emails(self, text: str) -> List[Dict]:
        """Detect email addresses in text."""
        detected = []
        matches = re.finditer(self.patterns.EMAIL_PATTERN, text)
        for match in matches:
            detected.append({
                'type': 'email',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.95
            })
        return detected
    
    def detect_addresses(self, text: str) -> List[Dict]:
        """Detect addresses in text."""
        detected = []
        for pattern in self.patterns.ADDRESS_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append({
                    'type': 'address',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.7
                })
        return detected
    
    def detect_names(self, text: str) -> List[Dict]:
        """Detect potential names in text (less reliable)."""
        detected = []
        for pattern in self.patterns.NAME_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Additional filtering to reduce false positives
                name = match.group()
                if self._is_likely_name(name):
                    detected.append({
                        'type': 'name',
                        'value': name,
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.6
                    })
        return detected
    
    def _is_likely_name(self, text: str) -> bool:
        """Check if text is likely a name (basic filtering)."""
        # Filter out common false positives
        common_false_positives = {
            'United States', 'New York', 'Los Angeles', 'San Francisco',
            'Data Science', 'Machine Learning', 'Python Programming',
            'John Doe', 'Jane Doe'  # Common placeholder names
        }
        
        return text not in common_false_positives
    
    def detect_all_pii(self, text: str) -> List[Dict]:
        """Detect all types of PII in text."""
        all_detected = []
        
        all_detected.extend(self.detect_phones(text))
        all_detected.extend(self.detect_personal_ids(text))
        all_detected.extend(self.detect_emails(text))
        all_detected.extend(self.detect_addresses(text))
        all_detected.extend(self.detect_names(text))
        
        # Sort by start position
        all_detected.sort(key=lambda x: x['start'])
        
        return all_detected


class PIIMaskingUtils:
    """Utility functions for PII masking operations."""
    
    @staticmethod
    def mask_entities(text: str, entities: List[Dict], mask_char: str = "*", mask_length: int = 7) -> str:
        """
        Mask detected PII entities in text.
        
        Args:
            text: Original text
            entities: List of detected PII entities
            mask_char: Character to use for masking
            mask_length: Length of mask string
            
        Returns:
            str: Text with entities masked
        """
        if not entities:
            return text
        
        # Sort entities by start position in reverse order to maintain positions
        sorted_entities = sorted(entities, key=lambda x: x['start'], reverse=True)
        
        masked_text = text
        mask_string = mask_char * mask_length
        
        for entity in sorted_entities:
            start = entity['start']
            end = entity['end']
            masked_text = masked_text[:start] + mask_string + masked_text[end:]
        
        return masked_text
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate if a string is a valid phone number."""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Check if it's a valid US phone number (10 or 11 digits)
        if len(digits) in [10, 11]:
            if len(digits) == 11 and digits[0] == '1':
                return True
            elif len(digits) == 10:
                return True
        
        return False
    
    @staticmethod
    def validate_ssn(ssn: str) -> bool:
        """Validate if a string is a valid SSN format."""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', ssn)
        
        # SSN should be exactly 9 digits
        if len(digits) != 9:
            return False
        
        # Basic validation rules
        # SSN cannot be all zeros, or start with 666, or 900-999
        if digits == '000000000':
            return False
        if digits.startswith('666'):
            return False
        if digits.startswith(('900', '901', '902', '903', '904', '905', '906', '907', '908', '909')):
            return False
        
        return True
    
    @staticmethod
    def get_entity_context(text: str, entity: Dict, context_length: int = 20) -> str:
        """
        Get context around a detected PII entity.
        
        Args:
            text: Original text
            entity: Detected entity
            context_length: Number of characters before and after the entity
            
        Returns:
            str: Context string
        """
        start = max(0, entity['start'] - context_length)
        end = min(len(text), entity['end'] + context_length)
        
        context = text[start:end]
        entity_in_context = text[entity['start']:entity['end']]
        
        return f"...{context}... (detected: '{entity_in_context}')"