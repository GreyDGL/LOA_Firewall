# PII Masking Module (Musk)

The Musk module provides functionality to detect and mask personally identifiable information (PII) using local Ollama models, specifically designed to work with llama3.2.

## Features

- **AI-powered PII detection and masking** using Ollama/llama3.2
- **Regex-based fallback** for when AI models are unavailable
- **Multiple PII types supported**: names, phone numbers, SSNs, emails, addresses, personal IDs
- **Batch processing** capabilities
- **Validation utilities** for phone numbers and SSNs
- **Flexible masking options** with customizable mask characters

## Prerequisites

1. **Ollama installed and running locally**:
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   
   # Pull llama3.2 model
   ollama pull llama3.2
   ```

2. **Python dependencies** (already included in pyproject.toml):
   - `ollama>=0.4.8`

## Quick Start

### Basic Usage

```python
from src.musk import PIIMasker

# Initialize the masker
masker = PIIMasker(model_name="llama3.2")

# Mask PII in text
text = "Hi, I'm John Smith and my phone is 555-123-4567"
masked_text = masker.mask_text(text)
print(masked_text)  # "Hi, I'm ******* and my phone is *******"
```

### Using Regex-only Mode

```python
# Use regex-based masking without AI
masked_text = masker.mask_text(text, use_ai=False)
```

### Batch Processing

```python
texts = [
    "Contact John at 555-0001",
    "Email: jane@example.com", 
    "SSN: 123-45-6789"
]

masked_texts = masker.process_batch(texts)
```

### PII Detection and Statistics

```python
# Get detailed PII statistics
stats = masker.get_pii_statistics(text)
print(f"Found {stats['total_entities']} PII entities")
print(f"Entity types: {stats['entity_types']}")
```

### Using Utility Functions

```python
from src.musk.utils import PIIDetector, PIIMaskingUtils

# Detect PII with regex patterns
detector = PIIDetector()
entities = detector.detect_all_pii(text)

# Manual masking with custom parameters
masked = PIIMaskingUtils.mask_entities(text, entities, mask_char="#", mask_length=5)
```

## Module Structure

- **`pii_masker.py`**: Main PIIMasker class with AI and fallback functionality
- **`ollama_client.py`**: Client for interacting with local Ollama models
- **`utils.py`**: Utility classes for regex-based detection and validation
- **`__init__.py`**: Module exports

## Demo Script

Run the demo script to see the module in action:

```bash
cd /Users/gelei/Research/LOA/LoAFirewall
python examples/demos/pii_masking_demo.py
```

The demo includes:
- Basic PII masking examples
- Regex-based detection demonstration
- Batch processing examples
- PII validation utilities

## Supported PII Types

1. **Names**: First/last names, full names
2. **Phone Numbers**: Various formats (US/International)
3. **Personal IDs**: SSN, driver's license, passport numbers
4. **Email Addresses**: Standard email formats  
5. **Addresses**: Street addresses and ZIP codes
6. **Credit Cards**: Standard card number formats

## Configuration

### Model Configuration

```python
# Use different Ollama model
masker = PIIMasker(model_name="llama2", host="http://localhost:11434")

# Check if model is available
if masker.ensure_model_ready():
    print("Model is ready")
else:
    print("Model not available")
```

### Masking Configuration

```python
# Custom mask replacement
masker.mask_replacement = "###REDACTED###"

# Or use utils for custom masking
PIIMaskingUtils.mask_entities(text, entities, mask_char="X", mask_length=10)
```

## Error Handling

The module gracefully handles various error conditions:
- **Ollama service unavailable**: Falls back to regex-based masking
- **Model not found**: Attempts to pull the model automatically
- **AI parsing errors**: Falls back to regex patterns
- **Invalid input**: Returns original text safely

## Integration with LoAFirewall

The Musk module integrates seamlessly with the LoAFirewall system:

```python
# In your firewall filters
from src.musk import PIIMasker

def sanitize_request(request_text):
    masker = PIIMasker()
    return masker.mask_text(request_text)
```

## Performance Notes

- **AI-based masking**: More accurate but slower (~1-2 seconds per request)
- **Regex-based masking**: Faster but less accurate for complex cases  
- **Batch processing**: More efficient for multiple texts
- **Model caching**: Ollama keeps models in memory for faster subsequent requests

## Troubleshooting

1. **"Model not available" error**: Ensure Ollama is running and llama3.2 is pulled
2. **Connection refused**: Check if Ollama service is running on port 11434
3. **Slow performance**: Consider using regex-only mode for high-throughput scenarios
4. **False positives**: Fine-tune regex patterns in `utils.py` as needed