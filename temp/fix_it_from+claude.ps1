##!/usr/bin/env python3
"""
Quick Fix Script for OmniDork (Windows Safe Version)
====================================================
No unicode issues!
"""

import os
import json
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    dirs = [
        "data/proxies",
        "data/accounts", 
        "data/findings",
        "exported_proxies",
        "logs",
        "core",
        "utils",
        "config",
        "behavior"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"[+] Created directory: {dir_path}")

def create_config_file():
    """Create a working config.py with proxy sources"""
    config_content = '''# config.py - Working Configuration
import os

# Proxy Sources - These are actual working sources
PROXY_SOURCES = [
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt',
    'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all',
    'https://www.proxy-list.download/api/v1/get?type=http',
    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
]

# Scanner settings
CHECK_INTERVAL = 30
CONNECTION_LIMIT = 100  # Reduced for stability
VALIDATION_ROUNDS = 2
VALIDATION_MODE = 'any'
TIMEOUT = 5.0
CHECK_ANONYMITY = False  # Faster without anonymity check
FORCE_FETCH = True
SINGLE_RUN = True
VERBOSE = True

# Test endpoints
TEST_ENDPOINTS = [
    'http://httpbin.org/ip',
    'https://api.ipify.org/?format=json',
    'http://ip-api.com/json/',
]
'''
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    print("[+] Created config.py with proxy sources")

def create_missing_modules():
    """Create minimal versions of missing modules"""
    
    # Create core/account.py
    account_content = '''# core/account.py
import json
from pathlib import Path

class AccountManager:
    def __init__(self, account_file="data/accounts/my_accounts.json"):
        self.accounts = []
        self.account_file = Path(account_file)
        self._load_accounts()
    
    def _load_accounts(self):
        if self.account_file.exists():
            try:
                with open(self.account_file, 'r') as f:
                    self.accounts = json.load(f)
            except:
                self.accounts = []
    
    def get_random_account(self):
        if self.accounts:
            import random
            return random.choice(self.accounts)
        return {"email": "test@example.com", "password": "password123"}
'''
    
    with open('core/account.py', 'w', encoding='utf-8') as f:
        f.write(account_content)
    print("[+] Created core/account.py")
    
    # Create empty __init__.py files
    for module in ['core', 'utils', 'behavior']:
        init_file = Path(module) / '__init__.py'
        init_file.touch()
        print(f"[+] Created {init_file}")

def create_proxy_manager():
    """Create a working proxy_manager.py"""
    proxy_manager_content = '''# proxy_manager.py
import random
import threading
import time
import logging
import os

class ProxyManager:
    def __init__(self, refresh_interval_min=15, max_proxies=100, disable_refresh=False):
        self.pool = []
        self.lock = threading.Lock()
        self.refresh_interval = refresh_interval_min * 60
        self.max_proxies = max_proxies
        self.disable_refresh = disable_refresh
        self.load_from_file("data/proxies/proxies.txt")
        
    def load_from_file(self, path):
        """Load proxies from file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.pool = [line.strip() for line in f if line.strip()]
            logging.info(f"Loaded {len(self.pool)} proxies from {path}")
    
    def get_proxies(self):
        """Get all proxies"""
        with self.lock:
            return self.pool.copy()
    
    def get_proxy(self):
        """Get a random proxy"""
        with self.lock:
            if self.pool:
                return random.choice(self.pool)
        return None
    
    def add_proxy(self, proxy):
        """Add a proxy to the pool"""
        with self.lock:
            if proxy not in self.pool:
                self.pool.append(proxy)
'''
    
    with open('proxy_manager.py', 'w', encoding='utf-8') as f:
        f.write(proxy_manager_content)
    print("[+] Created proxy_manager.py")

def create_sample_accounts():
    """Create sample accounts file"""
    accounts = [
        {
            "email": "user1@example.com",
            "password": "password123",
            "notes": "Test account 1"
        },
        {
            "email": "user2@example.com", 
            "password": "password456",
            "notes": "Test account 2"
        }
    ]
    
    accounts_file = Path("data/accounts/my_accounts.json")
    accounts_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(accounts_file, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2)
    print("[+] Created sample accounts file")

def create_integration_config():
    """Create integration configuration"""
    config = {
        "proxy_sources": [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all"
        ],
        "scanner": {
            "connection_limit": 100,
            "timeout": 5.0,
            "validation_rounds": 2
        },
        "enable_dorking": True,
        "enable_crawling": True,
        "enable_paywall_bypass": False,
        "verbose": True
    }
    
    with open('omnidork_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    print("[+] Created omnidork_config.json")

def test_imports():
    """Test if imports work"""
    print("\n[*] Testing imports...")
    
    try:
        import aiohttp
        print("[+] aiohttp installed")
    except ImportError:
        print("[-] aiohttp not installed - run: pip install aiohttp")
    
    try:
        import bs4
        print("[+] beautifulsoup4 installed")
    except ImportError:
        print("[-] beautifulsoup4 not installed - run: pip install beautifulsoup4")
    
    try:
        from selenium import webdriver
        print("[+] selenium installed")
    except ImportError:
        print("[-] selenium not installed - run: pip install selenium")
    
    try:
        import colorama
        print("[+] colorama installed")
    except ImportError:
        print("[-] colorama not installed - run: pip install colorama")

def create_rapidproxy_config():
    """Create RapidProxyScan config if needed"""
    config_content = '''# rapidproxyscan_config.py
PROXY_SOURCES = [
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all',
]
'''
    with open('rapidproxyscan_config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    print("[+] Created rapidproxyscan_config.py")

def main():
    print("=" * 50)
    print("OmniDork Quick Fix Script (Windows Safe)")
    print("=" * 50)
    print()
    
    # Create directories
    print("[*] Creating directories...")
    create_directories()
    
    # Create configuration files
    print("\n[*] Creating configuration files...")
    create_config_file()
    create_integration_config()
    create_rapidproxy_config()
    
    # Create missing modules
    print("\n[*] Creating missing modules...")
    create_missing_modules()
    create_proxy_manager()
    
    # Create sample data
    print("\n[*] Creating sample data...")
    create_sample_accounts()
    
    # Test imports
    test_imports()
    
    print("\n" + "=" * 50)
    print("[+] Quick fix complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Install missing packages:")
    print("   pip install aiohttp beautifulsoup4 selenium colorama requests")
    print("\n2. Run proxy fetcher:")
    print("   python fetch_initial_proxies.py")
    print("\n3. Then run OmniDork:")
    print("   python ultidork_master.py")
    print("\n4. Choose option 1 first to update proxy pool")
    print("5. Then scan real domains like: example.com or github.com")

if __name__ == "__main__":
    main()