# 🛡️ LLM Firewall

Alio content safety filtering service that provides dual-layer protection for AI applications through keyword-based filtering and advanced AI guard models.

## 🚀 Quick Start (1 Minute Setup)

### Option 1: Automatic Setup (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup
```bash
# Build and deploy
docker-compose up -d

# Verify it's working
curl http://localhost:5001/health
```

## ✅ Verify Installation

Test the firewall with a simple request:
```bash
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test message"}'
```

Expected response:
```json
{
  "is_safe": true,
  "overall_reason": "Content appears safe",
  "processing_times": {
    "total": 0.245
  }
}
```

## 📊 Key Features

- **🔍 Dual-Layer Filtering**: Keyword matching + AI-based analysis
- **⚡ Real-time Processing**: Fast API responses (<500ms typical)
- **🔧 Dynamic Updates**: Update filters without restart
- **🛡️ Comprehensive Detection**: Malware, exploits, sensitive data, harmful content
- **📈 Production Ready**: Docker-based deployment with monitoring
- **🔒 Secure**: Containerized with security hardening

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/check` | POST | Analyze content safety |
| `/keywords` | GET | Get current filters |
| `/keywords` | PUT | Update filters |

## 🔧 Configuration

Service runs on **port 5001** by default. Customize via environment variables:

```bash
# Custom port
docker run -e LLM_FIREWALL_PORT=8080 -p 8080:8080 llm-firewall

# Debug mode
docker run -e LLM_FIREWALL_DEBUG=true -e LLM_FIREWALL_LOG_LEVEL=DEBUG llm-firewall
```

## 📚 Documentation

- **[Complete Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[API Reference](INSTALLATION.md#-api-reference)** - Full API documentation  
- **[Configuration Options](INSTALLATION.md#-configuration)** - All environment variables
- **[Troubleshooting](INSTALLATION.md#-troubleshooting)** - Common issues and solutions

## 🎯 Usage Examples

### Python Client
```python
import requests

def check_content(text):
    response = requests.post(
        "http://localhost:5001/check",
        json={"text": text}
    )
    return response.json()["is_safe"]

# Example usage
is_safe = check_content("This is a normal message")
print(f"Content is safe: {is_safe}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function checkContent(text) {
    const response = await axios.post('http://localhost:5001/check', {
        text: text
    });
    return response.data.is_safe;
}

// Example usage
checkContent('This is a normal message')
    .then(isSafe => console.log('Content is safe:', isSafe));
```

## 🔧 Management Commands

```bash
# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Update service
docker-compose down && docker-compose up -d --build
```

## 📈 Performance

- **Typical Response Time**: 200-500ms
- **Throughput**: 100+ requests/second (single instance)
- **Memory Usage**: 2-4GB RAM
- **Startup Time**: 30-60 seconds

For high-volume deployments, see [scaling documentation](INSTALLATION.md#load-balancing).

## 🛠️ System Requirements

- **OS**: Ubuntu 20.04+ (or compatible Linux)
- **Docker**: 20.10+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk**: 10GB free space
- **Network**: Internet access for initial setup

## 🔒 Security Features

- Container-based isolation
- Non-root user execution
- Resource limits and monitoring
- Configurable network access
- Audit logging

For production security recommendations, see the [security section](INSTALLATION.md#-security-considerations).

## 🚨 Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Service won't start | `docker-compose logs` to check errors |
| Port already in use | Change port: `./setup.sh -p 8080` |
| Slow responses | Increase resources: `docker update --memory=8g llm-firewall` |
| Health check fails | Wait 60s for startup, then restart if needed |

For detailed troubleshooting, see [INSTALLATION.md](INSTALLATION.md#-troubleshooting).

## 📞 Support

1. **Check logs**: `docker-compose logs llm-firewall`
2. **Verify health**: `curl http://localhost:5001/health`
3. **Review documentation**: [INSTALLATION.md](INSTALLATION.md)
4. **Check system resources**: `docker stats llm-firewall`

## 📋 Files Included

```
llm-firewall/
├── README.md              # This file - quick start guide
├── INSTALLATION.md        # Complete documentation
├── Dockerfile             # Production Docker image
├── docker-compose.yml     # Easy deployment configuration
├── setup.sh               # Automated setup script
├── run.py                 # Application entry point
├── pyproject.toml         # Python dependencies
└── [your firewall code]   # LLM Firewall implementation
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  LLM Firewall    │───▶│   Ollama AI     │
│                 │    │  (Port 5001)     │    │  (Port 11434)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Keyword Filters  │
                       │ + Regex Patterns │
                       └──────────────────┘
```

---

**🎉 Ready to deploy? Run `./setup.sh` to get started in under a minute!**

For questions or issues, refer to [INSTALLATION.md](INSTALLATION.md) for comprehensive documentation.