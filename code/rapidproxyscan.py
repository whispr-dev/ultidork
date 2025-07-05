# rapidproxyscan.py

"""
RapidProxyScan - Advanced Optimizations Module
==============================================

This module implements a sophisticated proxy scanner with advanced optimizations:
1. Lightweight custom endpoint creation
2. CDN-distributed endpoint selection for geographical optimization
3. DNS pre-resolution and aggressive caching
4. Header compression and bandwidth optimization
5. Binary protocol implementations
6. Special formatting for viewbot/Supreme environments

Requirements:
- Python 3.7+
- aiohttp
- beautifulsoup4
- colorama
"""

import asyncio
import socket
import ipaddress
import random
import time
import json
import gzip
import struct
import hashlib
import logging
import os
import aiohttp
import argparse
import re
import csv
import sys # Added for sys.exit in utilities
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import defaultdict

# Import your config.py file to access the global constants
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("proxy_optimizer")

# Initialize colorama
init()

# Global constants (if any remain that are not in config.py, e.g., USER_AGENTS)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.5 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
]

# ===========================================================================
# PROXY RELATED CLASSES
# ===========================================================================

class ProxyTester:
    def __init__(self, test_url: str = "http://proxy-test.fastping.it.com/"):
        """
        Initializes the ProxyTester with a specific URL to test proxies against.
        """
        self.test_url = test_url
        logger.debug(f"ProxyTester initialized with test URL: {self.test_url}")

    # Helper to determine speed based on measured latency (client-side)
    def _determine_speed(self, latency_ms: float) -> str:
        """
        Determines proxy speed based on measured latency.
        These are example thresholds; adjust as needed for UltiDork.
        """
        if latency_ms < 200:
            return "fast"
        elif latency_ms < 800:
            return "medium"
        else:
            return "slow"

    async def test_proxy(self, proxy_url: str) -> dict:
        """
        Tests a single proxy against the specified test_url and
        interprets its JSON response for speed, anonymity, and security.

        Args:
            proxy_url: The full URL of the proxy (e.g., "http://user:pass@host:port").

        Returns:
            A dictionary containing proxy details and interpreted metrics.
            Returns a dictionary with 'is_usable': False and 'error' on failure.
        """
        start_time = time.time()
        result = {
            "proxy": proxy_url,
            "is_usable": False,
            "latency_ms": -1,
            "description": "Proxy test failed or unknown status.",
            "security_level": "unknown",  # 'secure as hecc', 'medium', 'low', 'unknown'
            "speed_rating": "unknown",    # 'fast', 'medium', 'slow', 'unknown'
            "raw_json_response": None,
            "error": None
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.test_url, proxy=proxy_url, timeout=15) as response:
                    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                    json_data = await response.json()
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000  # Latency in milliseconds (client-side RTT)

                    result["latency_ms"] = latency
                    result["raw_json_response"] = json_data

                    if json_data and json_data.get("status") == "success":
                        result["is_usable"] = True
                        result["description"] = "Proxy is active and responsive."

                        # Extract fields from your proxy test app's JSON
                        anonymity_level_from_endpoint = json_data.get("anonymity_level", "unknown").lower()
                        connecting_ip = json_data.get("connecting_ip")
                        client_ip_from_headers = json_data.get("client_ip_from_headers")

                        # Determine security level
                        if anonymity_level_from_endpoint == "elite":
                            result["security_level"] = "secure as hecc"
                            result["description"] += " Highly anonymous."
                        elif anonymity_level_from_endpoint == "anonymous":
                            result["security_level"] = "medium"
                            result["description"] += " Anonymous."
                        elif anonymity_level_from_endpoint == "transparent":
                            result["security_level"] = "low"
                            result["description"] += " Not very well hidden (transparent)."
                        else:
                            result["security_level"] = "unknown"
                            result["description"] += " Anonymity unknown."

                        # Determine speed rating using the client-side calculated latency
                        result["speed_rating"] = self._determine_speed(latency)
                        result["description"] += f" This is a {result['speed_rating']} proxy."

                        # Additional checks for transparency, even if endpoint inferred "elite" or "anonymous"
                        # If client_ip_from_headers is present and different from connecting_ip, it's leaky
                        if client_ip_from_headers and connecting_ip and client_ip_from_headers != connecting_ip:
                            # Re-classify if it was thought to be elite/anonymous but leaked IP
                            if result["security_level"] != "low":
                                result["security_level"] = "low (IP leaked)"
                                result["description"] = result["description"].replace("Highly anonymous.", "").replace("Anonymous.", "") + " Exposed via headers."

                    else:
                        result["description"] = f"Proxy test endpoint returned non-success status or invalid JSON: {json_data}"

        except aiohttp.ClientError as e:
            result["error"] = str(e)
            result["description"] = f"Connection error: {e}"
            logger.warning(f"Proxy test failed for {proxy_url} (ClientError): {e}")
        except json.JSONDecodeError as e:
            result["error"] = str(e)
            result["description"] = f"Invalid JSON response: {e}"
            logger.warning(f"Proxy test for {proxy_url} received non-JSON response: {e}")
        except asyncio.TimeoutError:
            result["error"] = "timeout"
            result["description"] = "Proxy test timed out."
            result["speed_rating"] = "slow" # Mark as slow if it times out
            logger.warning(f"Proxy test timed out for {proxy_url}")
        except Exception as e:
            result["error"] = str(e)
            result["description"] = f"An unexpected error occurred: {e}"
            logger.error(f"An unexpected error occurred during proxy test for {proxy_url}: {e}")

        logger.debug(f"Proxy test result for {proxy_url}: {result}")
        return result


