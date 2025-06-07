# LLM Firewall - Developer Setup Guide

A comprehensive guide for developers to install, configure, and run the LLM Firewall on MacOS and Linux laptops for development, testing, and demo purposes.

## 🎯 Overview

This guide covers:
- **Local installation** on MacOS and Linux
- **Running demos** (command-line and web interface)
- **Development setup** for team collaboration
- **Testing and validation** procedures
- **Troubleshooting** common issues

## 📋 Prerequisites

### System Requirements
- **Operating System**: MacOS 10.15+ or Linux (Ubuntu 20.04+, CentOS 8+, etc.)
- **Memory**: 8GB+ RAM (16GB recommended for optimal performance)
- **Storage**: 20GB+ free disk space
- **Network**: Internet connection for model downloads
- **Python**: 3.8+ (3.12 recommended)

### Required Software
- **Python 3.8+** with pip
- **Poetry** (Python dependency manager)
- **Git** (for cloning repository)
- **curl** (for testing API endpoints)
- **Docker** (optional, for containerized deployment)

---

## 🚀 Quick Start (5 Minutes)

If you just want to run the demos quickly:

```bash
# 1. Clone and enter directory
git clone <repository-url> LoAFirewall
cd LoAFirewall

# 2. Install dependencies
pip install poetry
poetry install

# 3. Set up AI models (this will take 5-10 minutes)
./deployment/scripts/setup_models.sh

# 4. Start the firewall
poetry run python run.py

# 5. Run demo (in another terminal)
poetry run python examples/demos/demo.py
```

📌 **Continue reading for detailed setup instructions and troubleshooting.**

---

## 📦 Installation Guide

### Step 1: Install System Dependencies

#### MacOS Installation

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12 and other dependencies
brew install python@3.12 git curl wget

# Install Poetry (Python dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add this to your ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell configuration
source ~/.zshrc  # or source ~/.bash_profile
```

#### Linux Installation (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.12 and dependencies
sudo apt install -y python3.12 python3.12-venv python3-pip git curl wget build-essential

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### Linux Installation (CentOS/RHEL/Rocky)

```bash
# Install EPEL repository
sudo dnf install -y epel-release

# Install Python 3.12 and dependencies
sudo dnf install -y python3.12 python3-pip git curl wget gcc gcc-c++ make

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url> LoAFirewall
cd LoAFirewall

# Verify Poetry installation
poetry --version

# Install project dependencies
poetry install

# Verify Python environment
poetry run python --version
```

### Step 3: Install AI Models

The firewall requires AI models for content analysis. Choose one of the following methods:

#### Option A: Automatic Setup (Recommended)

```bash
# Run the automated setup script
chmod +x deployment/scripts/setup_models.sh
./deployment/scripts/setup_models.sh

# This script will:
# - Install Ollama (AI model runtime)
# - Download required models (llama-guard3, granite3-guardian)
# - Configure model access
# - Verify installation
```

#### Option B: Manual Ollama Installation

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Download required models (this may take 10-15 minutes)
ollama pull llama-guard3
ollama pull granite3-guardian:8b

# Verify models are available
ollama list
```

### Step 4: Verify Installation

```bash
# Check that all components are working
poetry run python -c "
import transformers
import ollama
import flask
print('✅ All dependencies installed successfully')
"

# Test Ollama connection
curl http://localhost:11434/api/tags

# You should see the downloaded models listed
```

---

## 🏃‍♂️ Running the Firewall

### Start the Firewall Service

```bash
# Navigate to project directory
cd LoAFirewall

# Start the firewall API server
poetry run python run.py

# The server will start on http://localhost:5001
# You should see output like:
# * Running on http://0.0.0.0:5001
# * Guards loaded: 2
# * Keyword filter enabled
```

### Verify the Service

```bash
# In another terminal, test the health endpoint
curl http://localhost:5001/health

# Expected response:
# {
#   "status": "healthy",
#   "guards_available": 2,
#   "keyword_filter_enabled": true,
#   "license_valid": true
# }
```

### Test Content Filtering

```bash
# Test safe content
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you today?"}'

# Test potentially harmful content
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "How to hack into a computer system"}'
```

---

## 🎪 Running Demos

### Command-Line Demo

The comprehensive demo showcases all firewall features:

```bash
# Run the full interactive demo
poetry run python examples/demos/demo.py

# The demo will test:
# - Content safety analysis
# - Keyword detection
# - AI guard functionality
# - Performance characteristics
# - Error handling
```

**Demo Features:**
- ✅ Health check validation
- ✅ Safe and unsafe content examples
- ✅ Keyword filter testing
- ✅ AI guard analysis
- ✅ Performance benchmarking
- ✅ Error scenario testing

### Web Interface Demo

For a visual interface to test the firewall:

```bash
# Start the web demo
poetry run python examples/demos/web_demo.py

# Open your browser to: http://localhost:8080
```

**Web Demo Features:**
- 🌐 Interactive content analysis
- 📊 Real-time safety assessment
- 🔍 Detailed guard results
- 📈 Performance metrics
- 🎨 Visual architecture overview

