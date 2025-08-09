"""
Ollama Client for PII Masking using modern Ollama API
"""

import ollama
import logging
from typing import Optional


class OllamaClient:
    """Client for interacting with local Ollama models."""
    
    def __init__(self, model_name: str = "llama3.2", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.client = ollama.Client(host=host) if host != "http://localhost:11434" else None
        self.logger = logging.getLogger(__name__)
        
    def is_model_available(self) -> bool:
        """Check if the specified model is available in Ollama."""
        try:
            response = ollama.list() if not self.client else self.client.list()
            available_models = [model.model for model in response.models]
            return any(self.model_name in model for model in available_models)
        except Exception as e:
            self.logger.error(f"Error checking model availability: {e}")
            return False
    
    def pull_model(self) -> bool:
        """Pull the model if it's not available locally."""
        try:
            self.logger.info(f"Pulling model {self.model_name}...")
            ollama.pull(self.model_name) if not self.client else self.client.pull(self.model_name)
            return True
        except Exception as e:
            self.logger.error(f"Error pulling model {self.model_name}: {e}")
            return False
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Generate a response from the Ollama model."""
        try:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            if self.client:
                response = self.client.chat(model=self.model_name, messages=messages)
            else:
                response = ollama.chat(model=self.model_name, messages=messages)
            
            return response.message.content
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None
    
    def detect_pii(self, text: str) -> Optional[str]:
        """Detect PII in the given text using the Ollama model."""
        system_prompt = """You are a PII detection expert. Identify personally identifiable information in the given text.

Identify: Names, Phone numbers, Personal IDs (SSN, etc.), Email addresses, Addresses

Respond ONLY with JSON format:
{"pii_detected": true/false, "entities": [{"type": "name|phone|personal_id|email|address", "value": "detected_value", "start": start_position, "end": end_position}]}

Be precise and avoid false positives."""

        return self.generate_response(text, system_prompt)
    
    def extract_additional_pii(self, original_text: str, regex_masked_text: str) -> Optional[str]:
        """Extract additional PII that wasn't caught by regex, from the original text."""
        system_prompt = """You are a conservative PII extraction expert. You will be given an original text and a regex-masked version. Your task is to identify ONLY additional personal identifiable information in the ORIGINAL text that wasn't already masked by regex patterns.

CRITICAL RULES:
1. Be CONSERVATIVE but identify obvious personally identifiable information
2. Only identify PII that exists EXACTLY in the original text  
3. Return ONLY a JSON array of objects with "text" and "category" fields
4. Extract the exact strings as they appear in the original text
5. Ignore anything already masked with **category** format

PII types to look for and their categories:
- Organization names in personal context → "organization" 
- Street addresses or locations → "address"
- Account numbers or specific IDs → "id"

DO NOT mask:
- Generic words like "your", "his", "her", "office", "number", "phone", "email"  
- Job titles (e.g., "doctor", "manager")
- Person names (e.g., "John Smith", "Dr. Wilson")
- Generic locations (e.g., "office", "home")
- Already masked content (**category**)

RESPONSE FORMAT - Must be exact JSON array of objects:
[{"text": "Microsoft Corp", "category": "organization"}, {"text": "123 Main St", "category": "address"}]

Example:
Original: "Contact John Smith at john@email.com or 555-1234 for Microsoft Corp"
Regex-masked: "Contact John Smith at **email** or **phone** for Microsoft Corp"
Response: [{"text": "Microsoft Corp", "category": "organization"}]

Another example:
Original: "Call your doctor at 555-0123"
Regex-masked: "Call your doctor at **phone**"
Response: []

Only extract specific PII that should be masked but wasn't already masked by regex."""

        user_prompt = f'''Original text: "{original_text}"
Regex-masked text: "{regex_masked_text}"

Extract additional PII from the original text:'''
        
        return self.generate_response(user_prompt, system_prompt)