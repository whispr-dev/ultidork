# proxy_manager.py
import random
import threading
import time
import logging
import os

class ProxyManager:
    def __init__(self, refresh_interval_min=15, max_proxies=100, disable_refresh=False, proxy_file="Proxy_list.txt"):
        self.pool = []
        self.lock = threading.Lock()
        self.refresh_interval = refresh_interval_min * 60
        self.max_proxies = max_proxies
        self.disable_refresh = disable_refresh
        self.load_from_file("data/proxies/proxies.txt")
        self.proxy_file = proxy_file
        self.proxies = self.load_proxies()

        
    def load_from_file(self, path):
        """Load proxies from file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.pool = [line.strip() for line in f if line.strip()]
            logging.info(f"Loaded {len(self.pool)} proxies from {path}")

    def load_proxies(self):
        try:
            with open(self.proxy_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []
    
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
    
    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
        
    def add_proxy(self, proxy):
        """Add a proxy to the pool"""
        with self.lock:
            if proxy not in self.pool:
                self.pool.append(proxy)
