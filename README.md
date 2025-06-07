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
2. **AI Guards**: Multiple AI models for content analysis:
   - LLaMA Guard 3: Detects 14 categories of harmful content
   - IBM Granite Guardian: Additional safety analysis
3. **Category Resolution**: Smart conflict resolution between guard outputs
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

```json
{
  "is_safe": true,
  "overall_reason": "Content is safe",
  "keyword_filter_result": {
    "is_safe": true,
    "reason": "No harmful keywords detected"
  },
  "guard_results": [
    {
      "is_safe": true,
      "category": "safe",
      "model": "llm-guard-1"
    }
  ],
  "category_analysis": {
    "final_category": "safe",
    "resolution_method": "consensus"
  },
  "processing_times": {
    "total": 0.123
  }
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
- **Fail-closed Design**: Defaults to blocking on errors
- **Docker Isolation**: Containerized deployment
- **Category Mapping**: Unified threat classification
- **Audit Logging**: Comprehensive request/response logging

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