# =============================================================
# >>> BEGIN ProxyInfo CLASS DETAILED INFO SECTION <<<
# =============================================================

class ProxyInfo:
    """
    Represents detailed information about a single proxy.
    """
    def __init__(self, host: str, port: int, protocol: str = "http", country: str = "Unknown",
                 avg_response_time: float = 0, reliability: float = 0, anonymity: str = "unknown"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.country = country
        self.avg_response_time = avg_response_time
        self.reliability = reliability
        self.anonymity = anonymity
        self.last_tested = 0 # Timestamp of last test
        # Add the new detailed fields from ProxyTester
        self.is_usable: bool = False
        self.latency_ms: float = -1
        self.description: str = "Not tested yet."
        self.security_level: str = "unknown"
        self.speed_rating: str = "unknown"
        self.raw_json_response: Optional[Dict[str, Any]] = None


    def update_from_test_result(self, test_result: Dict[str, Any]):
        """Updates ProxyInfo attributes from a ProxyTester result."""
        self.is_usable = test_result.get("is_usable", False)
        self.latency_ms = test_result.get("latency_ms", -1)
        self.description = test_result.get("description", "No detailed description.")
        self.security_level = test_result.get("security_level", "unknown")
        self.speed_rating = test_result.get("speed_rating", "unknown")
        self.raw_json_response = test_result.get("raw_json_response")

        # Update core proxy info if available in test result
        if self.raw_json_response:
            self.anonymity = self.raw_json_response.get("anonymity_level", "unknown")
            # You might want to get country from raw_json_response if available
            # self.country = self.raw_json_response.get("country", self.country)

    def to_dict(self) -> Dict[str, Any]:
        """Converts proxy information to a dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "avg_response_time": self.avg_response_time, # This might be less relevant now
            "reliability": self.reliability,             # This too
            "anonymity": self.anonymity,
            "last_tested": self.last_tested,
            "is_usable": self.is_usable,
            "latency_ms": self.latency_ms,
            "description": self.description,
            "security_level": self.security_level,
            "speed_rating": self.speed_rating,
            "raw_json_response": self.raw_json_response # Include for full detail
        }

    def __repr__(self) -> str:
        """String representation of the ProxyInfo object."""
        return f"ProxyInfo({self.host}:{self.port} [{self.protocol}], Usable: {self.is_usable}, Speed: {self.speed_rating}, Security: {self.security_level})"

    def __hash__(self) -> int:
        """Enables hashing for use in sets/dictionaries."""
        return hash((self.host, self.port, self.protocol))

    def __eq__(self, other: Any) -> bool:
        """Enables equality comparison."""
        if not isinstance(other, type(self)): return NotImplemented
        return self.host == other.host and self.port == other.port and self.protocol == other.protocol

# ===========================================================================
# OPTIMIZER INTEGRATION (Placeholder for your advanced logic)
# ===========================================================================

class OptimizerIntegration:
    """
    Placeholder for the advanced optimization logic of RapidProxyScan.
    This class would implement custom endpoint creation, CDN selection,
    DNS pre-resolution, header compression, binary protocols, etc.
    """
    def __init__(self):
        logger.debug("OptimizerIntegration initialized.")

    async def initialize(self):
        """Initializes any resources required by the optimizer."""
        logger.info("Optimizer: Initializing...")
        await asyncio.sleep(0.1) # Simulate async initialization
        logger.info("Optimizer: Initialization complete.")

    async def optimize_proxy_test(self, session: aiohttp.ClientSession, proxy_info: ProxyInfo) -> Dict[str, Any]:
        """
        Determines optimal test configuration for a given proxy.
        Returns a dictionary with 'url', 'headers', 'is_fast_track', 'use_binary_protocol'.
        """
        # In this updated flow, the ProxyTester directly handles the test URL.
        # This method could still be used for *other* optimizations, like
        # choosing different test patterns or headers based on proxy type,
        # but the primary test URL for detailed JSON is handled by ProxyTester.
        optimized_url = proxy_info.raw_json_response.get('test_endpoint', "http://proxy-test.fastping.it.com/") if proxy_info.raw_json_response else "http://proxy-test.fastping.it.com/" # Default to the common test URL
        headers = self._get_random_headers() # Use internal method for headers

        # Example optimization logic (to be replaced by actual implementation)
        is_fast_track = random.choice([True, False])
        use_binary_protocol = random.choice([True, False])

        logger.debug(f"Optimizer: Optimizing test for {proxy_info.host}:{proxy_info.port}")
        return {
            'url': optimized_url,
            'headers': headers,
            'is_fast_track': is_fast_track,
            'use_binary_protocol': use_binary_protocol
        }

    async def post_test_processing(self, proxy_info: ProxyInfo, success: bool, test_result: Dict[str, Any], endpoint: str):
        """
        Processes the results after a proxy test using the detailed test_result.
        Updates proxy_info's attributes based on the comprehensive test results.
        """
        logger.debug(f"Optimizer: Post-test processing for {proxy_info.host}:{proxy_info.port}")
        proxy_info.update_from_test_result(test_result) # Update with all detailed info

        # Old reliability/avg_response_time might become less relevant if we use new fields
        if success:
            proxy_info.reliability = min(100, proxy_info.reliability + 5)
            proxy_info.avg_response_time = (proxy_info.avg_response_time + proxy_info.latency_ms) / 2 if proxy_info.avg_response_time else proxy_info.latency_ms
        else:
            proxy_info.reliability = max(0, proxy_info.reliability - 10)
        proxy_info.last_tested = time.time()

        # Example: Log the outcome or trigger further actions
        if success:
            logger.info(f"Optimizer: Proxy {proxy_info.host}:{proxy_info.port} passed test (Latency: {proxy_info.latency_ms:.0f}ms, Speed: {proxy_info.speed_rating}, Security: {proxy_info.security_level}).")
        else:
            logger.warning(f"Optimizer: Proxy {proxy_info.host}:{proxy_info.port} failed test: {proxy_info.description}.")

    async def export_specialized_formats(self, proxies_to_export: List[ProxyInfo]) -> List[str]:
        """
        Exports verified proxies in specialized formats for viewbot/Supreme environments.
        Returns a list of paths to the exported files.
        """
        logger.info("Optimizer: Exporting specialized formats (placeholder)...")
        # Placeholder: Actual implementation would generate specific file formats.
        # For now, just print a message.
        if proxies_to_export:
            logger.info(f"Optimizer: Would export {len(proxies_to_export)} proxies to specialized formats.")
        return []

    def _get_random_headers(self) -> Dict[str, str]:
        """Helper to get random headers for optimization."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

# ===========================================================================
# PROXY SCANNER MANAGER
# ===========================================================================

class ProxyScanManager:
    """Main proxy scan manager class for RapidProxyScan."""
    def __init__(self,
                 check_interval: int,
                 connection_limit: int,
                 validation_rounds: int,
                 validation_mode: str,
                 timeout: float,
                 check_anonymity: bool,
                 force_fetch: bool,
                 verbose: bool,
                 single_run: bool,
                 # Parameters sourced from config.py's global constants
                 proxy_sources: List[str],
                 proxy_test_workers: int,
                 proxy_fetch_interval: int,
                 proxy_test_timeout: float,
                 proxy_test_retries: int,
                 max_proxies_to_keep: int,
                 proxy_refresh_min_interval: int,
                 test_url: str,
                 export_interval: int,
                 max_fetch_attempts: int,
                 fetch_retry_delay: int
                ):
        # Assign all passed configuration parameters as instance attributes
        self.check_interval = check_interval
        self.connection_limit = connection_limit
        self.validation_rounds = validation_rounds
        self.validation_mode = validation_mode
        self.timeout = timeout
        self.check_anonymity = check_anonymity
        self.force_fetch = force_fetch
        self.single_run = single_run # 'args' object is no longer passed directly to __init__

        self.proxy_sources = proxy_sources
        self.proxy_test_workers = proxy_test_workers
        self.proxy_fetch_interval = proxy_fetch_interval
        self.proxy_test_timeout = proxy_test_timeout
        self.proxy_test_retries = proxy_test_retries
        self.max_proxies_to_keep = max_proxies_to_keep
        self.proxy_refresh_min_interval = proxy_refresh_min_interval
        self.test_url = test_url
        self.export_interval = export_interval
        self.max_fetch_attempts = max_fetch_attempts
        self.fetch_retry_delay = fetch_retry_delay

        # Initialize other dynamic attributes to None or empty before use
        self.session: Optional[aiohttp.ClientSession] = None
        self.proxy_fetch_executor: Optional[ThreadPoolExecutor] = None
        self.proxy_test_executor: Optional[ThreadPoolExecutor] = None
        self.proxies: Dict[str, ProxyInfo] = {} # Change to dict for detailed ProxyInfo objects
        self.verified_proxies: Set[str] = set() # Still keep a set of addresses for quick lookup
        self.lock: asyncio.Lock = asyncio.Lock()
        self.proxy_queue: asyncio.Queue = asyncio.Queue()
        self.proxy_test_queue: asyncio.Queue = asyncio.Queue()
        self.optimizer: OptimizerIntegration = OptimizerIntegration()
        self.proxy_tester = ProxyTester(test_url=self.test_url) # Instantiate the ProxyTester here

        # Set logging level based on verbose flag
        if verbose: # Use the passed verbose argument directly
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def _get_random_headers(self) -> Dict[str, str]:
        """
        Generates a dictionary of random HTTP headers, including a User-Agent.
        """
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1", # Do Not Track Request Header
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

    async def initialize(self):
        """
        Initializes the scanner's resources, including aiohttp session,
        thread pools, and fetches initial proxy lists.
        """
        self.session = aiohttp.ClientSession() # Create a new aiohttp ClientSession
        # Create thread pools for fetching and testing proxies, using configured workers
        self.proxy_fetch_executor = ThreadPoolExecutor(max_workers=self.max_fetch_attempts)
        self.proxy_test_executor = ThreadPoolExecutor(max_workers=self.proxy_test_workers)

        print(f"{Fore.CYAN}Fetching initial proxy lists...{Style.RESET_ALL}")
        logger.info("Fetching initial proxy lists...")
        await self.fetch_proxy_lists()

        print(f"{Fore.GREEN}Scanner initialized successfully.{Style.RESET_ALL}")
        logger.info("Scanner initialized successfully.")

    async def cleanup(self):
        """
        Cleans up scanner resources by closing the aiohttp session
        and shutting down thread pools.
        """
        print(f"{Fore.CYAN}Initiating cleanup...{Style.RESET_ALL}")
        logger.info("Initiating cleanup...")

        # Close the aiohttp session if it exists and is not already closed
        if self.session and not self.session.closed:
            await self.session.close()
            print(f"{Fore.GREEN}aiohttp session closed.{Style.RESET_ALL}")
            logger.info("aiohttp session closed.")

        # Shutdown the proxy fetch thread pool if it exists
        if hasattr(self, 'proxy_fetch_executor') and self.proxy_fetch_executor:
            self.proxy_fetch_executor.shutdown(wait=True) # Wait for current tasks to complete
            print(f"{Fore.GREEN}Proxy fetch executor shut down.{Style.RESET_ALL}")
            logger.info("Proxy fetch executor shut down.")

        # Shutdown the proxy test thread pool if it exists
        if hasattr(self, 'proxy_test_executor') and self.proxy_test_executor:
            self.proxy_test_executor.shutdown(wait=True) # Wait for current tasks to complete
            print(f"{Fore.GREEN}Proxy test executor shut down.{Style.RESET_ALL}")
            logger.info("Proxy test executor shut down.")

        print(f"{Fore.GREEN}Cleanup complete.{Style.RESET_ALL}")
        logger.info("Cleanup complete.")

    async def export_results(self, force: bool = False, output_dir: str = "exported_proxies", filename_prefix: str = "proxies"):
        """
        Exports the verified proxies to text and CSV files.
        Verified proxies are stored in self.verified_proxies (set of "host:port" strings).
        Detailed proxy information is retrieved from self.proxies (dict of {address: ProxyInfo}).

        Args:
            force (bool): If True, forces export even if no new proxies are found (e.g., on program exit).
            output_dir (str): Directory to save the exported files.
            filename_prefix (str): Prefix for the output filenames.
        """
        proxies_to_export_info = [self.proxies[addr] for addr in self.verified_proxies if addr in self.proxies and self.proxies[addr].is_usable]

        if not proxies_to_export_info and not force:
            print(f"{Fore.YELLOW}No new verified proxies to export. Skipping export.{Style.RESET_ALL}")
            logger.info("No new verified proxies to export.")
            return

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.txt")
        csv_filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.csv")

        exported_count = 0
        try:
            with open(txt_filename, 'w') as f_txt:
                for proxy_info in sorted(proxies_to_export_info, key=lambda x: x.latency_ms): # Sort by latency
                    f_txt.write(f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}\n")
                    exported_count += 1
            print(f"{Fore.GREEN}Exported {exported_count} verified proxies to {txt_filename}{Style.RESET_ALL}")
            logger.info(f"Exported {exported_count} verified proxies to {txt_filename}")

            if proxies_to_export_info:
                # Ensure all ProxyInfo objects have a consistent set of keys for CSV header
                # We'll collect all possible keys from the 'to_dict' of all proxies
                all_keys = set()
                for p_info in proxies_to_export_info:
                    all_keys.update(p_info.to_dict().keys())
                csv_headers = sorted(list(all_keys)) # Sort headers for consistent order

                with open(csv_filename, 'w', newline='') as f_csv:
                    writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
                    writer.writeheader()
                    for proxy_info in proxies_to_export_info:
                        row = proxy_info.to_dict()
                        # Fill missing keys with None or empty string to match header
                        for header in csv_headers:
                            if header not in row:
                                row[header] = None # Or ""
                        writer.writerow(row)
                print(f"{Fore.GREEN}Exported detailed proxy info to {csv_filename}{Style.RESET_ALL}")
                logger.info(f"Exported detailed proxy info to {csv_filename}")

        except IOError as e:
            print(f"{Fore.RED}Error exporting proxies: {e}{Style.RESET_ALL}")
            logger.error(f"Error exporting proxies: {e}")
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred during export: {e}{Style.RESET_ALL}")
            logger.error(f"An unexpected error occurred during proxy export: {e}")

    async def fetch_proxy_lists(self):
        """
        Fetches proxy lists from configured sources.
        """
        logger.info(f"Attempting to fetch proxy lists from {len(self.proxy_sources)} sources.")
        fetched_proxies_count = 0
        for source_url in self.proxy_sources:
            print(f"{Fore.YELLOW}Fetching from: {source_url}{Style.RESET_ALL}")
            try:
                async with self.session.get(source_url, timeout=self.timeout) as response:
                    response.raise_for_status() # Raise an exception for HTTP errors
                    content = await response.text()
                    new_proxies = self.parse_proxy_list(content, source_url)
                    for host, port in new_proxies:
                        proxy_address = f"{host}:{port}"
                        if proxy_address not in self.proxies:
                            self.proxies[proxy_address] = ProxyInfo(host, port)
                            # Only add to test queue if it's new, otherwise it will be picked up by refresh logic
                            await self.proxy_test_queue.put(self.proxies[proxy_address])
                            self.proxies[proxy_address].last_tested = time.time() # Mark as queued
                            fetched_proxies_count += 1
                logger.info(f"Fetched {len(new_proxies)} proxies from {source_url}.")
            except aiohttp.ClientError as e:
                logger.error(f"Failed to fetch from {source_url}: {e}")
            except Exception as e:
                logger.error(f"An error occurred while processing {source_url}: {e}")
        print(f"{Fore.CYAN}Total new proxies added to queue: {fetched_proxies_count}{Style.RESET_ALL}")
        logger.info(f"Total new proxies added to queue: {fetched_proxies_count}")

    def parse_proxy_list(self, content: str, source_url: str) -> List[Tuple[str, int]]:
        """
        Parses content from a proxy list URL.
        Currently supports plain text (host:port) and basic HTML parsing.
        """
        proxies = []
        # Attempt to parse as plain text (one proxy per line)
        lines = content.splitlines()
        for line in lines:
            match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', line.strip())
            if match:
                try:
                    host = match.group(1)
                    port = int(match.group(2))
                    proxies.append((host, port))
                except ValueError:
                    logger.debug(f"Skipping invalid proxy format: {line}")
            else:
                # Attempt basic HTML parsing for common table structures
                soup = BeautifulSoup(content, 'html.parser')
                for td in soup.find_all('td'):
                    text = td.get_text(strip=True)
                    match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', text)
                    if match:
                        try:
                            host = match.group(1)
                            port = int(match.group(2))
                            if (host, port) not in proxies: # Avoid duplicates from HTML
                                proxies.append((host, port))
                        except ValueError:
                            pass # Ignore if port is not an int
        return proxies

    async def test_proxy_worker(self):
        """Worker function to test proxies from the queue."""
        while True:
            proxy_info = await self.proxy_test_queue.get()
            if proxy_info is None: # Sentinel value to stop worker
                break

            try:
                proxy_url = f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}"
                test_result = await self.proxy_tester.test_proxy(proxy_url)

                if test_result.get("is_usable"):
                    async with self.lock:
                        proxy_info.update_from_test_result(test_result) # Update detailed info
                        self.verified_proxies.add(f"{proxy_info.host}:{proxy_info.port}")
                        logger.info(f"{Fore.GREEN}Verified: {proxy_info.host}:{proxy_info.port} (Latency: {proxy_info.latency_ms:.0f}ms, Speed: {proxy_info.speed_rating}, Security: {proxy_info.security_level}){Style.RESET_ALL}")
                else:
                    logger.warning(f"{Fore.YELLOW}Failed: {proxy_info.host}:{proxy_info.port} - {test_result.get('description', 'Unknown error')}{Style.RESET_ALL}")
                    proxy_info.update_from_test_result(test_result) # Update even if not usable, for debugging

                # The OptimizerIntegration's post_test_processing now uses the detailed test_result
                await self.optimizer.post_test_processing(proxy_info, test_result.get("is_usable"), test_result, self.test_url)

            except Exception as e:
                logger.error(f"Error in proxy test worker for {proxy_info.host}:{proxy_info.port}: {e}")
            finally:
                self.proxy_test_queue.task_done()

    # The old `test_proxy` method is replaced by calling `self.proxy_tester.test_proxy`
    # and the `check_proxy_anonymity` logic is now handled by the endpoint itself and `ProxyTester`'s interpretation.
    # So these methods can be removed or restructured if they are no longer called directly.
    # For now, I'm removing the old `test_proxy` as the `proxy_test_worker` will now call the `ProxyTester`.
    # The `check_proxy_anonymity` logic should primarily live in your Flask endpoint.

    async def start_scanning_loop(self):
        """
        Manages the main proxy scanning loop.
        """
        last_fetch_time = 0
        last_export_time = 0

        # Start proxy test workers
        workers = [asyncio.create_task(self.test_proxy_worker()) for _ in range(self.proxy_test_workers)]

        while True:
            current_time = time.time()

            # Fetch new proxies periodically
            if current_time - last_fetch_time >= self.proxy_fetch_interval or self.force_fetch:
                await self.fetch_proxy_lists()
                last_fetch_time = current_time
                self.force_fetch = False # Reset force_fetch after fetching

            # Queue proxies for testing (those not tested recently or not yet usable)
            async with self.lock:
                for addr, proxy_info in list(self.proxies.items()):
                    # Re-test if it's been longer than refresh interval, or if it was previously unusable
                    if (current_time - proxy_info.last_tested >= self.proxy_refresh_min_interval) or (not proxy_info.is_usable):
                        await self.proxy_test_queue.put(proxy_info)
                        proxy_info.last_tested = current_time # Mark as queued
                        proxy_info.is_usable = False # Reset usability while re-testing (optional)


            # Perform exports periodically
            if current_time - last_export_time >= self.export_interval and self.verified_proxies:
                await self.export_results()
                last_export_time = current_time
                self.verified_proxies.clear() # Clear after export if desired

            # If single_run mode, break after one cycle (after initial fetch/test)
            if self.single_run:
                # Wait for all tasks to be done in the queues
                await self.proxy_queue.join()
                await self.proxy_test_queue.join()
                await self.export_results(force=True) # Final export
                break

            # If there are no proxies to test and not in single_run mode, wait for a bit
            if self.proxy_queue.empty() and self.proxy_test_queue.empty():
                print(f"{Fore.MAGENTA}No proxies in queue. Waiting for {self.check_interval} seconds...{Style.RESET_ALL}")
                await asyncio.sleep(self.check_interval)
            else:
                # Briefly sleep to allow other tasks to run
                await asyncio.sleep(1)

        # Send sentinel values to stop workers
        for _ in workers:
            await self.proxy_test_queue.put(None)
        await asyncio.gather(*workers) # Wait for workers to finish processing sentinels

    async def run(self):
        """
        Main asynchronous execution method for the proxy scanner.
        Orchestrates initialization, scanning, and graceful shutdown.
        """
        try:
            print(f"{Fore.CYAN}Initializing scanner...{Style.RESET_ALL}")
            logger.info("Initializing scanner...")
            await self.optimizer.initialize() # Initialize the optimizer first
            await self.initialize() # Initialize scanner resources

            print(f"{Fore.CYAN}Scanner initialized. Starting scanning loop...{Style.RESET_ALL}")
            logger.info("Scanner initialized. Starting scanning loop...")
            await self.start_scanning_loop()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Ctrl+C detected. Initiating graceful shutdown...{Style.RESET_ALL}")
            logger.info("Ctrl+C detected. Initiating graceful shutdown.")
            await self.export_results(force=True) # Ensure results are exported on interrupt
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred during scanning: {e}{Style.RESET_ALL}")
            logger.exception("An unexpected error occurred during scanning.")
        finally:
            print(f"{Fore.CYAN}Cleaning up scanner resources...{Style.RESET_ALL}")
            logger.info("Cleaning up scanner resources.")
            await self.cleanup()
            print(f"{Fore.CYAN}Scanner has shut down cleanly.{Style.RESET_ALL}")
            logger.info("Scanner has shut down cleanly.")


