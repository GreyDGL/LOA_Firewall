# api.py
from flask import Flask, request, jsonify
import logging
import time
import json
import uuid
import sys
import os

from src.core.firewall import LLMFirewall
from src.core.config_manager import ConfigManager

from langfuse import Langfuse
from langfuse import observe

# Add src to path for PII masking
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from musk import PIIMasker
    PII_MASKER_AVAILABLE = True
except ImportError:
    PII_MASKER_AVAILABLE = False

langfuse = Langfuse(
  secret_key="sk-lf-955c3a32-bfbe-4499-97b8-2187dc2af3a4",
  public_key="pk-lf-bbdb5145-9398-47cb-a207-78dc0b9001ca",
  host="https://cloud.langfuse.com"
)




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

        # Initialize PII masker if available
        self.pii_masker = None
        self.pii_requests_processed = 0
        self.pii_items_masked = 0
        if PII_MASKER_AVAILABLE:
            try:
                self.pii_masker = PIIMasker(model_name="llama3.2")
                logging.info("PII masker initialized successfully")
            except Exception as e:
                logging.warning(f"Failed to initialize PII masker: {e}")

        # Create Flask app
        self.app = Flask(__name__)
        self.setup_routes()

        # Configure rate limiting if enabled
        self.setup_rate_limiting()

    @observe(name="content-check", as_type="span")
    def _check_content_with_metadata(self, request_data, metadata):
        """
        Check content safety with langfuse observability
        
        Args:
            request_data (dict): The full request JSON data
            metadata (dict): Request metadata
            
        Returns:
            dict: Firewall check result
        """
        text = request_data.get("text")
        result = self.firewall.check_content(text, request_metadata=metadata)
        langfuse.update_current_trace(
            metadata=result
        )
        return result

    def setup_routes(self):
        """Configure API routes"""

        @self.app.route("/check", methods=["POST"])
        def check_content():
            """Endpoint to check content safety"""
            request_id = str(uuid.uuid4())
            start_time = time.time()

            # Log request
            logging.info(f"Request {request_id} received at /check")

            # Validate request
            if not request.is_json:
                logging.warning(f"Request {request_id} rejected: not JSON")
                return jsonify({"error": "Request must be JSON", "request_id": request_id}), 400

            data = request.json
            text = data.get("text")

            if not text:
                logging.warning(f"Request {request_id} rejected: missing 'text' field")
                return jsonify({"error": "Missing 'text' field", "request_id": request_id}), 400

            # Add request metadata
            metadata = {
                "timestamp": time.time(),
                "request_id": request_id,
                "client_ip": request.remote_addr or "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "request_size": len(text),
                "content_type": request.headers.get("Content-Type", "unknown"),
                "referer": request.headers.get("Referer", "unknown"),
            }

            # Check content with langfuse observability
            try:
                result = self._check_content_with_metadata(data, metadata)
                processing_time = time.time() - start_time

                # Create sanitized response for public API
                sanitized_result = self._create_sanitized_response(
                    result, processing_time, request_id
                )

                # Log result summary
                logging.info(
                    f"Request {request_id} processed in {processing_time:.3f}s, "
                    f"is_safe: {result['is_safe']}"
                )

                return jsonify(sanitized_result)
            except Exception as e:
                logging.error(f"Error processing request {request_id}: {str(e)}", exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Internal server error",
                            "request_id": request_id,
                            "message": str(e),
                        }
                    ),
                    500,
                )

        @self.app.route("/mask-pii", methods=["POST"])
        def mask_pii():
            """Endpoint to mask PII in text"""
            request_id = str(uuid.uuid4())
            start_time = time.time()

            # Log request
            logging.info(f"Request {request_id} received at /mask-pii")

            # Validate request
            if not request.is_json:
                logging.warning(f"Request {request_id} rejected: not JSON")
                return jsonify({"error": "Request must be JSON", "request_id": request_id}), 400

            data = request.json
            text = data.get("text")
            use_ai = data.get("use_ai", True)

            if not text:
                logging.warning(f"Request {request_id} rejected: missing 'text' field")
                return jsonify({"error": "Missing 'text' field", "request_id": request_id}), 400

            # Check if PII masker is available
            if not self.pii_masker:
                return jsonify({
                    "error": "PII masking service not available",
                    "request_id": request_id,
                    "message": "PII masker not initialized"
                }), 503

            # Add request metadata
            metadata = {
                "timestamp": time.time(),
                "request_id": request_id,
                "client_ip": request.remote_addr or "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "request_size": len(text),
                "use_ai": use_ai,
            }

            try:
                # Perform PII masking
                masking_details = self.pii_masker.mask_text_with_details(text, use_ai=use_ai)
                processing_time = time.time() - start_time

                # Create sanitized response
                sanitized_result = self._create_pii_sanitized_response(
                    masking_details, processing_time, request_id, metadata
                )

                # Update statistics
                self.pii_requests_processed += 1
                total_pii_masked = (masking_details.get('regex_masked_count', 0) + 
                                   masking_details.get('ai_masked_count', 0))
                self.pii_items_masked += total_pii_masked

                # Log result summary
                has_pii = masking_details['masked_text'] != masking_details['original_text']
                logging.info(
                    f"Request {request_id} processed in {processing_time:.3f}s, "
                    f"PII detected: {has_pii}, items masked: {total_pii_masked}"
                )

                return jsonify(sanitized_result)

            except Exception as e:
                logging.error(f"Error processing PII masking request {request_id}: {str(e)}", exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Internal server error",
                            "request_id": request_id,
                            "message": str(e),
                        }
                    ),
                    500,
                )

        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Endpoint for health checks"""
            # Check if PII masker is ready
            pii_masker_status = "disabled"
            if self.pii_masker:
                try:
                    # Quick test to see if the masker is functional
                    ollama_available = self.pii_masker.ensure_model_ready()
                    pii_masker_status = "ready" if ollama_available else "limited"
                except:
                    pii_masker_status = "error"
            
            return jsonify(
                {
                    "status": "ok",
                    "timestamp": time.time(),
                    "version": "1.0.0",
                    "services": {
                        "firewall": {
                            "guards_available": len(self.firewall.guards),
                            "keyword_filter_enabled": self.config.get("keyword_filter", {}).get(
                                "enabled", False
                            ),
                        },
                        "pii_masking": {
                            "status": pii_masker_status,
                            "available": self.pii_masker is not None,
                            "ai_powered": pii_masker_status in ["ready", "limited"],
                        }
                    }
                }
            )

        @self.app.route("/stats", methods=["GET"])
        def get_stats():
            """Endpoint for firewall and PII masking statistics"""
            return jsonify(
                {
                    "status": "ok",
                    "firewall": {
                        "total_tokens_processed": self.firewall.get_token_count(),
                        "requests_processed": 0,  # Placeholder for actual metrics
                        "unsafe_content_detected": 0,
                        "average_processing_time": 0,
                    },
                    "pii_masking": {
                        "requests_processed": self.pii_requests_processed,
                        "total_pii_items_masked": self.pii_items_masked,
                        "service_available": self.pii_masker is not None,
                        "average_pii_per_request": (
                            round(self.pii_items_masked / self.pii_requests_processed, 2) 
                            if self.pii_requests_processed > 0 else 0
                        ),
                    }
                }
            )

        @self.app.route("/keywords", methods=["GET"])
        def get_keywords():
            """Endpoint to retrieve current keyword filtering configuration"""
            try:
                if not self.firewall.keyword_filter:
                    return (
                        jsonify(
                            {
                                "error": "Keyword filter not enabled",
                                "keywords": [],
                                "regex_patterns": [],
                            }
                        ),
                        400,
                    )

                return jsonify(
                    {
                        "keywords": self.firewall.keyword_filter.blacklist.get("keywords", []),
                        "regex_patterns": self.firewall.keyword_filter.blacklist.get(
                            "regex_patterns", []
                        ),
                        "blacklist_file": self.firewall.keyword_filter.blacklist_file,
                    }
                )
            except Exception as e:
                logging.error(f"Error retrieving keywords: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to retrieve keywords", "message": str(e)}), 500

        @self.app.route("/keywords", methods=["PUT"])
        def update_keywords():
            """Endpoint to update keyword filtering configuration"""
            try:
                if not self.firewall.keyword_filter:
                    return jsonify({"error": "Keyword filter not enabled"}), 400

                # Validate request
                if not request.is_json:
                    return jsonify({"error": "Request must be JSON"}), 400

                data = request.json
                keywords = data.get("keywords", [])
                regex_patterns = data.get("regex_patterns", [])

                # Validate inputs
                if not isinstance(keywords, list) or not isinstance(regex_patterns, list):
                    return jsonify({"error": "Keywords and regex_patterns must be lists"}), 400

                # Validate regex patterns
                import re

                for pattern in regex_patterns:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        return (
                            jsonify({"error": f"Invalid regex pattern '{pattern}': {str(e)}"}),
                            400,
                        )

                # Update the blacklist
                self.firewall.keyword_filter.blacklist = {
                    "keywords": keywords,
                    "regex_patterns": regex_patterns,
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

                    with open(blacklist_file, "w") as f:
                        json.dump(self.firewall.keyword_filter.blacklist, f, indent=2)

                logging.info(
                    f"Keywords updated: {len(keywords)} keywords, {len(regex_patterns)} patterns"
                )

                return jsonify(
                    {
                        "message": "Keywords updated successfully",
                        "keywords_count": len(keywords),
                        "regex_patterns_count": len(regex_patterns),
                        "saved_to_file": blacklist_file is not None,
                    }
                )

            except Exception as e:
                logging.error(f"Error updating keywords: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to update keywords", "message": str(e)}), 500

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
            "unknown_unsafe": "unsafe_content",
        }

        public_category = category_mapping.get(final_category, "unsafe_content")

        # Create simplified guard summaries (without revealing model names)
        guard_summaries = []
        for i, guard_result in enumerate(result.get("guard_results", []), 1):
            guard_summary = {
                "guard_id": f"guard_{i}",
                "status": "safe" if guard_result.get("is_safe", True) else "flagged",
                "confidence": "normal",  # Generic confidence level
            }

            # Add category for flagged content (but keep it generic)
            if not guard_result.get("is_safe", True):
                raw_category = guard_result.get("category", "unknown")
                guard_summary["detection_type"] = category_mapping.get(
                    raw_category, "unsafe_content"
                )

            guard_summaries.append(guard_summary)

        # Create simplified keyword filter summary
        keyword_summary = None
        keyword_result = result.get("keyword_filter_result")
        if keyword_result:
            keyword_summary = {
                "enabled": True,
                "status": "safe" if keyword_result.get("is_safe", True) else "flagged",
                "matches_found": len(keyword_result.get("matches", [])),
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
                "consensus": len([g for g in guard_summaries if g["status"] == "safe"])
                == len(guard_summaries),
            },
            "processing_time_ms": round(processing_time * 1000, 2),
            "tokens_processed": result.get("tokens_processed", 0),
            "total_tokens_processed": result.get("total_tokens_processed", 0),
            "timestamp": time.time(),
        }

        # Add warning if fallback was used
        if fallback_used:
            sanitized_response["warning"] = (
                "Analysis completed with reduced confidence due to system limitations"
            )

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

    def _create_pii_sanitized_response(self, masking_details, processing_time, request_id, metadata):
        """
        Create a sanitized response for PII masking that follows the same pattern as firewall responses

        Args:
            masking_details (dict): Full PII masking result
            processing_time (float): Request processing time
            request_id (str): Request ID
            metadata (dict): Request metadata

        Returns:
            dict: Sanitized response for public API
        """
        original_text = masking_details.get('original_text', '')
        masked_text = masking_details.get('masked_text', '')
        has_pii = original_text != masked_text

        # Create sanitized response similar to firewall API structure
        sanitized_response = {
            "request_id": request_id,
            "pii_detected": has_pii,
            "masked_text": masked_text,
            "method_used": masking_details.get('method_used', 'unknown'),
            "confidence": "high" if masking_details.get('ai_masked_count', 0) > 0 else "medium",
            "analysis": {
                "total_pii_found": (masking_details.get('regex_masked_count', 0) + 
                                   masking_details.get('ai_masked_count', 0)),
                "regex_detections": masking_details.get('regex_masked_count', 0),
                "ai_detections": masking_details.get('ai_masked_count', 0),
                "ai_extracted_items": len(masking_details.get('ai_extracted_pii', [])),
            },
            "processing_time_ms": round(processing_time * 1000, 2),
            "text_length": len(original_text),
            "timestamp": metadata.get('timestamp', time.time()),
        }

        # Add AI analysis details if available
        if masking_details.get('ai_extracted_pii'):
            # Don't expose the actual PII values for security
            sanitized_response["analysis"]["pii_categories_found"] = len(
                set(item.replace('**', '').replace('*', '') for item in masking_details['ai_extracted_pii'])
            )

        # Add status message
        if has_pii:
            sanitized_response["status"] = "pii_masked"
            sanitized_response["message"] = f"Successfully masked {sanitized_response['analysis']['total_pii_found']} PII item(s)"
        else:
            sanitized_response["status"] = "no_pii_detected"
            sanitized_response["message"] = "No personal information detected in the text"

        return sanitized_response

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


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the API
    api = FirewallAPI()
    
    # Override port to 5001 for consistency
    api.config["api"] = api.config.get("api", {})
    api.config["api"]["port"] = 5001
    
    print("🛡️  Starting LLM Firewall API with PII Masking")
    print("📡 API will be available at: http://localhost:5001")
    print("🔧 Endpoints:")
    print("   POST /check - Content safety analysis")
    print("   POST /mask-pii - PII masking")
    print("   GET  /health - Health check")
    print("   GET  /stats - Usage statistics")
    print()
    
    api.run()