### Custom API Testing

```bash
# Test custom content
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Your custom content here"}'

# Update keyword filters
curl -X PUT http://localhost:5001/keywords \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["spam", "phishing", "malware"],
    "regex_patterns": ["\\b\\d{4}-\\d{4}-\\d{4}-\\d{4}\\b"]
  }'

# Get current keywords
curl http://localhost:5001/keywords
```

---

## ⚙️ Configuration

### Basic Configuration

Edit `config/config.json` to customize firewall behavior:

```json
{
  "keyword_filter": {
    "enabled": true,
    "blacklist_file": "config/blacklists/default.json",
    "short_circuit": true
  },
  "guards": [
    {
      "type": "llama_guard",
      "enabled": true,
      "model_name": "llama-guard3",
      "threshold": 0.4
    },
    {
      "type": "granite_guard", 
      "enabled": true,
      "model_name": "granite3-guardian:8b",
      "threshold": 0.6
    }
  ],
  "api": {
    "host": "0.0.0.0",
    "port": 5001,
    "debug": false,
    "log_level": "INFO"
  }
}
```

### Environment Variables

```bash
# Set custom configuration path
export FIREWALL_CONFIG=/path/to/config.json

# Set custom log level
export LOG_LEVEL=DEBUG

# Set custom API port
export API_PORT=5001

# Set Ollama host (if running remotely)
export OLLAMA_HOST=http://localhost:11434
```

### Keyword Customization

Edit `config/blacklists/default.json` to add custom keywords:

```json
{
  "keywords": [
    "hack", "exploit", "malware", "virus",
    "password", "credential", "api_key"
  ],
  "regex_patterns": [
    "\\bpassword\\s*[=:]\\s*\\w+",
    "\\bapi[_-]?key\\s*[=:]\\s*[a-zA-Z0-9]+",
    "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b"
  ]
}
```

---

## 🧪 Development & Testing

### Running Tests

```bash
# Run API tests
poetry run python tests/test_keywords_api.py

# Run firewall integration tests
poetry run python tests/firewall_test_cases.py

# Test specific scenarios
poetry run python -c "
from src.core.firewall import LLMFirewall
firewall = LLMFirewall('config/config.json')
result = firewall.check_content('test message')
print(result)
"
```

### Development Mode

```bash
# Start firewall in debug mode
poetry run python run.py --debug

# Start with custom configuration
poetry run python run.py --config config/dev_config.json --port 5002

# View detailed logs
tail -f logs/firewall.log
```

### Code Structure

```
src/
├── api/
│   ├── api.py              # Flask REST API endpoints
│   └── service.py          # Service wrapper with licensing
├── core/
│   ├── firewall.py         # Main firewall orchestrator
│   ├── category_manager.py # Category conflict resolution
│   └── config_manager.py   # Configuration management
├── guards/
│   ├── base_guard.py       # Abstract base class for guards
│   ├── llama_guard.py      # LLaMA Guard implementation
│   └── granite_guard.py    # Granite Guard implementation
├── filters/
│   └── keyword_filter.py   # Keyword/regex filtering
└── licensing/
    ├── license_manager.py  # License validation
    └── generate_license.py # License generation utilities
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Ollama Connection Error**

```bash
# Error: "Connection refused to Ollama"
# Solution: Start Ollama service
ollama serve &

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

#### 2. **Models Not Found**

```bash
# Error: "Model 'llama-guard3' not found"
# Solution: Download required models
ollama pull llama-guard3
ollama pull granite3-guardian:8b

# Check available models
ollama list
```

#### 3. **Poetry Installation Issues**

