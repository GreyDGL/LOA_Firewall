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
        Resolve conflicts between multiple guard results
        
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
        
        if method == "consensus":
            return f"All guards agree: {category_info['description']}"
        elif method == "highest_severity":
            conflicting = resolution_result.get("conflicting_categories", [])
            if conflicting:
                return f"Multiple detections - selected highest severity: {category_info['description']}"
            else:
                return category_info["description"]
        elif method == "first_match":
            return f"First unsafe detection: {category_info['description']}"
        else:
            return category_info["description"]