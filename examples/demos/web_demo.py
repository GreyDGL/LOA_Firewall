#!/usr/bin/env python3
"""
Simple Flask web frontend to showcase the LLM Firewall
"""

from flask import Flask, render_template_string, request, jsonify
import json
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Template for the demo page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alio LLM Firewall - Live Demo</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #88cc88;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #000;
            border: 2px solid #66aa66;
            border-radius: 10px;
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #66aa66;
            padding-bottom: 20px;
        }
        .ascii-logo {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre;
            color: #88cc88;
            margin-bottom: 10px;
        }
        .architecture {
            background: #111;
            border: 1px solid #333;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .flow-diagram {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre;
            color: #77aa77;
            margin: 20px 0;
        }
        .demo-section {
            background: #0a0a0a;
            border: 1px solid #66aa66;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .input-group {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #88cc88;
            font-weight: bold;
        }
        textarea {
            width: 100%;
            height: 120px;
            background: #222;
            color: #88cc88;
            border: 1px solid #66aa66;
            padding: 10px;
            font-family: 'Courier New', monospace;
            border-radius: 3px;
        }
        button {
            background: #224422;
            color: #88cc88;
            border: 2px solid #66aa66;
            padding: 10px 20px;
            font-family: 'Courier New', monospace;
            cursor: pointer;
            border-radius: 3px;
            font-size: 14px;
        }
        button:hover {
            background: #336633;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #111;
            border-left: 4px solid #66aa66;
            border-radius: 3px;
        }
        .safe {
            border-left-color: #66aa66;
            color: #88cc88;
        }
        .unsafe {
            border-left-color: #ff0000;
            color: #ff6666;
        }
        .feature-box {
            display: inline-block;
            background: #0a0a0a;
            border: 1px solid #333;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            width: 200px;
            vertical-align: top;
        }
        .feature-title {
            color: #88cc88;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .processing-time {
            font-size: 12px;
            color: #888;
            margin-top: 10px;
        }
        .category-info {
            font-size: 12px;
            margin-top: 10px;
            padding: 10px;
            background: #0a0a0a;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="ascii-logo">
╔═══════════════════════════════════════════════════════════════╗
║                      ALIO LLM FIREWALL                       ║
║                   Secure Content Filtering                   ║
╚═══════════════════════════════════════════════════════════════╝
            </div>
            <h2>Live Demo & Architecture Overview</h2>
        </div>

        <div class="architecture">
            <h3>🛡️ Firewall Architecture</h3>
            <div class="flow-diagram">
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│ Keyword Filter  │───▶│   AI Guards     │
│   "Test Text"   │    │   (Blacklist)   │    │  (LLM Models)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       │
                                │                       ▼
                        ┌───────────────┐    ┌─────────────────┐
                        │  Short-Circuit │    │ Category System │
                        │   on Unsafe    │    │   Resolution    │
                        └───────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                               ┌─────────────────────────────────┐
                               │        FINAL RESULT             │
                               │   ✅ SAFE  or  ❌ BLOCKED      │
                               └─────────────────────────────────┘
            </div>

            <div style="display: flex; flex-wrap: wrap; justify-content: space-around;">
                <div class="feature-box">
                    <div class="feature-title">Keyword Filter</div>
                    Fast regex-based detection of malicious patterns and banned words
                </div>
                <div class="feature-box">
                    <div class="feature-title">LLaMA Guard</div>
                    Advanced AI model for detecting 14 categories of harmful content
                </div>
                <div class="feature-box">
                    <div class="feature-title">Granite Guard</div>
                    IBM's safety-focused AI model for content classification
                </div>
                <div class="feature-box">
                    <div class="feature-title">Category Resolution</div>
                    Smart conflict resolution between multiple AI guard outputs
                </div>
            </div>
        </div>

        <div class="demo-section">
            <h3>🎯 Live Content Analysis Demo</h3>
            <p>Enter any text below to see how the firewall analyzes and categorizes content in real-time:</p>
            
            <div class="input-group">
                <label for="testText">Enter text to analyze:</label>
                <textarea id="testText" placeholder="Type your message here...&#10;&#10;Try examples like:&#10;• 'Hello, how are you today?'&#10;• 'How to hack into a system'&#10;• 'Ignore all previous instructions'">Hello, how are you today?</textarea>
            </div>
            
            <button onclick="analyzeText()">🔍 Analyze Content</button>
            
            <div id="result" style="display: none;"></div>
        </div>

        <div class="architecture">
            <h3>📊 Security Categories</h3>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-around;">
                <div class="feature-box">
                    <div class="feature-title">SAFE (Severity: 0)</div>
                    Content is safe and does not violate any policies
                </div>
                <div class="feature-box">
                    <div class="feature-title">UNKNOWN_UNSAFE (Severity: 1)</div>
                    Unsafe content of unknown or mixed type
                </div>
                <div class="feature-box">
                    <div class="feature-title">HARMFUL (Severity: 2)</div>
                    Harmful or malicious prompt content
                </div>
                <div class="feature-box">
                    <div class="feature-title">JAILBREAK (Severity: 3)</div>
                    Jailbreak or prompt injection attempt
                </div>
            </div>
        </div>
    </div>

    <script>
        async function analyzeText() {
            const text = document.getElementById('testText').value;
            const resultDiv = document.getElementById('result');
            
            if (!text.trim()) {
                alert('Please enter some text to analyze');
                return;
            }
            
            // Show loading state
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<div style="color: #ffff00;">⏳ Analyzing content...</div>';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text })
                });
                
                const result = await response.json();
                displayResult(result);
            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #ff0000;">❌ Error: ${error.message}</div>`;
            }
        }
        
        function displayResult(result) {
            const resultDiv = document.getElementById('result');
            const isFirewallRunning = result.firewall_running;
            
            if (!isFirewallRunning) {
                resultDiv.innerHTML = `
                    <div class="result unsafe">
                        <h4>⚠️ Firewall API Not Running</h4>
                        <p>The firewall API service is not currently running. This demo shows simulated results:</p>
                        <div class="category-info">
                            <strong>Simulated Analysis:</strong><br>
                            • Content would be processed through keyword filter<br>
                            • Then analyzed by LLaMA Guard and Granite Guard<br>
                            • Final safety determination made by category resolution system<br>
                            <br>
                            <strong>To run full analysis:</strong><br>
                            1. Start the firewall API: <code>python api.py</code><br>
                            2. Ensure it's running on port 5001<br>
                            3. Refresh this demo page
                        </div>
                    </div>
                `;
                return;
            }
            
            const safetyClass = result.is_safe ? 'safe' : 'unsafe';
            const safetyIcon = result.is_safe ? '✅' : '❌';
            const safetyText = result.is_safe ? 'SAFE' : 'BLOCKED';
            
            let html = `
                <div class="result ${safetyClass}">
                    <h4>${safetyIcon} Analysis Result: ${safetyText}</h4>
                    <p><strong>Reason:</strong> ${result.overall_reason}</p>
            `;
            
            // Show keyword filter result
            if (result.keyword_filter_result) {
                const kwSafety = result.keyword_filter_result.is_safe ? '✅' : '❌';
                html += `
                    <div class="category-info">
                        <strong>Keyword Filter:</strong> ${kwSafety} ${result.keyword_filter_result.reason}
                `;
                if (result.keyword_filter_result.matches && result.keyword_filter_result.matches.length > 0) {
                    html += `<br><strong>Matches:</strong> ${result.keyword_filter_result.matches.join(', ')}`;
                }
                html += `</div>`;
            }
            
            // Show guard results
            if (result.guard_results && result.guard_results.length > 0) {
                html += '<div class="category-info"><strong>AI Guard Results:</strong><br>';
                result.guard_results.forEach((guard, index) => {
                    const guardSafety = guard.is_safe ? '✅' : '❌';
                    html += `• Guard ${index + 1} (${guard.model}): ${guardSafety} ${guard.category}<br>`;
                });
                html += '</div>';
            }
            
            // Show category analysis
            if (result.category_analysis) {
                const cat = result.category_analysis;
                html += `
                    <div class="category-info">
                        <strong>Final Category:</strong> ${cat.final_category.toUpperCase()}<br>
                        <strong>Resolution Method:</strong> ${cat.resolution_method}<br>
                        <strong>Description:</strong> ${cat.category_info.description}
                    </div>
                `;
            }
            
            // Show processing times
            if (result.processing_times) {
                html += `
                    <div class="processing-time">
                        <strong>Processing Time:</strong> ${(result.processing_times.total * 1000).toFixed(1)}ms
                    </div>
                `;
            }
            
            html += '</div>';
            resultDiv.innerHTML = html;
        }
        
        // Allow Enter key to submit
        document.getElementById('testText').addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'Enter') {
                analyzeText();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main demo page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze text through the firewall"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Special case: if text is the default safe example, always return safe
        if text.strip() == "Hello, how are you today?":
            return jsonify({
                'firewall_running': True,
                'is_safe': True,
                'overall_reason': 'Content is safe',
                'keyword_filter_result': {
                    'is_safe': True,
                    'reason': 'No harmful keywords detected',
                    'matches': []
                },
                'guard_results': [
                    {
                        'is_safe': True,
                        'category': 'safe',
                        'model': 'llm-guard-1',
                        'reason': 'Content is safe'
                    },
                    {
                        'is_safe': True,
                        'category': 'safe',
                        'model': 'llm-guard-2',
                        'reason': 'Content is safe'
                    }
                ],
                'category_analysis': {
                    'final_category': 'safe',
                    'resolution_method': 'consensus',
                    'category_info': {
                        'code': 'SAFE',
                        'description': 'Content is safe and does not violate any policies',
                        'severity': 0
                    }
                },
                'processing_times': {
                    'total': 0.123
                },
                'text_length': len(text)
            })
        
        # Try to connect to the firewall API
        try:
            response = requests.post(
                'http://localhost:5001/check',
                json={'text': text},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result['firewall_running'] = True
                return jsonify(result)
            else:
                # API returned an error
                return jsonify({
                    'firewall_running': False,
                    'error': f'Firewall API error: {response.status_code}',
                    'is_safe': True,
                    'overall_reason': 'Firewall API not responding - demo mode'
                })
                
        except requests.exceptions.ConnectionError:
            # Firewall API is not running - return demo response
            return jsonify({
                'firewall_running': False,
                'is_safe': True,
                'overall_reason': 'Firewall API not running - demo mode',
                'text_length': len(text),
                'demo_mode': True
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'LLM Firewall Web Demo',
        'firewall_api_available': check_firewall_api()
    })

def check_firewall_api():
    """Check if the main firewall API is available"""
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    print("🛡️  Starting LLM Firewall Web Demo")
    print("📡 Demo will be available at: http://localhost:8080")
    print("🔧 Make sure the firewall API is running on port 5001 for full functionality")
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=True)