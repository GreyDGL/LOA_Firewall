# LoA Firewall - Development Guide

This guide is for developers working on the LoA Firewall codebase.

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- Docker (for containerized testing)
- Git

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd LoAFirewall

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Verify installation
python run.py --help
```

## 🏗️ Project Architecture

### Core Components

- **`src/core/firewall.py`**: Main orchestrator that manages the filtering pipeline
- **`src/core/category_manager.py`**: Handles category conflict resolution between guards
- **`src/core/config_manager.py`**: Configuration loading and validation

### API Layer

- **`src/api/api.py`**: Flask REST API endpoints
- **`src/api/service.py`**: Service wrapper with licensing validation

### Content Guards

- **`src/guards/base_guard.py`**: Abstract base class for all guards
- **`src/guards/llama_guard.py`**: LLaMA Guard 3 implementation
- **`src/guards/granite_guard.py`**: IBM Granite Guardian implementation

### Filtering

- **`src/filters/keyword_filter.py`**: Keyword and regex-based filtering

### Licensing

- **`src/licensing/license_manager.py`**: License validation and management
- **`src/licensing/generate_license.py`**: License key generation

## 🔧 Development Tasks

### Running Tests

```bash
# API integration tests
python tests/test_keywords_api.py

# Firewall component tests
python tests/firewall_test_cases.py

# Guard validation (requires models)
python src/guards/llama_guard.py
python src/guards/granite_guard.py
```

### Running Demos

```bash
# Command-line demo
python examples/demos/demo.py

# Web interface demo
python examples/demos/web_demo.py
# Visit http://localhost:8080
```

### Local Development Server

```bash
# Run with default config
python run.py

# Run with custom config
python run.py --config config/config.json --debug

# Run with logging
python run.py --log-level DEBUG --log-file logs/dev.log
```

## 🔌 Adding New Guards

1. **Create Guard Class**:
   ```python
   from src.guards.base_guard import BaseGuard
   
   class MyGuard(BaseGuard):
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           
       def initialize(self):
           # Setup your guard here
           return True
           
       def check_content(self, text):
           # Implement your guard logic
           return {
               "is_safe": True,
               "category": "safe",
               "raw_category": "safe",
               "reason": "Content is safe",
               "model": "my-guard",
               "raw_response": "Safe"
           }
   ```

2. **Register in Firewall**:
   ```python
   # In src/core/firewall.py
   self.guard_registry = {
       "my_guard": "src.guards.my_guard.MyGuard"
   }
   ```

3. **Add Configuration**:
   ```json
   // In config/config.json
   {
     "guards": [
       {
         "type": "my_guard",
         "enabled": true,
         "category_mapping": {
           "safe": "safe",
           "unsafe": "unknown_unsafe"
         }
       }
     ]
   }
   ```

## 🧪 Testing Guards

```bash
# Validate guard implementation
python src/guards/my_guard.py

# Test with sample content
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Test content"}'
```

## 📝 Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include docstrings for all classes and methods
- Keep imports organized (standard, third-party, local)

### Example Function

```python
def check_content(self, text: str) -> Dict[str, Any]:
    """
    Check if content is safe
    
    Args:
        text (str): Content to analyze
        
    Returns:
        Dict[str, Any]: Analysis result with safety determination
    """
    # Implementation here
    pass
```

## 🐛 Debugging

### Common Issues

1. **Import Errors**: Ensure you're running from project root and imports use full paths
2. **Config Not Found**: Check that `config/config.json` exists and is valid
3. **Guard Initialization**: Verify required models are available (LLaMA/Granite)

### Debug Logging

```bash
# Enable debug logging
python run.py --log-level DEBUG

# Check logs
tail -f logs/firewall.log
```

### Health Checks

```bash
# API health
curl http://localhost:5001/health

# Guard status
curl http://localhost:5001/check -d '{"text":"test"}' -H "Content-Type: application/json"
```

## 🚀 Building & Deployment

### Docker Build

```bash
cd deployment/docker
docker build -t llm-firewall:dev .
```

### Client Package

```bash
cd deployment/scripts
python build_client_image.py --customer "Test Client" --tag "firewall:test" --secret "test-secret" --days 30
```

## 📊 Performance Monitoring

### Timing Analysis

The firewall includes built-in timing for:
- Total request processing
- Individual guard execution
- Category resolution

Check response `processing_times` field for performance data.

### Memory Usage

Monitor memory usage especially when:
- Loading multiple LLM models
- Processing large text inputs
- Running multiple concurrent requests

## 🔐 Security Considerations

- Never commit license keys or secrets
- Use environment variables for sensitive configuration
- Validate all inputs thoroughly
- Follow principle of least privilege
- Implement proper error handling (fail closed)

## 📖 Documentation

- Update this guide when adding new features
- Include examples in docstrings
- Update API documentation for endpoint changes
- Keep configuration examples current