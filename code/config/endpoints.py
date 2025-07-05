# D:\code\ultidorki\code\core\proxy_manager.py
import asyncio
import random
import time
import logging
from typing import List, Dict, Optional, Any

# Make sure the problematic import line is GONE from here:
# from config.endpoints import PROXY_SOURCES, PROXY_TEST_URL # THIS LINE MUST BE DELETED

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages a pool of proxies, providing functionalities to add, retrieve,
    and refresh proxies. This is distinct from RapidProxyScanManager
    which is focused on *scanning* and *testing* proxies from sources.
    This manager provides a usable pool for other modules.
    """
    def __init__(self, refresh_interval_min: int = 15, max_proxies: int = 1000, disable_refresh: bool = False):
        self.pool: List[str] = []  # Stores proxy strings, e.g., "http://host:port"
        self.refresh_interval_min = refresh_interval_min
        self.max_proxies = max_proxies
        self.disable_refresh = disable_refresh
        self.last_refresh_time = time.time()
        self.lock = asyncio.Lock() # For concurrent access if needed

        # Assuming config might be passed, but not directly used by ProxyManager
        # as it operates on its own pool of validated proxies.
        # If your UnifiedScanner loads proxies into this manager, it will use them.

    def add_proxy(self, proxy_address: str):
        """Adds a single proxy to the pool if it's not already there and within limits."""
        if proxy_address not in self.pool and len(self.pool) < self.max_proxies:
            self.pool.append(proxy_address)
            logger.debug(f"Added proxy to pool: {proxy_address}")
        elif proxy_address in self.pool:
            logger.debug(f"Proxy already in pool: {proxy_address}")
        else:
            logger.warning(f"Proxy pool full. Skipping {proxy_address}")

    def add_proxies(self, proxy_list: List[str]):
        """Adds multiple proxies to the pool."""
        for proxy in proxy_list:
            self.add_proxy(proxy)

    def get_proxy(self) -> Optional[str]:
        """Gets a random proxy from the pool."""
        if not self.pool:
            logger.warning("Proxy pool is empty. No proxy available.")
            return None
        return random.choice(self.pool)

    def get_proxies(self) -> List[str]:
        """Returns the entire list of proxies in the pool."""
        return list(self.pool)

    def get_pool_size(self) -> int:
        """Returns the current number of proxies in the pool."""
        return len(self.pool)

    def clear_pool(self):
        """Clears all proxies from the pool."""
        self.pool = []
        logger.info("Proxy pool cleared.")

    async def load_from_file(self, filepath: str):
        """Loads proxies from a text file (one proxy per line)."""
        try:
            with open(filepath, 'r') as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.add_proxies(proxies)
            logger.info(f"Loaded {len(proxies)} proxies from {filepath}")
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading proxies from file {filepath}: {e}")

    def get_elite_proxies_raw_strings(self) -> List[str]:
        """
        Placeholder to simulate getting elite proxies.
        In a real scenario, this might filter from the main pool
        or load from a specific 'elite' export by RapidProxyScan.
        For now, returns a small dummy list.
        """
        logger.warning("Using dummy elite proxies for _acquire_and_test_elite_proxies in QuantumOSINTBridge. "
                       "You should load actual elite proxies into ProxyManager from RapidProxyScan exports.")
        return [
            "http://192.168.1.1:8888", # Example private IP (will fail external test)
            "http://192.168.1.2:8080",
            "http://1.1.1.1:80", # Dummy public IP (ensure it's not real or used only for testing)
            "http://2.2.2.2:443"
        ]