# ===========================================================================
# UTILITY FUNCTIONS (from config.py hints, implemented here for completeness)
# ===========================================================================

def run_speed_test(filepath: str):
    """
    Placeholder for a function to run a speed test on proxies from a file.
    """
    print(f"{Fore.BLUE}Running speed test on proxies from: {filepath}{Style.RESET_ALL}")
    logger.info(f"Running speed test on {filepath} (placeholder).")
    # Implement actual speed test logic here
    if not os.path.exists(filepath):
        print(f"{Fore.RED}Error: File not found at {filepath}{Style.RESET_ALL}")
        return
    with open(filepath, 'r') as f:
        proxies = f.readlines()
        print(f"Simulating speed test for {len(proxies)} proxies from {filepath}...")
    print(f"{Fore.GREEN}Speed test completed (placeholder).{Style.RESET_ALL}")

def clean_old_files():
    """
    Placeholder for a function to clean old exported proxy files.
    """
    print(f"{Fore.BLUE}Cleaning old exported files (placeholder)...{Style.RESET_ALL}")
    logger.info("Cleaning old exported files (placeholder).")
    # Implement logic to delete old files here
    print(f"{Fore.GREEN}Old files cleaned (placeholder).{Style.RESET_ALL}")

def analyze_proxy_stats():
    """
    Placeholder for a function to analyze proxy statistics.
    """
    print(f"{Fore.BLUE}Analyzing proxy statistics (placeholder)...{Style.RESET_ALL}")
    logger.info("Analyzing proxy statistics (placeholder).")
    # Implement logic to read logs/exports and present statistics
    print(f"{Fore.GREEN}Proxy statistics analysis completed (placeholder).{Style.RESET_ALL}")

