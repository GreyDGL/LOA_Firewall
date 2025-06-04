# firewall.py
import logging
import importlib
import time
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

    def check_content(self, text):
        """
        Run the content through the full filtering pipeline

        Args:
            text (str): Text to check

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
            "processing_times": {}
        }

        # Step 1: Check keyword filter if initialized and enabled
        if self.keyword_filter and self.config.get("keyword_filter", {}).get("enabled", True):
            kw_start = time.time()
            try:
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
                result["keyword_filter_result"] = {
                    "is_safe": False,
                    "reason": f"Error in keyword filter: {str(e)}",
                    "matches": []
                }
                # Continue to LLM guards

            result["processing_times"]["keyword_filter"] = time.time() - kw_start

        # Step 2: Run through all enabled LLM guards
        for i, guard in enumerate(self.guards):
            guard_start = time.time()
            try:
                guard_result = guard.check_content(text)
                result["guard_results"].append(guard_result)

                # Note: We'll determine final safety after category resolution
            except Exception as e:
                logging.error(f"Error in guard {i}: {str(e)}", exc_info=True)
                # Fail closed on error
                guard_result = {
                    "is_safe": False,
                    "reason": "Error during content analysis",
                    "model": f"llm-guard-{i+1}",
                    "raw_response": "Analysis failed"
                }
                result["guard_results"].append(guard_result)
                result["is_safe"] = False
                if not result["overall_reason"]:
                    result["overall_reason"] = "Error during content analysis"

            result["processing_times"][f"guard_{i}"] = time.time() - guard_start

        # Step 3: Resolve category conflicts and determine final result
        if result["guard_results"]:
            category_start = time.time()
            
            # Resolve category conflicts
            resolution_result = self.category_manager.resolve_category_conflicts(result["guard_results"])
            
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