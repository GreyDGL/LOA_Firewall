# LoA Firewall - LLM Content Security Solution

A comprehensive, production-ready firewall solution for securing LLM interactions with dual-layer content filtering, AI-based guards, and enterprise licensing.

## 🚀 Quick Start

For **clients** deploying the firewall:
- See [Client Installation Guide](docs/client/INSTALL.md)
- See [Client Deployment Guide](docs/client/CLIENT_DEPLOYMENT.md)

For **vendors** delivering to clients:
- See [Vendor Delivery Instructions](docs/vendor/VENDOR_DELIVERY_INSTRUCTIONS.md)
- See [Secure Delivery Guide](docs/vendor/SECURE_DELIVERY.md)

For **developers** working on the codebase:
- See [Development Documentation](docs/development/)

## 📁 Project Structure

```
LoAFirewall/
├── src/                           # Core application code
│   ├── core/                      # Core firewall components
│   │   ├── firewall.py            # Main firewall orchestrator
│   │   ├── category_manager.py    # Category conflict resolution
│   │   └── config_manager.py      # Configuration management
│   ├── api/                       # API layer
│   │   ├── api.py                 # Flask REST API
│   │   └── service.py             # Firewall service with licensing
│   ├── guards/                    # AI guard implementations
│   │   ├── base_guard.py          # Abstract base class
│   │   ├── llama_guard.py         # LLaMA Guard 3 implementation
│   │   └── granite_guard.py       # IBM Granite Guardian
│   ├── filters/                   # Filtering components
│   │   └── keyword_filter.py      # Keyword/regex filtering
│   └── licensing/                 # License management
│       ├── license_manager.py     # License validation
│       └── generate_license.py    # License generation
├── config/                        # Configuration files
│   ├── config.json               # Main configuration
│   ├── config.py                 # Configuration constants
│   └── blacklists/               # Keyword blacklists
├── deployment/                    # Deployment files
│   ├── docker/                   # Docker configurations
│   ├── scripts/                  # Build and deployment scripts
│   └── client-packages/          # Pre-built client packages
├── docs/                         # Documentation
│   ├── client/                   # Client-facing documentation
│   ├── vendor/                   # Vendor/delivery documentation
│   └── development/              # Development documentation
├── examples/                     # Demos and examples
│   ├── demos/                    # Demo applications
│   └── client/                   # Client example code
├── tests/                        # Test files
├── logs/                         # Log files (created at runtime)
├── pyproject.toml               # Python project configuration
├── poetry.lock                  # Dependency lock file
└── run.py                       # Main entry point
```

## 🛡️ Architecture Overview

The firewall uses a multi-layer approach:

1. **Keyword Filter**: Fast regex-based detection for known patterns
2. **AI Guards**: Multiple AI models for comprehensive content analysis
   - Primary Guard: Advanced content classification and threat detection
   - Secondary Guard: Additional safety validation and cross-verification
3. **Category Resolution**: Intelligent conflict resolution and consensus building
4. **Licensing**: Time-based license validation for commercial deployment

## 🚀 Running the Firewall

### Development Mode

```bash
# Install dependencies
poetry install

# Run with default configuration
python run.py

# Run with custom configuration
python run.py --config config/config.json --host 0.0.0.0 --port 5001
```

### Production Mode

```bash
# Using Docker Compose (recommended)
cd deployment/docker
docker-compose up -d

# Using the service wrapper
python src/api/service.py
```

## 🧪 Testing & Demos

### Run Demos

```bash
# Command-line demo
python examples/demos/demo.py

# Web interface demo
python examples/demos/web_demo.py
# Visit http://localhost:8080
```

### Run Tests

```bash
# Basic API tests
python tests/test_keywords_api.py

# Firewall integration tests  
python tests/firewall_test_cases.py
```

## 📖 API Usage

### Basic Content Check

```bash
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Your content to analyze"}'
```

### Response Format

**Safe Content Response:**
```json
{
  "request_id": "abc-123-def",
  "is_safe": true,
  "category": "safe",
  "confidence": "high",
  "reason": "Content analysis completed successfully",
  "analysis": {
    "guards": [
      {"guard_id": "guard_1", "status": "safe", "confidence": "normal"},
      {"guard_id": "guard_2", "status": "safe", "confidence": "normal"}
    ],
    "keyword_filter": {
      "enabled": true,
      "status": "safe",
      "matches_found": 0
    },
    "consensus": true
  },
  "processing_time_ms": 245.67,
  "timestamp": 1673234567.123
}
```