def setup_auto_update():
    """
    Placeholder for a function to set up automatic updates for the scanner.
    """
    print(f"{Fore.BLUE}Setting up auto-update (placeholder)...{Style.RESET_ALL}")
    logger.info("Setting up auto-update (placeholder).")
    # Implement auto-update setup logic here
    print(f"{Fore.GREEN}Auto-update setup completed (placeholder).{Style.RESET_ALL}")

# ===========================================================================
# MAIN ENTRY POINT AND ARGUMENT PARSING
# ===========================================================================

# This function will parse command-line arguments and fallback to config.py values
def get_args():
    parser = argparse.ArgumentParser(description="RapidProxyScan - Advanced Proxy Scanner")
    # Add arguments corresponding to config.py constants
    parser.add_argument("--check-interval", type=int, default=config.CHECK_INTERVAL,
                        help="How often to check for new proxies (in seconds)")
    parser.add_argument("--connection-limit", type=int, default=config.CONNECTION_LIMIT,
                        help="Maximum concurrent connections for proxy testing")
    parser.add_argument("--validation-rounds", type=int, default=config.VALIDATION_ROUNDS,
                        help="Number of validation tests per proxy")
    parser.add_argument("--validation-mode", type=str, default=config.VALIDATION_MODE,
                        choices=['any', 'majority', 'all'],
                        help="Validation mode: 'any', 'majority', or 'all'")
    parser.add_argument("--timeout", type=float, default=config.TIMEOUT,
                        help="Connection timeout in seconds")
    parser.add_argument("--check-anonymity", action=argparse.BooleanOptionalAction, default=config.CHECK_ANONYMITY,
                        help="Check proxy anonymity level")
    parser.add_argument("--force-fetch", action=argparse.BooleanOptionalAction, default=config.FORCE_FETCH,
                        help="Force fetch proxy lists on each cycle")
    parser.add_argument("--verbose", action=argparse.BooleanOptionalAction, default=config.VERBOSE,
                        help="Enable verbose logging")
    parser.add_argument("--single-run", action=argparse.BooleanOptionalAction, default=config.SINGLE_RUN,
                        help="Run once and exit")

    # Add arguments for other parameters that ProxyScanManager.__init__ expects
    parser.add_argument("--proxy-sources", type=str, nargs='*', default=config.PROXY_SOURCES,
                        help="List of proxy sources URLs/paths (space-separated)")
    parser.add_argument("--proxy-test-workers", type=int, default=config.CONNECTION_LIMIT, # Using CONNECTION_LIMIT as a sensible default
                        help="Number of concurrent workers for testing proxies")
    parser.add_argument("--proxy-fetch-interval", type=int, default=config.CHECK_INTERVAL * 2, # Using a multiple of CHECK_INTERVAL
                        help="Interval in seconds to fetch new proxy lists")
    parser.add_argument("--proxy-test-timeout", type=float, default=config.TIMEOUT,
                        help="Timeout for individual proxy tests")
    parser.add_argument("--proxy-test-retries", type=int, default=config.VALIDATION_ROUNDS,
                        help="Number of retries for a failed proxy test")
    parser.add_argument("--max-proxies-to-keep", type=int, default=10000,
                        help="Maximum number of proxies to store in memory")
    parser.add_argument("--proxy-refresh-min-interval", type=int, default=300,
                        help="Minimum interval before re-testing a proxy")
    parser.add_argument("--test-url", type=str, default="http://ip-api.com/json",
                        help="URL to test proxy connectivity")
    parser.add_argument("--export-interval", type=int, default=300,
                        help="Interval in seconds to export verified proxies")
    parser.add_argument("--max-fetch-attempts", type=int, default=5,
                        help="Max attempts to fetch a proxy list")
    parser.add_argument("--fetch-retry-delay", type=int, default=5,
                        help="Delay between fetch retries")

    args = parser.parse_args()
    return args

