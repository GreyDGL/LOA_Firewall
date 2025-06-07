# firewall.py
import logging
import importlib
import time
import hashlib
import json
from datetime import datetime
from src.core.category_manager import CategoryManager


class LLMFirewall:
    """Main firewall orchestrator that manages the filtering pipeline"""

    def __init__(self, config):
        """
        Initialize the firewall with configuration

        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.guards = []
        self.keyword_filter = None
        
        # Initialize category manager
        self.category_manager = CategoryManager(config)

        # Keep track of guard registration
        self.guard_registry = {
            "llama_guard": "src.guards.llama_guard.LlamaGuard",
            "granite_guard": "src.guards.granite_guard.GraniteGuard"
            # Additional guards can be registered here
        }

        # Initialize components
        self.initialize()

    def register_guard(self, guard_type, class_path):
        """
        Register a new guard type

        Args:
            guard_type (str): Type identifier for the guard
            class_path (str): Import path to the guard class
        """
        self.guard_registry[guard_type] = class_path
        logging.info(f"Registered guard type: {guard_type} -> {class_path}")

    def initialize(self):
        """Initialize keyword filter and all configured LLM guards"""
        logging.info("Initializing LLM Firewall")

        # Initialize keyword filter if enabled
        if self.config.get("keyword_filter", {}).get("enabled", True):
            try:
                from src.filters.keyword_filter import KeywordFilter
                blacklist_file = self.config.get("keyword_filter", {}).get("blacklist_file")
                self.keyword_filter = KeywordFilter(blacklist_file)
                logging.info("Keyword filter initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize keyword filter: {str(e)}", exc_info=True)
                # Continue without keyword filter

        # Initialize all enabled guards
        guard_configs = self.config.get("guards", [])
        for guard_config in guard_configs:
            if guard_config.get("enabled", False):
                guard_type = guard_config.get("type")
                if guard_type not in self.guard_registry:
                    logging.warning(f"Unknown guard type: {guard_type}")
                    continue

                try:
                    # Dynamically import and instantiate the guard
                    class_path = self.guard_registry[guard_type]
                    module_path, class_name = class_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    guard_class = getattr(module, class_name)

                    # Create guard instance with config
                    guard = guard_class(**{k: v for k, v in guard_config.items()
                                           if k not in ['type', 'enabled']})

                    # Initialize guard
                    if guard.initialize():
                        self.guards.append(guard)
                        logging.info(f"Guard {guard_type} initialized successfully")
                    else:
                        logging.error(f"Guard {guard_type} failed to initialize")
                except Exception as e:
                    logging.error(f"Failed to initialize guard {guard_type}: {str(e)}", exc_info=True)

        # Log initialization summary
        logging.info(f"Firewall initialized with {len(self.guards)} guards and " +
                     ("keyword filter enabled" if self.keyword_filter else "keyword filter disabled"))

    def check_content(self, text, timeout=30, request_metadata=None):
        """
        Run the content through the full filtering pipeline with fallback to safe

        Args:
            text (str): Text to check
            timeout (int): Maximum time in seconds before fallback (default: 30)
            request_metadata (dict, optional): Request metadata (IP, user agent, etc.)

        Returns:
            dict: Full result with details from each filter/guard
        """
        start_time = time.time()

        result = {
            "is_safe": True,
            "keyword_filter_result": None,
            "guard_results": [],
            "category_analysis": None,
            "overall_reason": "",
            "processing_times": {},
            "fallback_used": False
        }

        try:
            final_result = self._check_content_with_timeout(text, timeout, start_time, result)
            
            # Log detailed analysis
            LLMFirewall._log_detailed_analysis(text, final_result, request_metadata)
            
            return final_result
        except Exception as e:
            logging.error(f"Critical error in firewall check_content: {str(e)}", exc_info=True)
            # Fallback to safe
            fallback_result = LLMFirewall._create_safe_fallback_result(start_time, "Critical firewall error - defaulting to safe")
            
            # Log fallback
            LLMFirewall._log_detailed_analysis(text, fallback_result, request_metadata)
            
            return fallback_result

    def _check_content_with_timeout(self, text, timeout, start_time, result):
        """
        Internal method to run content checking with timeout protection
        """
        # Check for timeout before each major step
        if time.time() - start_time > timeout:
            return LLMFirewall._create_safe_fallback_result(start_time, "Timeout during firewall processing - defaulting to safe")

        # Step 1: Check keyword filter if initialized and enabled
        if self.keyword_filter and self.config.get("keyword_filter", {}).get("enabled", True):
            kw_start = time.time()
            try:
                # Check timeout before keyword filter
                if time.time() - start_time > timeout:
                    return LLMFirewall._create_safe_fallback_result(start_time, "Timeout before keyword filter - defaulting to safe")
                
                kw_result = self.keyword_filter.check_content(text)
                result["keyword_filter_result"] = kw_result

                # If keyword filter flags content as unsafe, we can short-circuit
                if not kw_result["is_safe"] and self.config.get("keyword_filter", {}).get("short_circuit", True):
                    result["is_safe"] = False
                    result["overall_reason"] = f"Keyword filter: {kw_result['reason']}"
                    result["processing_times"]["keyword_filter"] = time.time() - kw_start
                    result["processing_times"]["total"] = time.time() - start_time
                    return result
            except Exception as e:
                logging.error(f"Error in keyword filter: {str(e)}", exc_info=True)
                # On keyword filter error, continue with guards but don't fail
                result["keyword_filter_result"] = {
                    "is_safe": True,  # Changed from False to True for fail-open
                    "reason": f"Keyword filter error - defaulting to safe: {str(e)}",
                    "matches": []
                }

            result["processing_times"]["keyword_filter"] = time.time() - kw_start

        # Step 2: Run through all enabled LLM guards
        for i, guard in enumerate(self.guards):
            # Check timeout before each guard
            if time.time() - start_time > timeout:
                return LLMFirewall._create_safe_fallback_result(start_time, f"Timeout before guard {i+1} - defaulting to safe")
            
            guard_start = time.time()
            try:
                guard_result = guard.check_content(text)
                result["guard_results"].append(guard_result)

                # Note: We'll determine final safety after category resolution
            except Exception as e:
                logging.error(f"Error in guard {i}: {str(e)}", exc_info=True)
                # Fail open on error - assume safe instead of unsafe
                guard_result = {
                    "is_safe": True,  # Changed from False to True for fail-open
                    "category": "safe",
                    "reason": f"Guard error - defaulting to safe: {str(e)}",
                    "model": f"llm-guard-{i+1}",
                    "raw_response": "Analysis failed"
                }
                result["guard_results"].append(guard_result)

            result["processing_times"][f"guard_{i}"] = time.time() - guard_start

        # Step 3: Resolve category conflicts and determine final result
        if result["guard_results"]:
            # Check timeout before category resolution
            if time.time() - start_time > timeout:
                return LLMFirewall._create_safe_fallback_result(start_time, "Timeout before category resolution - defaulting to safe")
            
            category_start = time.time()
            
            try:
                # Resolve category conflicts
                resolution_result = self.category_manager.resolve_category_conflicts(result["guard_results"])
            except Exception as e:
                logging.error(f"Error during category resolution: {str(e)}", exc_info=True)
                return LLMFirewall._create_safe_fallback_result(start_time, f"Category resolution error - defaulting to safe: {str(e)}")
            
            # Generate comprehensive category analysis
            result["category_analysis"] = {
                "final_category": resolution_result["final_category"],
                "resolution_method": resolution_result["resolution_method"],
                "conflicting_categories": resolution_result.get("conflicting_categories", []),
                "category_info": self.category_manager.get_category_info(resolution_result["final_category"])
            }
            
            # Update overall safety based on final category
            final_is_safe = resolution_result["final_is_safe"]
            
            # Keyword filter can override if it found unsafe content and short_circuit is enabled
            if result["keyword_filter_result"] and not result["keyword_filter_result"]["is_safe"]:
                if self.config.get("keyword_filter", {}).get("short_circuit", True):
                    result["is_safe"] = False
                    result["overall_reason"] = f"Keyword filter: {result['keyword_filter_result']['reason']}"
                else:
                    # Combine keyword and guard results
                    result["is_safe"] = final_is_safe and result["keyword_filter_result"]["is_safe"]
                    if not result["is_safe"]:
                        if not result["keyword_filter_result"]["is_safe"] and not final_is_safe:
                            result["overall_reason"] = "Both keyword filter and AI guards detected unsafe content"
                        elif not result["keyword_filter_result"]["is_safe"]:
                            result["overall_reason"] = f"Keyword filter: {result['keyword_filter_result']['reason']}"
                        else:
                            result["overall_reason"] = self.category_manager.generate_final_reason(resolution_result, result["guard_results"])
                    else:
                        result["overall_reason"] = "All checks passed"
            else:
                # Only guard results determine safety
                result["is_safe"] = final_is_safe
                if result["is_safe"]:
                    result["overall_reason"] = "All checks passed"
                else:
                    result["overall_reason"] = self.category_manager.generate_final_reason(resolution_result, result["guard_results"])
            
            result["processing_times"]["category_resolution"] = time.time() - category_start
        else:
            # No guards ran, rely on keyword filter result
            if result["keyword_filter_result"]:
                result["is_safe"] = result["keyword_filter_result"]["is_safe"]
                result["overall_reason"] = result["keyword_filter_result"]["reason"]
            else:
                # No filters ran at all
                result["is_safe"] = True
                result["overall_reason"] = "No filters enabled - content passed by default"

        # Set total processing time
        result["processing_times"]["total"] = time.time() - start_time

        return result

    @staticmethod
    def _create_safe_fallback_result(start_time, reason):
        """
        Create a safe fallback result when the firewall fails or times out
        
        Args:
            start_time (float): Start time of the operation
            reason (str): Reason for the fallback
            
        Returns:
            dict: Safe fallback result
        """
        return {
            "is_safe": True,
            "keyword_filter_result": None,
            "guard_results": [],
            "category_analysis": {
                "final_category": "safe",
                "resolution_method": "fallback",
                "conflicting_categories": [],
                "category_info": {
                    "code": "SAFE",
                    "description": "Content is safe (fallback)",
                    "severity": 0
                }
            },
            "overall_reason": reason,
            "processing_times": {
                "total": time.time() - start_time
            },
            "fallback_used": True
        }

    @staticmethod
    def _log_detailed_analysis(text, result, request_metadata=None):
        """
        Log detailed analysis information for monitoring and debugging
        
        Args:
            text (str): Original input text
            result (dict): Firewall analysis result
            request_metadata (dict): Request metadata (IP, user agent, etc.)
        """
        try:
            # Generate text hash for privacy
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
            
            # Extract key information
            is_safe = result.get("is_safe", True)
            category_analysis = result.get("category_analysis") or {}
            final_category = category_analysis.get("final_category", "unknown")
            resolution_method = category_analysis.get("resolution_method", "unknown")
            overall_reason = result.get("overall_reason", "")
            processing_time = result.get("processing_times", {}).get("total", 0)
            fallback_used = result.get("fallback_used", False)
            
            # Extract matched keywords/rules
            matched_keywords = []
            matched_rules = []
            
            keyword_result = result.get("keyword_filter_result")
            if keyword_result and not keyword_result.get("is_safe", True):
                matches = keyword_result.get("matches", [])
                for match in matches:
                    if match.get("type") == "keyword":
                        matched_keywords.append(match.get("pattern", ""))
                    elif match.get("type") == "regex":
                        matched_rules.append(match.get("pattern", ""))
            
            # Extract guard information
            guard_results_summary = []
            for guard_result in result.get("guard_results", []):
                guard_info = {
                    "model": guard_result.get("model", "unknown"),
                    "is_safe": guard_result.get("is_safe", True),
                    "category": guard_result.get("category", "unknown"),
                    "raw_category": guard_result.get("raw_category", "unknown")
                }
                guard_results_summary.append(guard_info)
            
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "text_hash": text_hash,
                "text_length": len(text),
                "is_safe": is_safe,
                "safety_status": "SAFE" if is_safe else "UNSAFE",
                "unsafe_type": final_category if not is_safe else None,
                "matched_keywords": matched_keywords,
                "matched_rules": matched_rules,
                "resolution_method": resolution_method,
                "overall_reason": overall_reason,
                "processing_time_ms": round(processing_time * 1000, 2),
                "fallback_used": fallback_used,
                "guard_results": guard_results_summary
            }
            
            # Add request metadata if provided
            if request_metadata:
                log_entry.update({
                    "request_ip": request_metadata.get("client_ip", "unknown"),
                    "user_agent": request_metadata.get("user_agent", "unknown"),
                    "request_id": request_metadata.get("request_id", "unknown")
                })
            
            # Create comprehensive log message
            status = "SAFE" if is_safe else "UNSAFE"
            summary_parts = [
                f"STATUS={status}",
                f"HASH={text_hash}",
                f"TIME={log_entry['processing_time_ms']}ms"
            ]
            
            if not is_safe:
                summary_parts.append(f"TYPE={final_category}")
                if matched_keywords:
                    summary_parts.append(f"KEYWORDS={','.join(matched_keywords[:3])}")
                if matched_rules:
                    summary_parts.append(f"RULES={len(matched_rules)}")
            
            if request_metadata:
                summary_parts.append(f"IP={request_metadata.get('client_ip', 'unknown')}")
            
            if fallback_used:
                summary_parts.append("FALLBACK=true")
            
            summary = " | ".join(summary_parts)
            
            # Get dedicated firewall analysis logger
            firewall_logger = logging.getLogger('firewall_analysis')
            
            # Log with different levels based on result
            if fallback_used:
                firewall_logger.warning(f"FIREWALL_FALLBACK | {summary}")
                logging.warning(f"Firewall fallback triggered: {text_hash}")
            elif not is_safe:
                firewall_logger.warning(f"FIREWALL_UNSAFE | {summary}")
                logging.info(f"Unsafe content detected: {text_hash} ({final_category})")
            else:
                firewall_logger.info(f"FIREWALL_SAFE | {summary}")
            
            # Also log detailed JSON for analysis (only in debug mode)
            if firewall_logger.isEnabledFor(logging.DEBUG):
                firewall_logger.debug(f"FIREWALL_DETAILED | {json.dumps(log_entry, indent=None)}")
                
        except Exception as e:
            logging.error(f"Error in detailed logging: {str(e)}", exc_info=True)

    def reload_configuration(self, new_config):
        """
        Reload the firewall with a new configuration

        Args:
            new_config (dict): New configuration

        Returns:
            bool: Success status
        """
        try:
            self.config = new_config
            # Clear current guards
            self.guards = []
            self.keyword_filter = None
            # Reinitialize with new config
            self.initialize()
            return True
        except Exception as e:
            logging.error(f"Failed to reload configuration: {str(e)}", exc_info=True)
            return False