**Unsafe Content Response:**
```json
{
  "request_id": "def-456-ghi",
  "is_safe": false,
  "category": "harmful_content",
  "confidence": "high",
  "reason": "Unsafe content detected",
  "analysis": {
    "guards": [
      {
        "guard_id": "guard_1",
        "status": "flagged",
        "confidence": "normal",
        "detection_type": "harmful_content"
      },
      {"guard_id": "guard_2", "status": "safe", "confidence": "normal"}
    ],
    "keyword_filter": {
      "enabled": true,
      "status": "safe", 
      "matches_found": 0
    },
    "consensus": false
  },
  "processing_time_ms": 312.45,
  "timestamp": 1673234567.123
}
```

### Response Fields

- **is_safe**: Boolean indicating if content is safe
- **category**: Content classification (`safe`, `harmful_content`, `policy_violation`, `injection_attempt`, `unsafe_content`)
- **confidence**: Analysis confidence level (`high`, `medium`, `low`)
- **reason**: Human-readable explanation of the decision
- **analysis.guards**: Summary of guard results (anonymized)
- **analysis.keyword_filter**: Keyword filtering summary
- **analysis.consensus**: Whether all guards agreed
- **processing_time_ms**: Processing time in milliseconds

### Additional API Endpoints

**Health Check:**
```bash
curl http://localhost:5001/health
```

**Get Current Keywords:**
```bash  
curl http://localhost:5001/keywords
```

**Update Keywords:**
```bash
curl -X PUT http://localhost:5001/keywords \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["malware", "hack"], "regex_patterns": ["\\bpassword\\b"]}'
```

**Get Statistics:**
```bash
curl http://localhost:5001/stats  
```

### Error Handling

The API returns appropriate HTTP status codes:
- **200**: Success
- **400**: Bad request (missing fields, invalid JSON)
- **403**: License validation failed  
- **500**: Internal server error

All error responses include:
```json
{
  "error": "Error description",
  "request_id": "unique-request-id",
  "message": "Detailed error message"
}
```

## ⚙️ Configuration

Main configuration is in `config/config.json`:

- **Keyword Filter**: Enable/disable, blacklist files, short-circuit behavior
- **AI Guards**: Model configurations, category mappings, thresholds  
- **Categories**: Unified category system, conflict resolution strategies
- **API**: Host, port, logging settings

## 🔐 Security Features

- **License-based Access**: Time-limited, encrypted licenses
- **Fail-safe Design**: Graceful degradation with safety fallbacks
- **Docker Isolation**: Containerized deployment options
- **Category Mapping**: Unified threat classification system
- **Sanitized Responses**: Implementation details protected from clients
- **Comprehensive Logging**: Detailed audit trails for analysis and monitoring
- **Timeout Protection**: Prevents hanging operations with automatic fallbacks

## 📦 Building & Deployment

### Client Package Generation

```bash
cd deployment/scripts

# Generate client package with license
python build_client_image.py \
  --customer "Client Name" \
  --tag "firewall:client-v1.0" \
  --secret "master-secret-key" \
  --days 180
```

### Binary Distribution

```bash
# Build standalone binary
python deployment/scripts/build_binary.py
```

## 🔧 Development

### Adding New Guards

1. Create new guard class extending `BaseGuard`
2. Implement `initialize()` and `check_content()` methods
3. Register in `firewall.py` guard registry
4. Add configuration to `config.json`

### Adding New Filters

1. Create filter class in `src/filters/`
2. Implement filtering logic
3. Integrate in `firewall.py` pipeline

## 📋 Requirements

- **Python**: 3.8+
- **Memory**: 4GB+ RAM (8GB recommended)
- **Storage**: 10GB+ for models
- **Network**: Internet access for model downloads
- **Docker**: For containerized deployment

## 📄 License

This software requires a valid license key for operation. Contact your vendor for licensing information.

## 🆘 Support

1. **Check Documentation**: Relevant guides in `docs/` directory
2. **Review Logs**: Check `logs/firewall.log` for errors
3. **Run Health Check**: `curl http://localhost:5001/health`
4. **Contact Vendor**: For licensing and support issues


## TODO:
1. Feedback loop: design a button to send false label/data to the server.