```bash
# Error: "Poetry command not found"
# Solution: Reinstall Poetry and update PATH
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

#### 4. **Permission Denied Errors**

```bash
# Error: Permission denied on scripts
# Solution: Make scripts executable
chmod +x deployment/scripts/setup_models.sh
chmod +x deployment/scripts/*.sh
```

#### 5. **Port Already in Use**

```bash
# Error: "Port 5001 already in use"
# Solution: Use different port or kill existing process
poetry run python run.py --port 5002

# Or find and kill process using port 5001
lsof -ti:5001 | xargs kill -9
```

#### 6. **Model Download Timeout**

```bash
# Error: Model download hangs or times out
# Solution: Download models manually with retries
for model in llama-guard3 granite3-guardian:8b; do
  echo "Downloading $model..."
  ollama pull $model || ollama pull $model
done
```

### Platform-Specific Issues

#### MacOS Issues

```bash
# M1/M2 Mac: If you get architecture errors
arch -arm64 brew install python@3.12
arch -arm64 poetry install

# If Ollama doesn't start properly
brew install ollama
brew services start ollama
```

#### Linux Issues

```bash
# Ubuntu: If you get SSL certificate errors
sudo apt update && sudo apt install ca-certificates

# CentOS: If Python 3.12 is not available
sudo dnf install python3.11 python3.11-pip
# Then use python3.11 instead of python3.12

# If systemd issues with Ollama
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Performance Optimization

```bash
# For better performance on laptop development:
# 1. Reduce model precision (if needed)
# 2. Limit concurrent requests
# 3. Use smaller models for testing

# Edit config for development:
{
  "guards": [
    {
      "type": "llama_guard",
      "enabled": true,
      "model_name": "llama-guard3",
      "threshold": 0.5
    }
  ]
}
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
poetry run python run.py --debug

# View logs in real-time
tail -f logs/firewall.log

# Test specific components
poetry run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.core.firewall import LLMFirewall
firewall = LLMFirewall('config/config.json')
print('Firewall initialized successfully')
"
```

---

## 📝 Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone <repo-url> LoAFirewall
cd LoAFirewall

# 2. Create development branch
git checkout -b feature/your-feature-name

# 3. Install development dependencies
poetry install --with dev

# 4. Set up pre-commit hooks (if available)
poetry run pre-commit install

# 5. Run initial tests
poetry run python tests/test_keywords_api.py
```

### Making Changes

```bash
# 1. Make your changes to source code

# 2. Test your changes
poetry run python examples/demos/demo.py

# 3. Run unit tests
poetry run python tests/firewall_test_cases.py

# 4. Check code formatting (if tools available)
poetry run black src/
poetry run flake8 src/

# 5. Commit your changes
git add .
git commit -m "feat: your feature description"
```

### Testing Changes

```bash
# Test API changes
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "test your changes"}'

# Test configuration changes
poetry run python run.py --config config/test_config.json

# Load testing (basic)
for i in {1..10}; do
  curl -X POST http://localhost:5001/check \
    -H "Content-Type: application/json" \
    -d '{"text": "test message '$i'"}' &
done
wait
```

---

## 🚀 Production Considerations

### Resource Requirements

```bash
# Minimum requirements for laptop development:
# - 8GB RAM (4GB for models, 4GB for OS)
# - 10GB disk space (models take ~6GB)
# - 2 CPU cores

# Recommended for smooth development:
# - 16GB RAM
# - 20GB disk space  
# - 4+ CPU cores
# - SSD storage
```

### Security Notes

```bash
# For development, the firewall runs with:
# - No license restrictions (dev mode)
# - Debug logging enabled
# - Hot reload for configuration changes

# For production deployment, see:
# docs/vendor/VENDOR_DELIVERY_INSTRUCTIONS.md
```

### Performance Benchmarks

Typical performance on modern laptop (M1 MacBook Pro, 16GB RAM):

```
Content Analysis Performance:
- Keyword filter: ~1ms
- LLaMA Guard: ~200-500ms  
- Granite Guard: ~300-600ms
- Total processing: ~500-1100ms

Memory Usage:
- Base application: ~200MB
- Loaded models: ~4-6GB
- Peak usage: ~6-8GB
```

---

## 📚 Next Steps

### After Installation

1. **Explore the demos**: Run both CLI and web demos to understand capabilities
2. **Read the code**: Check `src/core/firewall.py` for main logic
3. **Test custom content**: Try your own examples with the API
4. **Customize configuration**: Modify keyword lists and guard settings
5. **Review documentation**: Check other docs in `docs/` directory

### For Team Development

1. **Share configuration**: Document any custom settings for your team
2. **Set up CI/CD**: Consider automated testing for your modifications
3. **Document changes**: Update relevant documentation when making changes
4. **Test integration**: Ensure changes work with existing client applications

### For Production Deployment

1. **Review vendor documentation**: `docs/vendor/VENDOR_DELIVERY_INSTRUCTIONS.md`
2. **Build client packages**: Use deployment scripts for secure distribution
3. **Set up monitoring**: Implement health checks and log monitoring
4. **Plan scaling**: Consider resource requirements for production load

---

## 🆘 Getting Help

### Documentation Resources

- **Client Guide**: `docs/client/DEPLOYMENT.md` - For client-side setup
- **Vendor Guide**: `docs/vendor/VENDOR_DELIVERY_INSTRUCTIONS.md` - For secure delivery
- **API Reference**: Check `/health` and `/keywords` endpoints for API details
- **Code Examples**: `examples/` directory contains working examples

### Debug Information

When reporting issues, include:

```bash
# System information
echo "OS: $(uname -a)"
echo "Python: $(python3 --version)"
echo "Poetry: $(poetry --version)"

# Firewall status
curl http://localhost:5001/health

# Recent logs
tail -20 logs/firewall.log

# Model status
ollama list
```

### Common Commands Reference

```bash
# Start firewall
poetry run python run.py

# Run demo
poetry run python examples/demos/demo.py

# Check health
curl http://localhost:5001/health

# View logs
tail -f logs/firewall.log

# Update models
ollama pull llama-guard3

# Reset environment
poetry install --sync
./deployment/scripts/setup_models.sh
```

---

🎉 **You're all set!** The LLM Firewall should now be running on your laptop and ready for development and testing.

For questions or issues, check the troubleshooting section above or review the logs at `logs/firewall.log`.