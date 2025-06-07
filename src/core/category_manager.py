# category_manager.py
from config.config import UNIFIED_CATEGORIES


class CategoryManager:
    """Manages unified categories and conflict resolution"""
    
    def __init__(self, config):
        """
        Initialize category manager with configuration
        
        Args:
            config (dict): Configuration dictionary
        """
        self.unified_categories = config.get("categories", {}).get("unified_categories", UNIFIED_CATEGORIES)
        self.conflict_resolution = config.get("categories", {}).get("conflict_resolution", {})
        
    def get_category_info(self, category_key):
        """
        Get information about a unified category
        
        Args:
            category_key (str): The category key
            
        Returns:
            dict: Category information with code, description, severity
        """
        return self.unified_categories.get(category_key, {
            "code": "UNKNOWN",
            "description": "Unknown category",
            "severity": 1
        })
    
    def get_category_severity(self, category_key):
        """
        Get severity level of a category
        
        Args:
            category_key (str): The category key
            
        Returns:
            int: Severity level (higher = more severe)
        """
        return self.get_category_info(category_key).get("severity", 1)
    
    def resolve_category_conflicts(self, guard_results):
        """
        Resolve conflicts between multiple guard results using custom logic:
        1. If both guards report safe → safe
        2. If llama safe, granite unsafe → prompt injection  
        3. If llama unsafe with reason, granite safe → report llama guard reasoning
        4. If both unsafe → report reason based on llama guard
        
        Args:
            guard_results (list): List of guard result dictionaries
            
        Returns:
            dict: Resolved result with final category and reasoning
        """
        if not guard_results:
            return {
                "final_category": "unknown_unsafe",
                "final_is_safe": False,
                "resolution_method": "no_guards",
                "conflicting_categories": []
            }
        
        # Check if we have exactly two guards (llama and granite)
        if len(guard_results) == 2:
            return self._resolve_two_guard_conflicts(guard_results)
        
        # Fallback to original logic for other cases
        # Extract categories and their sources
        categories = []
        for result in guard_results:
            if result.get("category"):
                categories.append({
                    "category": result["category"],
                    "model": result.get("model", "unknown"),
                    "severity": self.get_category_severity(result["category"])
                })
        
        if not categories:
            return {
                "final_category": "unknown_unsafe",
                "final_is_safe": False,
                "resolution_method": "no_categories",
                "conflicting_categories": []
            }
        
        # Check if all guards agree
        unique_categories = list(set(cat["category"] for cat in categories))
        if len(unique_categories) == 1:
            final_category = unique_categories[0]
            return {
                "final_category": final_category,
                "final_is_safe": final_category == "safe",
                "resolution_method": "consensus",
                "conflicting_categories": []
            }
        
        # Handle conflicts based on strategy
        strategy = self.conflict_resolution.get("strategy", "highest_severity")
        
        if strategy == "highest_severity":
            return self._resolve_by_highest_severity(categories)
        elif strategy == "consensus":
            return self._resolve_by_consensus(categories)
        elif strategy == "first_match":
            return self._resolve_by_first_match(categories)
        else:
            # Default to highest severity
            return self._resolve_by_highest_severity(categories)
    
    def _resolve_two_guard_conflicts(self, guard_results):
        """
        Resolve conflicts between exactly two guards (llama and granite) using custom logic:
        1. If both guards report safe → safe
        2. If llama safe, granite unsafe → prompt injection  
        3. If llama unsafe with reason, granite safe → report llama guard reasoning
        4. If both unsafe → report reason based on llama guard
        
        Args:
            guard_results (list): List of exactly 2 guard result dictionaries
            
        Returns:
            dict: Resolved result with final category and reasoning
        """
        # Identify which guard is which
        llama_result = None
        granite_result = None
        
        for result in guard_results:
            model = result.get("model", "")
            if "guard-1" in model or "llama" in model.lower():
                llama_result = result
            elif "guard-2" in model or "granite" in model.lower():
                granite_result = result
        
        # If we can't identify the guards, fall back to the original logic
        if not llama_result or not granite_result:
            categories = []
            for result in guard_results:
                if result.get("category"):
                    categories.append({
                        "category": result["category"],
                        "model": result.get("model", "unknown"),
                        "severity": self.get_category_severity(result["category"])
                    })
            return self._resolve_by_highest_severity(categories)
        
        llama_category = llama_result.get("category", "unknown")
        granite_category = granite_result.get("category", "unknown")
        llama_safe = llama_category == "safe"
        granite_safe = granite_category == "safe"
        
        # Rule 1: If both guards report safe → safe
        if llama_safe and granite_safe:
            return {
                "final_category": "safe",
                "final_is_safe": True,
                "resolution_method": "both_safe",
                "conflicting_categories": [],
                "llama_category": llama_category,
                "granite_category": granite_category
            }
        
        # Rule 2: If llama safe, granite unsafe → prompt injection
        elif llama_safe and not granite_safe:
            return {
                "final_category": "prompt_injection",
                "final_is_safe": False,
                "resolution_method": "llama_safe_granite_unsafe",
                "conflicting_categories": [llama_category, granite_category],
                "llama_category": llama_category,
                "granite_category": granite_category
            }
        
        # Rule 3: If llama unsafe with reason, granite safe → report llama guard reasoning
        elif not llama_safe and granite_safe:
            return {
                "final_category": llama_category,
                "final_is_safe": False,
                "resolution_method": "llama_unsafe_granite_safe",
                "conflicting_categories": [granite_category],
                "llama_category": llama_category,
                "granite_category": granite_category,
                "selected_model": llama_result.get("model", "llama-guard")
            }
        
        # Rule 4: If both unsafe → report reason based on llama guard
        else:  # both unsafe
            return {
                "final_category": llama_category,
                "final_is_safe": False,
                "resolution_method": "both_unsafe_use_llama",
                "conflicting_categories": [granite_category] if granite_category != llama_category else [],
                "llama_category": llama_category,
                "granite_category": granite_category,
                "selected_model": llama_result.get("model", "llama-guard")
            }

    def _resolve_by_highest_severity(self, categories):
        """Resolve by selecting the category with highest severity"""
        highest_severity = max(cat["severity"] for cat in categories)
        highest_severity_cats = [cat for cat in categories if cat["severity"] == highest_severity]
        
        # If multiple categories have same highest severity, pick the first one
        selected = highest_severity_cats[0]
        
        return {
            "final_category": selected["category"],
            "final_is_safe": selected["category"] == "safe",
            "resolution_method": "highest_severity",
            "conflicting_categories": [cat["category"] for cat in categories if cat["category"] != selected["category"]],
            "selected_model": selected["model"]
        }
    
    def _resolve_by_consensus(self, categories):
        """Resolve by majority vote, fall back to highest severity"""
        from collections import Counter
        
        category_counts = Counter(cat["category"] for cat in categories)
        most_common = category_counts.most_common()
        
        # If there's a clear majority
        if len(most_common) > 1 and most_common[0][1] > most_common[1][1]:
            final_category = most_common[0][0]
            return {
                "final_category": final_category,
                "final_is_safe": final_category == "safe",
                "resolution_method": "consensus",
                "conflicting_categories": [cat[0] for cat in most_common[1:]],
                "vote_counts": dict(category_counts)
            }
        else:
            # No clear majority, fall back to highest severity
            return self._resolve_by_highest_severity(categories)
    
    def _resolve_by_first_match(self, categories):
        """Resolve by using the first non-safe category, or safe if all are safe"""
        # Find first unsafe category
        for cat in categories:
            if cat["category"] != "safe":
                return {
                    "final_category": cat["category"],
                    "final_is_safe": False,
                    "resolution_method": "first_match",
                    "conflicting_categories": [c["category"] for c in categories if c["category"] != cat["category"]],
                    "selected_model": cat["model"]
                }
        
        # All are safe
        return {
            "final_category": "safe",
            "final_is_safe": True,
            "resolution_method": "first_match",
            "conflicting_categories": []
        }
    
    def generate_final_reason(self, resolution_result, guard_results):
        """
        Generate a comprehensive reason for the final decision
        
        Args:
            resolution_result (dict): Result from resolve_category_conflicts
            guard_results (list): Original guard results
            
        Returns:
            str: Final reason string
        """
        final_category = resolution_result["final_category"]
        method = resolution_result["resolution_method"]
        
        category_info = self.get_category_info(final_category)
        
        # Handle new resolution methods
        if method == "both_safe":
            return "Both guards agree: Content is safe"
        elif method == "llama_safe_granite_unsafe":
            return "Prompt injection detected: LlamaGuard safe, GraniteGuard unsafe"
        elif method == "llama_unsafe_granite_safe":
            # Find the original reason from LlamaGuard
            llama_result = None
            for result in guard_results:
                model = result.get("model", "")
                if "guard-1" in model or "llama" in model.lower():
                    llama_result = result
                    break
            if llama_result and llama_result.get("reason"):
                return llama_result["reason"]
            else:
                return f"LlamaGuard detection: {category_info['description']}"
        elif method == "both_unsafe_use_llama":
            # Find the original reason from LlamaGuard  
            llama_result = None
            for result in guard_results:
                model = result.get("model", "")
                if "guard-1" in model or "llama" in model.lower():
                    llama_result = result
                    break
            if llama_result and llama_result.get("reason"):
                return llama_result["reason"]
            else:
                return f"Both guards unsafe - LlamaGuard reasoning: {category_info['description']}"
        elif method == "consensus":
            return f"All guards agree: {category_info['description']}"
        elif method == "highest_severity":
            conflicting = resolution_result.get("conflicting_categories", [])
            if conflicting:
                return f"Multiple detections - selected highest severity: {category_info['description']}"
            else:
                return category_info["description"]
        elif method == "first_match":
            return f"First unsafe detection: {category_info['description']}"
        elif method == "fallback":
            return "Firewall timeout or error - content assumed safe"
        else:
            return category_info["description"]