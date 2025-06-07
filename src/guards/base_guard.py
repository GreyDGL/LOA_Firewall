from abc import ABC, abstractmethod


class BaseGuard(ABC):
    """Abstract base class for LLM guards"""

    def __init__(self, **kwargs):
        """Initialize base guard with common parameters"""
        self.category_mapping = kwargs.get('category_mapping', {})
        
    @abstractmethod
    def initialize(self):
        """Initialize the guard model"""
        pass

    @abstractmethod
    def check_content(self, text):
        """
        Check if the content is safe

        Args:
            text (str): The text to check

        Returns:
            dict: Result with unified category format:
            {
                'is_safe': bool,
                'category': str,  # unified category key
                'raw_category': str,  # original model category
                'reason': str,
                'model': str,
                'raw_response': str
            }
        """
        pass
    
    def map_to_unified_category(self, raw_category):
        """
        Map model-specific category to unified category
        
        Args:
            raw_category (str): The raw category from the model
            
        Returns:
            str: Unified category key
        """
        # Special case: if raw_category is "safe" and not in mapping, default to "safe"
        if raw_category == "safe" and raw_category not in self.category_mapping:
            return "safe"
        
        return self.category_mapping.get(raw_category, "unknown_unsafe")
    
    def is_safe_category(self, unified_category):
        """
        Determine if a unified category represents safe content
        
        Args:
            unified_category (str): The unified category
            
        Returns:
            bool: True if safe, False if unsafe
        """
        return unified_category == "safe"
