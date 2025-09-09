"""
PII Masker - Core functionality for masking personally identifiable information
"""

import json
import re
import logging
from typing import Dict, List
from .ollama_client import OllamaClient


class PIIMasker:
    """Main class for PII detection and masking using Ollama models."""
    
    def __init__(self, model_name: str = "llama3.2", host: str = "http://localhost:11434"):
        self.ollama_client = OllamaClient(model_name, host)
        self.logger = logging.getLogger(__name__)
        self.mask_replacement = "*******"
        
        # Regex patterns for fallback masking with categories
        # Order matters: more specific patterns should come first
        self.patterns = {
            'credit_card': {
                'pattern': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b|\b\d{13,19}\b'),
                'mask': '**credit_card**'
            },
            'ssn': {
                'pattern': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
                'mask': '**ssn**'
            },
            'phone': {
                'pattern': re.compile(r'\b(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b|\b[0-9]{8,12}\b'),
                'mask': '**phone**'
            },
            'email': {
                'pattern': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                'mask': '**email**'
            }
        }
        
    def ensure_model_ready(self) -> bool:
        """Ensure the Ollama model is available and ready to use."""
        if not self.ollama_client.is_model_available():
            self.logger.info(f"Pulling model {self.ollama_client.model_name}...")
            return self.ollama_client.pull_model()
        return True
    
    def _regex_fallback_masking(self, text: str) -> str:
        """Fallback PII masking using regex patterns with categories."""
        masked_text = text
        for category, config in self.patterns.items():
            pattern = config['pattern']
            mask = config['mask']
            masked_text = pattern.sub(mask, masked_text)
        return masked_text
    
    def detect_pii_entities(self, text: str) -> List[Dict]:
        """Detect PII entities in text using Ollama model."""
        if not self.ensure_model_ready():
            return []
        
        try:
            response = self.ollama_client.detect_pii(text)
            if response:
                parsed = json.loads(response)
                return parsed.get('entities', []) if parsed.get('pii_detected') else []
        except Exception as e:
            self.logger.error(f"PII detection failed: {e}")
        return []
    
    def mask_text(self, text: str, use_ai: bool = True) -> str:
        """Main method to mask PII in text using two-pass approach."""
        if not text or not text.strip():
            return text
        
        # Pass 1: Apply regex masking first
        regex_masked = self._regex_fallback_masking(text)
        
        # Pass 2: Use AI to find additional PII not caught by regex
        if use_ai and self.ensure_model_ready():
            try:
                # Only proceed if regex didn't catch everything or we want AI validation
                additional_pii = self._extract_additional_pii(text, regex_masked)
                if additional_pii:
                    return self._apply_additional_masking(regex_masked, text, additional_pii)
            except Exception as e:
                self.logger.error(f"AI PII extraction failed: {e}")
        
        return regex_masked
    
    def _extract_additional_pii(self, original_text: str, regex_masked_text: str) -> List[Dict]:
        """Extract additional PII using AI that wasn't caught by regex."""
        try:
            response = self.ollama_client.extract_additional_pii(original_text, regex_masked_text)
            if not response:
                return []
            
            # Parse JSON response
            import json
            pii_list = json.loads(response.strip())
            
            # Validate it's a list
            if not isinstance(pii_list, list):
                self.logger.warning(f"Invalid PII extraction response format: {response}")
                return []
            
            # Common false positives to filter out
            false_positives = {
                'your', 'his', 'her', 'their', 'my', 'our', 'your phone', 'your email',
                'office', 'home', 'phone', 'number', 'email', 'address', 'contact',
                'doctor', 'manager', 'boss', 'colleague', 'client', 'customer',
                'phone number', 'email address', 'office number', 'the', 'a', 'an',
                'his office', 'her office', 'your office', 'john', 'smith', 'brown',
                'johnson', 'wilson', 'davis', 'miller', 'example', 'com', 'inc', 'corp'
            }
            
            # Filter and validate PII
            validated_pii = []
            for pii_item in pii_list:
                # Handle both old string format and new object format for backward compatibility
                if isinstance(pii_item, str):
                    pii_text = pii_item.strip()
                    pii_category = "unknown"
                elif isinstance(pii_item, dict) and 'text' in pii_item:
                    pii_text = pii_item['text'].strip()
                    pii_category = pii_item.get('category', 'unknown')
                else:
                    continue
                
                # Skip if it's a common false positive
                if pii_text.lower() in false_positives:
                    self.logger.debug(f"Skipping false positive: '{pii_text}'")
                    continue
                
                # Skip if it's too short (likely not real PII) 
                if len(pii_text) < 3:
                    self.logger.debug(f"Skipping too short: '{pii_text}'")
                    continue
                
                # Skip if it looks like part of an email domain
                if '.' in pii_text and len(pii_text.split('.')) == 2:
                    self.logger.debug(f"Skipping potential domain part: '{pii_text}'")
                    continue
                
                # Check if this PII actually exists in the original text
                if pii_text in original_text:
                    # Check if this area is not already masked by regex
                    original_index = original_text.find(pii_text)
                    if original_index != -1:
                        corresponding_area = regex_masked_text[original_index:original_index + len(pii_text)]
                        # Check if area contains any **category** markers (regex masking)
                        if '**' not in corresponding_area:
                            validated_pii.append({'text': pii_text, 'category': pii_category})
                        else:
                            self.logger.debug(f"Skipping already masked PII: '{pii_text}'")
                    else:
                        validated_pii.append({'text': pii_text, 'category': pii_category})
                else:
                    self.logger.debug(f"Skipping invalid PII extraction: '{pii_text}' not found in original text")
            
            return validated_pii
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse PII extraction JSON: {e}")
            return []
        except Exception as e:
            self.logger.error(f"PII extraction error: {e}")
            return []
    
    def _apply_additional_masking(self, regex_masked_text: str, original_text: str, additional_pii: List[Dict]) -> str:
        """Apply additional masking for PII found by AI with categories."""
        result = regex_masked_text
        
        # Sort by text length (longest first) to avoid partial replacements
        sorted_pii = sorted(additional_pii, key=lambda x: len(x['text']), reverse=True)
        
        for pii_item in sorted_pii:
            pii_text = pii_item['text']
            pii_category = pii_item['category']
            
            # Create categorized mask
            categorized_mask = f"**{pii_category}**"
            
            # Only replace if the PII exists in both original and current result
            # This prevents replacing already masked content
            if pii_text in original_text and pii_text in result:
                result = result.replace(pii_text, categorized_mask)
                self.logger.debug(f"Masked additional PII: '{pii_text}' as {categorized_mask}")
        
        return result
    
    def mask_text_with_details(self, text: str, use_ai: bool = True) -> Dict:
        """Mask PII and return detailed information about what was masked."""
        if not text or not text.strip():
            return {
                'original_text': text,
                'masked_text': text,
                'regex_masked_count': 0,
                'ai_masked_count': 0,
                'ai_extracted_pii': [],
                'method_used': 'none'
            }
        
        # Pass 1: Apply regex masking first
        regex_masked = self._regex_fallback_masking(text)
        regex_masked_count = text.count(self.mask_replacement) - regex_masked.count(self.mask_replacement) + regex_masked.count(self.mask_replacement)
        
        # Calculate regex masking count by counting differences
        original_parts = text.split()
        regex_parts = regex_masked.split()
        regex_changes = sum(1 for i, (orig, masked) in enumerate(zip(original_parts, regex_parts)) if orig != masked and self.mask_replacement in masked)
        
        result = {
            'original_text': text,
            'masked_text': regex_masked,
            'regex_masked_count': regex_changes,
            'ai_masked_count': 0,
            'ai_extracted_pii': [],
            'method_used': 'regex_only'
        }
        
        # Pass 2: Use AI to find additional PII
        if use_ai and self.ensure_model_ready():
            try:
                additional_pii = self._extract_additional_pii(text, regex_masked)
                if additional_pii:
                    final_masked = self._apply_additional_masking(regex_masked, text, additional_pii)
                    # Extract just the text for backward compatibility
                    ai_pii_texts = [item['text'] for item in additional_pii]
                    result.update({
                        'masked_text': final_masked,
                        'ai_masked_count': len(additional_pii),
                        'ai_extracted_pii': ai_pii_texts,
                        'ai_extracted_pii_detailed': additional_pii,  # Include categories
                        'method_used': 'regex_and_ai'
                    })
                else:
                    result['method_used'] = 'regex_and_ai_no_additional'
            except Exception as e:
                self.logger.error(f"AI PII extraction failed: {e}")
                result['method_used'] = 'regex_with_ai_error'
        
        return result
    
    def process_batch(self, texts: List[str], use_ai: bool = True) -> List[str]:
        """Process a batch of texts for PII masking."""
        return [self.mask_text(text, use_ai) for text in texts]
    
    def get_pii_statistics(self, text: str) -> Dict:
        """Get statistics about PII detected in the text."""
        entities = self.detect_pii_entities(text)
        stats = {'total_entities': len(entities), 'entity_types': {}}
        
        for entity in entities:
            entity_type = entity.get('type', 'unknown')
            stats['entity_types'][entity_type] = stats['entity_types'].get(entity_type, 0) + 1
        
        return stats