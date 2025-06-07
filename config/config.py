# config.py

# Unified firewall categories
UNIFIED_CATEGORIES = {
    "safe": {
        "code": "SAFE",
        "description": "Content is safe and does not violate any policies",
        "severity": 0
    },
    "jailbreak": {
        "code": "JAILBREAK",
        "description": "Jailbreak attempt detected",
        "severity": 3
    },
    "harmful_prompt": {
        "code": "HARMFUL",
        "description": "Harmful or malicious prompt",
        "severity": 2
    },
    "prompt_injection": {
        "code": "PROMPT_INJECTION",
        "description": "Prompt injection attempt detected",
        "severity": 2
    },
    "unknown_unsafe": {
        "code": "UNKNOWN_UNSAFE",
        "description": "Unsafe content of unknown or mixed type",
        "severity": 1
    }
}

# LlamaGuard S1-S14 categories mapping to unified categories
LLAMAGUARD_CATEGORY_MAPPING = {
    "S1": "harmful_prompt",    # Violent Crimes
    "S2": "harmful_prompt",    # Non-Violent Crimes
    "S3": "harmful_prompt",    # Sex-Related Crimes
    "S4": "harmful_prompt",    # Child Sexual Exploitation
    "S5": "harmful_prompt",    # Defamation
    "S6": "harmful_prompt",    # Specialized Advice
    "S7": "harmful_prompt",    # Privacy
    "S8": "harmful_prompt",    # Intellectual Property
    "S9": "harmful_prompt",    # Indiscriminate Weapons
    "S10": "harmful_prompt",   # Hate
    "S11": "harmful_prompt",   # Suicide & Self-Harm
    "S12": "harmful_prompt",   # Sexual Content
    "S13": "jailbreak",        # Elections (could be manipulation attempt)
    "S14": "jailbreak",        # Code Interpreter Abuse
    "safe": "safe"
}

# Granite Guard mapping (simple safe/unsafe)
GRANITE_CATEGORY_MAPPING = {
    "safe": "safe",
    "unsafe": "unknown_unsafe"
}

# Category conflict resolution rules
CATEGORY_CONFLICT_RESOLUTION = {
    "strategy": "highest_severity",  # Options: "highest_severity", "first_match", "consensus"
    "severity_order": ["safe", "unknown_unsafe", "harmful_prompt", "prompt_injection", "jailbreak"]
}

default_config = {
    "keyword_filter": {
        "enabled": True,
        "blacklist_file": None,  # Use default blacklist
        "short_circuit": True    # Stop checking if keyword filter flags content
    },
    "guards": [
        {
            "type": "llama_guard",
            "enabled": True,
            "model_name": "llama-guard3",
            "category_mapping": LLAMAGUARD_CATEGORY_MAPPING
        },
        {
            "type": "granite_guard",
            "enabled": True,
            "model_name": "granite3-guardian:8b",
            "category_mapping": GRANITE_CATEGORY_MAPPING
        }
    ],
    "categories": {
        "unified_categories": UNIFIED_CATEGORIES,
        "conflict_resolution": CATEGORY_CONFLICT_RESOLUTION
    }
}