import re
import json
import os


class KeywordFilter:
    """Keyword and regex-based content filter"""

    def __init__(self, blacklist_file=None):
        self.blacklist_file = blacklist_file
        self.blacklist = {"keywords": [], "regex_patterns": []}
        self.compiled_patterns = []

        # Load default blacklist if no file specified
        if not blacklist_file:
            self._load_default_blacklist()
        else:
            self.load_blacklist(blacklist_file)

    def _load_default_blacklist(self):
        """Load a default set of keywords and patterns"""
        self.blacklist = {
            "keywords": [
                "hack",
                "exploit",
                "bypass security",
                "illegal",
                "steal password",
                "malware",
                "phishing",
                "ransomware",
                "keylogger",
            ],
            "regex_patterns": [
                r"(\b|_)password(\b|_)",
                r"(\b|_)ssh[_-]key(\b|_)",
                r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b",
                # Credit card pattern
            ],
        }
        self._compile_patterns()

    def load_blacklist(self, file_path):
        """Load blacklist from a JSON file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    self.blacklist = json.load(f)
                self._compile_patterns()
            else:
                print(f"Blacklist file {file_path} not found. Using default.")
                self._load_default_blacklist()
        except Exception as e:
            print(f"Error loading blacklist: {str(e)}")
            self._load_default_blacklist()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.blacklist["regex_patterns"]
        ]

    def check_content(self, text):
        """
        Check if content contains blacklisted keywords or matches regex patterns

        Args:
            text (str): Text to check

        Returns:
            dict: Result with {'is_safe': bool, 'reason': str, 'matches': list}
        """
        matches = []

        # Check keywords
        text_lower = text.lower()
        for keyword in self.blacklist["keywords"]:
            if keyword.lower() in text_lower:
                matches.append(f"Keyword: {keyword}")

        # Check regex patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(text):
                matches.append(f"Pattern: {self.blacklist['regex_patterns'][i]}")

        is_safe = len(matches) == 0
        reason = (
            "Content contains blacklisted terms" if not is_safe else "Content passed keyword filter"
        )

        return {"is_safe": is_safe, "reason": reason, "matches": matches}