def run_scanner(check_interval: int = None,
                connection_limit: int = None,
                validation_rounds: int = None,
                validation_mode: str = None,
                timeout: float = None,
                check_anonymity: bool = None,
                force_fetch: bool = None,
                verbose: bool = None,
                single_run: bool = None,
                # Parameters that ProxyScanManager.__init__ expects
                proxy_sources: List[str] = None,
                proxy_test_workers: int = None,
                proxy_fetch_interval: int = None,
                proxy_test_timeout: float = None,
                proxy_test_retries: int = None,
                max_proxies_to_keep: int = None,
                proxy_refresh_min_interval: int = None,
                test_url: str = None,
                export_interval: int = None,
                max_fetch_attempts: int = None,
                fetch_retry_delay: int = None
                ):
    """
    Main function to run the proxy scanner.
    It can be called with explicit arguments (e.g., from config.py)
    or without arguments (e.g., when rapidproxyscan.py is run directly).
    """
    # Default to config.py values if arguments are not provided
    # This allows config.py to explicitly pass args, or rapidproxyscan.py
    # to get them from CLI or config.py defaults via get_args().
    check_interval = check_interval if check_interval is not None else config.CHECK_INTERVAL
    connection_limit = connection_limit if connection_limit is not None else config.CONNECTION_LIMIT
    validation_rounds = validation_rounds if validation_rounds is not None else config.VALIDATION_ROUNDS
    validation_mode = validation_mode if validation_mode is not None else config.VALIDATION_MODE
    timeout = timeout if timeout is not None else config.TIMEOUT
    check_anonymity = check_anonymity if check_anonymity is not None else config.CHECK_ANONYMITY
    force_fetch = force_fetch if force_fetch is not None else config.FORCE_FETCH
    verbose = verbose if verbose is not None else config.VERBOSE
    single_run = single_run if single_run is not None else config.SINGLE_RUN

    proxy_sources = proxy_sources if proxy_sources is not None else config.PROXY_SOURCES
    proxy_test_workers = proxy_test_workers if proxy_test_workers is not None else config.CONNECTION_LIMIT
    proxy_fetch_interval = proxy_fetch_interval if proxy_fetch_interval is not None else config.CHECK_INTERVAL * 2
    proxy_test_timeout = proxy_test_timeout if proxy_test_timeout is not None else config.TIMEOUT
    proxy_test_retries = proxy_test_retries if proxy_test_retries is not None else config.VALIDATION_ROUNDS
    max_proxies_to_keep = max_proxies_to_keep if max_proxies_to_keep is not None else 10000
    proxy_refresh_min_interval = proxy_refresh_min_interval if proxy_refresh_min_interval is not None else 300
    test_url = test_url if test_url is not None else "http://ip-api.com/json"
    export_interval = export_interval if export_interval is not None else 300
    max_fetch_attempts = max_fetch_attempts if max_fetch_attempts is not None else 5
    fetch_retry_delay = fetch_retry_delay if fetch_retry_delay is not None else 5

    scanner = ProxyScanManager(
        check_interval=check_interval,
        connection_limit=connection_limit,
        validation_rounds=validation_rounds,
        validation_mode=validation_mode,
        timeout=timeout,
        check_anonymity=check_anonymity,
        force_fetch=force_fetch,
        verbose=verbose,
        single_run=single_run,
        proxy_sources=proxy_sources,
        proxy_test_workers=proxy_test_workers,
        proxy_fetch_interval=proxy_fetch_interval,
        proxy_test_timeout=proxy_test_timeout,
        proxy_test_retries=proxy_test_retries,
        max_proxies_to_keep=max_proxies_to_keep,
        proxy_refresh_min_interval=proxy_refresh_min_interval,
        test_url=test_url,
        export_interval=export_interval,
        max_fetch_attempts=max_fetch_attempts,
        fetch_retry_delay=fetch_retry_delay
    )
    asyncio.run(scanner.run())

