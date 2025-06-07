# LoA Firewall API Documentation

This document provides comprehensive documentation for the LoA Firewall REST API.

## Base URL

```
http://localhost:5001
```

## Authentication

All API requests require a valid license. The firewall validates the license automatically on startup and periodically during operation.

## Content Types

All requests should use `Content-Type: application/json` for POST/PUT requests.

## Request/Response Format

All responses include a `request_id` for tracking and debugging purposes.

---

## Endpoints

### 1. Content Analysis

**POST /check**

Analyzes content for safety using the firewall's multi-layer detection system.

#### Request Body

```json
{
  "text": "Content to analyze"
}
```

#### Response (Safe Content)

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

#### Response (Unsafe Content)

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
      "status": "flagged",
      "matches_found": 2
    },
    "consensus": false
  },
  "processing_time_ms": 312.45,
  "timestamp": 1673234567.123
}
```

#### Categories

- **safe**: Content is safe
- **harmful_content**: Content contains harmful or malicious material
- **policy_violation**: Content violates usage policies
- **injection_attempt**: Potential prompt injection or manipulation attempt
- **unsafe_content**: Generic unsafe content classification

#### Status Codes

- **200**: Analysis completed successfully
- **400**: Bad request (missing 'text' field, invalid JSON)
- **500**: Internal server error

---

### 2. Health Check

**GET /health**

Returns the current status and configuration of the firewall service.

#### Response

```json
{
  "status": "ok",
  "timestamp": 1673234567.123,
  "version": "1.0.0",
  "guards_available": 2,
  "keyword_filter_enabled": true
}
```

#### Status Codes

- **200**: Service is healthy and operational

---

### 3. Keyword Management

#### Get Keywords

**GET /keywords**

Retrieves the current keyword filtering configuration.

#### Response

```json
{
  "keywords": ["malware", "hack", "exploit"],
  "regex_patterns": ["\\bpassword\\b", "\\bapi[_-]key\\b"],
  "blacklist_file": "config/blacklists/default.json"
}
```

#### Status Codes

- **200**: Keywords retrieved successfully
- **400**: Keyword filter not enabled

#### Update Keywords

**PUT /keywords**

Updates the keyword filtering configuration.

#### Request Body

```json
{
  "keywords": ["malware", "hack", "exploit", "virus"],
  "regex_patterns": ["\\bpassword\\b", "\\bapi[_-]key\\b", "\\d{16}"]
}
```

#### Response

```json
{
  "message": "Keywords updated successfully",
  "keywords_count": 4,
  "regex_patterns_count": 3,
  "saved_to_file": true
}
```

#### Status Codes

- **200**: Keywords updated successfully
- **400**: Bad request (keyword filter not enabled, invalid JSON, invalid regex)

---

### 4. Statistics

**GET /stats**

Returns firewall usage statistics and performance metrics.

#### Response

```json
{
  "status": "ok",
  "requests_processed": 1234,
  "unsafe_content_detected": 45,
  "average_processing_time": 0.234
}
```

#### Status Codes

- **200**: Statistics retrieved successfully

---

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "error": "Error type description",
  "request_id": "unique-request-id", 
  "message": "Detailed error message"
}
```

### Common Error Scenarios

#### 400 Bad Request

```json
{
  "error": "Missing 'text' field",
  "request_id": "abc-123",
  "message": "Request must include a 'text' field"
}
```

#### 403 Forbidden

```json
{
  "error": "License validation failed",
  "request_id": "def-456",
  "message": "License has expired or is invalid"
}
```

#### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "request_id": "ghi-789",
  "message": "An unexpected error occurred during processing"
}
```

---

## Performance Considerations

### Timeouts

- **Default Request Timeout**: 30 seconds
- **Guard Timeout**: 25 seconds per guard
- **Fallback Behavior**: Defaults to "safe" classification on timeout

### Rate Limiting

Rate limiting may be configured depending on deployment settings. Contact your administrator for specific limits.

### Caching

The firewall does not cache results by default. Each request is processed independently for maximum security.

---

## Client Integration Examples

### Python

```python
import requests

def check_content(text, firewall_url="http://localhost:5001"):
    response = requests.post(
        f"{firewall_url}/check",
        json={"text": text},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["is_safe"], result["reason"]
    else:
        raise Exception(f"Firewall error: {response.status_code}")

# Usage
is_safe, reason = check_content("Hello, how are you?")
print(f"Safe: {is_safe}, Reason: {reason}")
```

### JavaScript

```javascript
async function checkContent(text, firewallUrl = "http://localhost:5001") {
    const response = await fetch(`${firewallUrl}/check`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    });
    
    if (response.ok) {
        const result = await response.json();
        return { safe: result.is_safe, reason: result.reason };
    } else {
        throw new Error(`Firewall error: ${response.status}`);
    }
}

// Usage
checkContent("Hello, how are you?")
    .then(result => console.log(`Safe: ${result.safe}, Reason: ${result.reason}`))
    .catch(error => console.error(error));
```

### cURL

```bash
# Basic content check
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Your content here"}' \
  | jq '.is_safe'

# Health check
curl http://localhost:5001/health | jq '.status'

# Update keywords
curl -X PUT http://localhost:5001/keywords \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["test"], "regex_patterns": ["\\btest\\b"]}'
```

---

## Logging and Monitoring

### Request Tracking

Every request is assigned a unique `request_id` that appears in:
- API responses
- Server logs
- Error messages

Use this ID for debugging and support requests.

### Log Levels

- **INFO**: Normal operations, safe content processing
- **WARNING**: Unsafe content detected, fallback operations
- **ERROR**: System errors, configuration issues

### Performance Monitoring

Monitor the `processing_time_ms` field in responses to track performance:
- **< 500ms**: Excellent performance
- **500-1000ms**: Good performance  
- **> 1000ms**: May indicate system load or model issues

---

## Changelog

### Version 1.0

- Initial API release
- Sanitized response format
- Multi-guard analysis
- Comprehensive error handling
- Timeout protection and fallback mechanisms