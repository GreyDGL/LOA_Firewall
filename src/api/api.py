# api.py
from flask import Flask, request, jsonify
import logging
import time
import json
import uuid

from src.core.firewall import LLMFirewall
from src.core.config_manager import ConfigManager


class FirewallAPI:
    """RESTful API for the LLM Firewall"""

    def __init__(self, config_path=None):
        """
        Initialize the API with configuration

        Args:
            config_path (str, optional): Path to custom config file
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()

        # Initialize firewall
        self.firewall = LLMFirewall(self.config)

        # Create Flask app
        self.app = Flask(__name__)
        self.setup_routes()

        # Configure rate limiting if enabled
        self.setup_rate_limiting()

    def setup_routes(self):
        """Configure API routes"""


        @self.app.route('/check', methods=['POST'])
        def check_content():
            """Endpoint to check content safety"""
            request_id = str(uuid.uuid4())
            start_time = time.time()

            # Log request
            logging.info(f"Request {request_id} received at /check")

            # Validate request
            if not request.is_json:
                logging.warning(f"Request {request_id} rejected: not JSON")
                return jsonify({
                    "error": "Request must be JSON",
                    "request_id": request_id
                }), 400

            data = request.json
            text = data.get('text')

            if not text:
                logging.warning(f"Request {request_id} rejected: missing 'text' field")
                return jsonify({
                    "error": "Missing 'text' field",
                    "request_id": request_id
                }), 400

            # Add request metadata
            metadata = {
                "timestamp": time.time(),
                "request_id": request_id,
                "client_ip": request.remote_addr or "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "request_size": len(text),
                "content_type": request.headers.get("Content-Type", "unknown"),
                "referer": request.headers.get("Referer", "unknown")
            }

            # Check content
            try:
                result = self.firewall.check_content(text, request_metadata=metadata)
                processing_time = time.time() - start_time
                
                # Create sanitized response for public API
                sanitized_result = self._create_sanitized_response(result, processing_time, request_id)

                # Log result summary
                logging.info(
                    f"Request {request_id} processed in {processing_time:.3f}s, "
                    f"is_safe: {result['is_safe']}"
                )

                return jsonify(sanitized_result)
            except Exception as e:
                logging.error(f"Error processing request {request_id}: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": str(e)
                }), 500

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Endpoint for health checks"""
            return jsonify({
                "status": "ok",
                "timestamp": time.time(),
                "version": "1.0.0",
                "guards_available": len(self.firewall.guards),
                "keyword_filter_enabled": self.config.get("keyword_filter", {}).get("enabled", False)
            })

        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Endpoint for firewall statistics"""
            # This would be implemented with a proper metrics collector
            return jsonify({
                "status": "ok",
                "requests_processed": 0,  # Placeholder for actual metrics
                "unsafe_content_detected": 0,
                "average_processing_time": 0
            })

        @self.app.route('/keywords', methods=['GET'])
        def get_keywords():
            """Endpoint to retrieve current keyword filtering configuration"""
            try:
                if not self.firewall.keyword_filter:
                    return jsonify({
                        "error": "Keyword filter not enabled",
                        "keywords": [],
                        "regex_patterns": []
                    }), 400
                
                return jsonify({
                    "keywords": self.firewall.keyword_filter.blacklist.get("keywords", []),
                    "regex_patterns": self.firewall.keyword_filter.blacklist.get("regex_patterns", []),
                    "blacklist_file": self.firewall.keyword_filter.blacklist_file
                })
            except Exception as e:
                logging.error(f"Error retrieving keywords: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Failed to retrieve keywords",
                    "message": str(e)
                }), 500

        @self.app.route('/keywords', methods=['PUT'])
        def update_keywords():
            """Endpoint to update keyword filtering configuration"""
            try:
                if not self.firewall.keyword_filter:
                    return jsonify({
                        "error": "Keyword filter not enabled"
                    }), 400

                # Validate request
                if not request.is_json:
                    return jsonify({
                        "error": "Request must be JSON"
                    }), 400

                data = request.json
                keywords = data.get('keywords', [])
                regex_patterns = data.get('regex_patterns', [])

                # Validate inputs
                if not isinstance(keywords, list) or not isinstance(regex_patterns, list):
                    return jsonify({
                        "error": "Keywords and regex_patterns must be lists"
                    }), 400

                # Validate regex patterns
                import re
                for pattern in regex_patterns:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        return jsonify({
                            "error": f"Invalid regex pattern '{pattern}': {str(e)}"
                        }), 400

                # Update the blacklist
                self.firewall.keyword_filter.blacklist = {
                    "keywords": keywords,
                    "regex_patterns": regex_patterns
                }
                
                # Recompile patterns
                self.firewall.keyword_filter._compile_patterns()

                # Save to file if blacklist_file is specified
                blacklist_file = self.firewall.keyword_filter.blacklist_file
                if blacklist_file:
                    import json
                    import os
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(blacklist_file), exist_ok=True)
                    
                    with open(blacklist_file, 'w') as f:
                        json.dump(self.firewall.keyword_filter.blacklist, f, indent=2)

                logging.info(f"Keywords updated: {len(keywords)} keywords, {len(regex_patterns)} patterns")
                
                return jsonify({
                    "message": "Keywords updated successfully",
                    "keywords_count": len(keywords),
                    "regex_patterns_count": len(regex_patterns),
                    "saved_to_file": blacklist_file is not None
                })

            except Exception as e:
                logging.error(f"Error updating keywords: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Failed to update keywords",
                    "message": str(e)
                }), 500

    def _create_sanitized_response(self, result, processing_time, request_id):
        """
        Create a sanitized response that doesn't reveal internal implementation details
        
        Args:
            result (dict): Full firewall result
            processing_time (float): Request processing time
            request_id (str): Request ID
            
        Returns:
            dict: Sanitized response for public API
        """
        # Extract basic information
        is_safe = result.get("is_safe", True)
        overall_reason = result.get("overall_reason", "")
        fallback_used = result.get("fallback_used", False)
        
        # Sanitize category information
        category_analysis = result.get("category_analysis") or {}
        final_category = category_analysis.get("final_category", "safe")
        
        # Map categories to public-friendly names
        category_mapping = {
            "safe": "safe",
            "harmful_prompt": "harmful_content",
            "jailbreak": "policy_violation", 
            "prompt_injection": "injection_attempt",
            "unknown_unsafe": "unsafe_content"
        }
        
        public_category = category_mapping.get(final_category, "unsafe_content")
        
        # Create simplified guard summaries (without revealing model names)
        guard_summaries = []
        for i, guard_result in enumerate(result.get("guard_results", []), 1):
            guard_summary = {
                "guard_id": f"guard_{i}",
                "status": "safe" if guard_result.get("is_safe", True) else "flagged",
                "confidence": "normal"  # Generic confidence level
            }
            
            # Add category for flagged content (but keep it generic)
            if not guard_result.get("is_safe", True):
                raw_category = guard_result.get("category", "unknown")
                guard_summary["detection_type"] = category_mapping.get(raw_category, "unsafe_content")
            
            guard_summaries.append(guard_summary)
        
        # Create simplified keyword filter summary
        keyword_summary = None
        keyword_result = result.get("keyword_filter_result")
        if keyword_result:
            keyword_summary = {
                "enabled": True,
                "status": "safe" if keyword_result.get("is_safe", True) else "flagged",
                "matches_found": len(keyword_result.get("matches", []))
            }
        
        # Build sanitized response
        sanitized_response = {
            "request_id": request_id,
            "is_safe": is_safe,
            "category": public_category,
            "confidence": "high" if not fallback_used else "medium",
            "reason": self._sanitize_reason(overall_reason),
            "analysis": {
                "guards": guard_summaries,
                "keyword_filter": keyword_summary,
                "consensus": len([g for g in guard_summaries if g["status"] == "safe"]) == len(guard_summaries)
            },
            "processing_time_ms": round(processing_time * 1000, 2),
            "timestamp": time.time()
        }
        
        # Add warning if fallback was used
        if fallback_used:
            sanitized_response["warning"] = "Analysis completed with reduced confidence due to system limitations"
        
        return sanitized_response
    
    def _sanitize_reason(self, reason):
        """
        Sanitize the reason string to remove implementation details
        
        Args:
            reason (str): Original reason string
            
        Returns:
            str: Sanitized reason
        """
        # Remove specific model names and technical details
        sanitized = reason.replace("LlamaGuard", "Content analyzer")
        sanitized = sanitized.replace("GraniteGuard", "Safety checker")
        sanitized = sanitized.replace("llama-guard", "analyzer")
        sanitized = sanitized.replace("granite", "checker")
        
        # Simplify technical messages
        if "Both guards agree" in sanitized:
            sanitized = "Content analysis completed successfully"
        elif "Multiple detections" in sanitized:
            sanitized = "Content flagged by safety analysis"
        elif "highest severity" in sanitized:
            sanitized = "Unsafe content detected"
        elif "Prompt injection detected" in sanitized:
            sanitized = "Potential security threat detected"
        elif "defaulting to safe" in sanitized:
            sanitized = "Analysis completed with safety fallback"
        
        return sanitized

    def setup_rate_limiting(self):
        """
        Set up rate limiting if enabled in config
        Note: For production, use a proper rate limiting library
        """
        # Placeholder for rate limiting implementation
        pass

    def run(self):
        """Run the API server"""
        api_config = self.config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 5000)
        debug = api_config.get("debug", False)

        logging.info(f"Starting API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)