if __name__ == "__main__":
    # This block will be executed if rapidproxyscan.py is run directly.
    # It will parse CLI arguments, defaulting to values from config.py.

    # Handle utility functions directly from command line first
    if len(sys.argv) > 1:
        if "--speed-test" in sys.argv:
            idx = sys.argv.index("--speed-test")
            if idx + 1 < len(sys.argv):
                run_speed_test(sys.argv[idx + 1])
            else:
                print(f"{Fore.RED}Error: --speed-test requires a file path.{Style.RESET_ALL}")
            sys.exit(0)

        if "--clean-old" in sys.argv:
            clean_old_files()
            sys.exit(0)

        if "--analyze" in sys.argv:
            analyze_proxy_stats()
            sys.exit(0)

        if "--setup-auto-update" in sys.argv:
            setup_auto_update()
            sys.exit(0)

    # If no utility function is called, proceed with scanner
    args = get_args()

    # Call run_scanner with arguments parsed from CLI (defaulting to config.py values)
    run_scanner(
        check_interval=args.check_interval,
        connection_limit=args.connection_limit,
        validation_rounds=args.validation_rounds,
        validation_mode=args.validation_mode,
        timeout=args.timeout,
        check_anonymity=args.check_anonymity,
        force_fetch=args.force_fetch,
        verbose=args.verbose,
        single_run=args.single_run,
        proxy_sources=args.proxy_sources,
        proxy_test_workers=args.proxy_test_workers,
        proxy_fetch_interval=args.proxy_fetch_interval,
        proxy_test_timeout=args.proxy_test_timeout,
        proxy_test_retries=args.proxy_test_retries,
        max_proxies_to_keep=args.max_proxies_to_keep,
        proxy_refresh_min_interval=args.proxy_refresh_min_interval,
        test_url=args.test_url,
        export_interval=args.export_interval,
        max_fetch_attempts=args.max_fetch_attempts,
        fetch_retry_delay=args.fetch_retry_delay
    )
