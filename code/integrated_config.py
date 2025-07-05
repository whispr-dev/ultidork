# integrated_config.py
"""
Integrated Configuration for OmniDork System
===========================================
Brings together all components into a unified configuration
"""

import os
from pathlib import Path

# Import component configurations
from extended_user_agents import USER_AGENTS, get_random_user_agent
from proxy_starter_list import PROXY_SOURCES, TEST_ENDPOINTS, get_elite_sources
from crawl_targets import CRAWL_TARGETS, get_targets_by_category

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for dir_path in [DATA_DIR, CONFIG_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =====================================================
# OMNIDORK RUST CONFIGURATION
# =====================================================
OMNIDORK_CONFIG = {
    "database": {
        "url": os.getenv("DATABASE_URL", "postgres://user:pass@localhost/omnidork"),
        "max_connections": 10,
        "timeout": 30,
    },
    
    "quantum_engine": {
        "max_documents": 10000,
        "compression_threshold": 1024 * 1024,  # 1MB
        "checkpoint_interval": 300,  # 5 minutes
        "fragility": 0.2,
        "entropy_weight": 0.1,
        "use_quantum_scoring": True,
        "use_persistence_theory": True,
    },
    
    "dork_engine": {
        "max_results_per_dork": 100,
        "rate_limit_delay": 2.0,  # seconds
        "user_agents": USER_AGENTS["desktop_windows"][:5],  # Top 5 Windows agents
        "custom_dorks": [
            'site:{domain} "api key"',
            'site:{domain} "authorization: Bearer"',
            'site:{domain} filetype:env',
            'site:{domain} filetype:json "password"',
            'site:{domain} inurl:swagger',
            'site:{domain} inurl:graphql',
            'site:{domain} "index of" backup',
            'site:{domain} intitle:"index of" "parent directory"',
        ],
    },
    
    "crawler": {
        "max_pages": 1000,
        "max_depth": 3,
        "concurrent_requests": 20,
        "timeout": 30,
        "respect_robots": False,
        "follow_redirects": True,
    },
    
    "vulnerability_matcher": {
        "custom_patterns": [
            {
                "name": "Hardcoded Credentials",
                "regex": r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\']{4,})["\']',
                "severity": "High",
            },
            {
                "name": "Private SSH Key",
                "regex": r'-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE KEY-----',
                "severity": "Critical",
            },
            {
                "name": "AWS Credentials",
                "regex": r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*["\']([^"\']+)["\']',
                "severity": "Critical",
            },
        ],
    },
}

# =====================================================
# RAPIDPROXYSCAN CONFIGURATION
# =====================================================
RAPIDPROXY_CONFIG = {
    "scanner": {
        "connection_limit": 1250,
        "validation_rounds": 3,
        "validation_mode": "majority",
        "timeout": 5.0,
        "check_anonymity": True,
        "force_fetch": False,
        "single_run": False,
    },
    
    "sources": {
        "elite": get_elite_sources(),
        "general": PROXY_SOURCES["general_sources"],
        "api": PROXY_SOURCES["api_endpoints"],
        "backup": PROXY_SOURCES["backup_sources"],
    },
    
    "test_endpoints": TEST_ENDPOINTS,
    
    "optimization": {
        "use_cdn_endpoints": True,
        "dns_cache_ttl": 300,
        "header_compression": True,
        "binary_protocol": False,
        "prioritize_elite": True,
    },
    
    "export": {
        "formats": ["txt", "csv", "json"],
        "directory": str(DATA_DIR / "proxies"),
        "prefix": "proxies",
    },
}

# =====================================================
# SUPREME VIEWBOT CONFIGURATION
# =====================================================
VIEWBOT_CONFIG = {
    "browser": {
        "headless": True,
        "disable_images": True,
        "window_size": "1920x1080",
        "user_agents": get_random_user_agent,  # Function reference
        "extensions": [],
    },
    
    "captcha": {
        "enabled": True,
        "api_key": os.getenv("CAPTCHA_API_KEY", ""),
        "service": "2captcha",
        "max_retries": 30,
        "poll_interval": 5,
    },
    
    "paywall_bypass": {
        "enabled": True,
        "methods": [
            "archive_org",
            "google_cache",
            "outline_com",
            "12ft_ladder",
            "reader_mode",
            "cookie_removal",
            "javascript_disable",
        ],
        "sites": get_targets_by_category("paywalled_sites"),
    },
    
    "humanization": {
        "mouse_movements": True,
        "scroll_behavior": True,
        "typing_delays": True,
        "random_pauses": True,
        "viewport_changes": True,
    },
    
    "proxy_rotation": {
        "enabled": True,
        "rotate_per_request": False,
        "rotate_per_session": True,
        "fallback_to_direct": True,
    },
    
    "accounts": {
        "file": str(DATA_DIR / "accounts" / "my_accounts.json"),
        "rotate": True,
        "create_if_needed": False,
    },
}

# =====================================================
# INTEGRATED SCANNER CONFIGURATION
# =====================================================
INTEGRATED_CONFIG = {
    "modes": {
        "osint": {
            "enabled": True,
            "components": ["dork_engine", "vulnerability_matcher", "bug_bounty"],
        },
        "quantum": {
            "enabled": True,
            "components": ["crawler", "quantum_engine"],
        },
        "proxy": {
            "enabled": True,
            "components": ["proxy_scanner"],
        },
        "evasion": {
            "enabled": True,
            "components": ["paywall_bypass", "captcha_solver", "humanization"],
        },
    },
    
    "workflow": {
        "proxy_first": True,  # Get proxies before scanning
        "use_proxies_for_dorking": True,
        "use_proxies_for_crawling": True,
        "parallel_processing": True,
        "save_checkpoints": True,
    },
    
    "targets": {
        "bug_bounty": get_targets_by_category("bug_bounty_platforms"),
        "security": get_targets_by_category("security_resources"),
        "testing": get_targets_by_category("testing_targets"),
        "custom": [],  # Add your own targets
    },
    
    "reporting": {
        "formats": ["json", "markdown", "html", "csv"],
        "include_screenshots": True,
        "include_raw_data": False,
        "output_dir": str(DATA_DIR / "reports"),
    },
    
    "logging": {
        "level": "INFO",
        "file": str(LOGS_DIR / "omnidork.log"),
        "max_size": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

# =====================================================
# ENVIRONMENT CONFIGURATION
# =====================================================
ENV_CONFIG = {
    "development": {
        "debug": True,
        "verbose": True,
        "proxy_limit": 100,
        "crawl_limit": 50,
    },
    
    "production": {
        "debug": False,
        "verbose": False,
        "proxy_limit": 10000,
        "crawl_limit": 5000,
    },
    
    "testing": {
        "debug": True,
        "verbose": True,
        "proxy_limit": 10,
        "crawl_limit": 10,
        "use_test_targets": True,
    },
}

# Current environment
ENVIRONMENT = os.getenv("OMNIDORK_ENV", "development")
CURRENT_ENV = ENV_CONFIG.get(ENVIRONMENT, ENV_CONFIG["development"])

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_config():
    """Get the complete configuration"""
    return {
        "omnidork": OMNIDORK_CONFIG,
        "rapidproxy": RAPIDPROXY_CONFIG,
        "viewbot": VIEWBOT_CONFIG,
        "integrated": INTEGRATED_CONFIG,
        "environment": CURRENT_ENV,
    }

def save_config(filename="omnidork_config.json"):
    """Save configuration to file"""
    import json
    config = get_config()
    
    # Convert function references to strings
    if callable(config["viewbot"]["browser"]["user_agents"]):
        config["viewbot"]["browser"]["user_agents"] = "get_random_user_agent"
    
    with open(filename, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {filename}")

def load_config(filename="omnidork_config.json"):
    """Load configuration from file"""
    import json
    with open(filename, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    # Display configuration summary
    config = get_config()
    
    print("OmniDork Integrated Configuration")
    print("=================================")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Config Directory: {CONFIG_DIR}")
    print(f"Logs Directory: {LOGS_DIR}")
    print(f"\nProxy Sources: {len(RAPIDPROXY_CONFIG['sources']['elite'])} elite, "
          f"{len(RAPIDPROXY_CONFIG['sources']['general'])} general")
    print(f"User Agents: {sum(len(agents) for agents in USER_AGENTS.values())} total")
    print(f"Crawl Targets: {sum(len(targets) for targets in CRAWL_TARGETS.values())} total")
    
    # Save default configuration
    save_config()
