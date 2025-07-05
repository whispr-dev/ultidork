#!/usr/bin/env python3
"""
OmniDork Unified Scanner Interface
==================================
Integrates quantum OSINT, proxy scanning, and evasion capabilities
"""

import asyncio
import argparse
import json
import sys
import os
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import requests
import re
from colorama import Fore, Style, init
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from ultidork.lookyloo_capture import capture_url

# Initialize colorama
init(autoreset=True)

# Add project paths
sys.path.append(str(Path(__file__).parent))

# Import OmniDork components
# (Ensure these modules exist and contain the classes they claim to)
try:
    from omnidork.dork_engine import DorkEngine
except ImportError:
    class DorkEngine: # Dummy class if not found
        def __init__(self, proxies: List[str]):
            print(f"{Fore.YELLOW}[!] DorkEngine not found. Using dummy. Proxies: {proxies}{Style.RESET_ALL}")
            self.proxies = proxies
        async def search(self, dork: str, target: str, max_results: int = 10, proxy: Optional[str] = None) -> List[Dict]:
            print(f"{Fore.YELLOW}[!] Dummy DorkEngine search for '{dork}' on '{target}' (proxy: {proxy}){Style.RESET_ALL}")
            return []

try:
    from omnidork.vulnerability_matcher import VulnerabilityMatcher
except ImportError:
    class VulnerabilityMatcher: # Dummy class if not found
        def __init__(self):
            print(f"{Fore.YELLOW}[!] VulnerabilityMatcher not found. Using dummy.{Style.RESET_ALL}")
        async def analyze_findings(self, *args, **kwargs) -> List[Dict]:
            print(f"{Fore.YELLOW}[!] Dummy VulnerabilityMatcher analyze_findings{Style.RESET_ALL}")
            return []
        def analyze_content(self, *args, **kwargs) -> List[Dict]:
            print(f"{Fore.YELLOW}[!] Dummy VulnerabilityMatcher analyze_content{Style.RESET_ALL}")
            return []

try:
    from omnidork.crawler import Crawler
except ImportError:
    class Crawler: # Dummy class if not found
        def __init__(self, proxy_scanner: Any, concurrent_requests: int, max_depth: int):
            print(f"{Fore.YELLOW}[!] Crawler not found. Using dummy.{Style.RESET_ALL}")
            self.proxy_scanner = proxy_scanner
        async def crawl(self, url: str, depth: int = 2, proxy: Optional[str] = None) -> List[Dict]:
            print(f"{Fore.YELLOW}[!] Dummy Crawler crawl for '{url}' (proxy: {proxy}){Style.RESET_ALL}")
            return []

try:
    # Assuming ProxyScanner is not the same as ProxyScanManager from rapidproxyscan
    from omnidork.proxy_scanner import ProxyScanner as OmniProxyScanner
except ImportError:
    class OmniProxyScanner: # Dummy class if not found
        def __init__(self):
            print(f"{Fore.YELLOW}[!] OmniProxyScanner not found. Using dummy.{Style.RESET_ALL}")

try:
    from omnidork.quantum_osint import QuantumScorer
except ImportError:
    class QuantumScorer: # Dummy class if not found
        def __init__(self, *args):
            print(f"{Fore.YELLOW}[!] QuantumScorer not found. Using dummy.{Style.RESET_ALL}")
        def calculate_score(self, *args, **kwargs) -> float:
            return 0.0


# Import RapidProxyScan components
from rapidproxyscan import ProxyScanManager, ProxyTester, ProxyInfo # Import ProxyInfo too if needed for detailed types

# Import core components (ensure these are in D:\code\ultidorki\code\core\)
from core.proxy_manager import ProxyManager
from core.browser import BrowserController
from core.captcha_solver import CaptchaSolver # Use captcha_solver for consistency

# Import utilities
try:
    from utils.paywall_buster import PaywallBuster
except ImportError:
    class PaywallBuster: # Dummy class if not found
        def __init__(self):
            print(f"{Fore.YELLOW}[!] PaywallBuster not found. Using dummy.{Style.RESET_ALL}")
        async def fetch_article_text(self, url: str, proxy: Optional[str] = None) -> Optional[str]:
            print(f"{Fore.YELLOW}[!] Dummy PaywallBuster fetch for '{url}' (proxy: {proxy}){Style.RESET_ALL}")
            return None


class UnifiedScanner:
    """Main scanner interface combining all capabilities"""

    def __init__(self, config: Dict):
        self.config = config
        self.targets = []
        self.proxies: List[Dict[str, Any]] = [] # Now a list of detailed proxy dictionaries
        self.current_proxy_index = 0 # To track proxy rotation
        self.results = {}

        # Initialize components
        self.init_components()

    def init_components(self):
        """Initialize all scanner components"""
        print(f"{Fore.CYAN}[*] Initializing scanner components...{Style.RESET_ALL}")

        # Quantum OSINT components
        self.quantum_scorer = QuantumScorer(1000)
        self.vulnerability_matcher = VulnerabilityMatcher()
        # DorkEngine initialized after proxies are ready in initialize_proxies

        # Proxy components - ProxyManager is for high-level management, ProxyScanManager for scanning.
        self.proxy_manager = ProxyManager(
            refresh_interval_min=self.config.get('proxy_refresh_interval', 15),
            max_proxies=self.config.get('max_proxies', 1000),
            disable_refresh=self.config.get('disable_proxy_refresh', False)
        )

        # Browser automation
        self.browser_controller = BrowserController(
            headless=self.config.get('headless', True)
        )

        # Evasion components
        self.captcha_solver = None
        if self.config.get('captcha_api_key'):
            self.captcha_solver = CaptchaSolver(self.config['captcha_api_key'])

        self.paywall_buster = PaywallBuster() # PaywallBuster should use browser/proxy manager internally

        print(f"{Fore.GREEN}[+] Components initialized{Style.RESET_ALL}")

    async def load_targets(self, target_input: str):
        """Load targets from various input formats"""
        targets = set()

        # Check if it's a file
        if os.path.isfile(target_input):
            print(f"{Fore.YELLOW}[*] Loading targets from file: {target_input}{Style.RESET_ALL}")
            with open(target_input, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        targets.update(self.parse_target_line(line))
        else:
            # Process as direct input
            targets.update(self.parse_target_line(target_input))

        self.targets = list(targets)
        print(f"{Fore.GREEN}[+] Loaded {len(self.targets)} targets{Style.RESET_ALL}")

    def parse_target_line(self, line: str) -> Set[str]:
        """Parse target input supporting wildcards and ranges"""
        targets = set()

        # Remove protocol if present
        line = re.sub(r'^https?://', '', line)

        # Handle wildcards (*.example.com)
        if '*' in line:
            # For now, just remove the wildcard - in production, you'd enumerate subdomains
            base_domain = line.replace('*.', '')
            targets.add(base_domain)
            print(f"{Fore.YELLOW}[!] Wildcard detected. Would enumerate subdomains for: {base_domain}{Style.RESET_ALL}")

        # Handle CIDR notation (192.168.1.0/24)
        elif '/' in line and re.match(r'\d+\.\d+\.\d+\.\d+/\d+', line):
            print(f"{Fore.YELLOW}[!] CIDR range detected: {line}. Would expand to IPs.{Style.RESET_ALL}")
            targets.add(line.split('/')[0])  # For now, just use the base IP

        # Handle port ranges (example.com:80-443)
        elif ':' in line and '-' in line.split(':')[1]:
            host, port_range = line.split(':')
            start_port, end_port = map(int, port_range.split('-'))
            for port in range(start_port, end_port + 1):
                targets.add(f"{host}:{port}")
        else:
            targets.add(line)

        return targets

    async def initialize_proxies(self):
        """Initialize and validate proxy pool using RapidProxyScanManager."""
        print(f"{Fore.CYAN}[*] Initializing proxy pool with RapidProxyScan...{Style.RESET_ALL}")

        proxy_scan_manager = ProxyScanManager(
            check_interval=30,
            connection_limit=self.config.get('threads', 50), # Use general threads setting if available
            validation_rounds=3,
            validation_mode='majority',
            timeout=5.0,
            check_anonymity=True,
            force_fetch=True,
            verbose=self.config.get('verbose', False),
            single_run=True, # Run once to get initial proxies
            proxy_sources=self.config.get('proxy_sources', []),
            proxy_test_workers=self.config.get('threads', 50), # Use general threads setting
            proxy_fetch_interval=60,
            proxy_test_timeout=5.0,
            proxy_test_retries=3,
            max_proxies_to_keep=self.config.get('max_proxies', 1000),
            proxy_refresh_min_interval=300,
            test_url=self.config.get('proxy_test_url', 'http://mail.whispr.dev:9876/'), # Use your specific endpoint
            export_interval=300,
            max_fetch_attempts=5,
            fetch_retry_delay=5
        )

        try:
            await proxy_scan_manager.initialize()
            await proxy_scan_manager.start_scanning_loop()

            # Retrieve the verified proxies from the ProxyScanManager
            # self.proxies will now store the detailed ProxyInfo objects
            # Filter for usable proxies and store their detailed dict representations
            self.proxies = [
                p.to_dict() for p in proxy_scan_manager.proxies.values()
                if p.is_usable and p.security_level != "low" # Filter out low-security ones for dorking
            ]
            self.proxies.sort(key=lambda x: x['latency_ms']) # Sort by latency for preferred use

            # Initialize DorkEngine with a list of proxy dicts
            if self.proxies:
                # DorkEngine might expect a simpler list of "http://host:port" or dicts
                # Adjust based on your DorkEngine's __init__
                dork_proxies = [f"{p['protocol']}://{p['host']}:{p['port']}" for p in self.proxies]
                self.dork_engine = DorkEngine(dork_proxies) # Assuming DorkEngine takes a list of proxy strings
            else:
                print(f"{Fore.YELLOW}[!] No usable proxies found for DorkEngine. Running without proxies.{Style.RESET_ALL}")
                self.dork_engine = DorkEngine([]) # Initialize without proxies

        except Exception as e:
            print(f"{Fore.RED}[!] RapidProxyScan integration failed: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Falling back to running DorkEngine without specific proxies.{Style.RESET_ALL}")
            self.dork_engine = DorkEngine([]) # Fallback if proxy scanning fails

        print(f"{Fore.GREEN}[+] Proxy pool initialized with {len(self.proxies)} usable proxies.{Style.RESET_ALL}")

    async def main():
        parser = argparse.ArgumentParser(
        description="OmniDork Unified Scanner - Quantum OSINT + Advanced Evasion"
    )

    # Target input
    parser.add_argument(
        'target',
        help='Target domain/IP or file containing targets. Supports wildcards (*) and CIDR ranges'
    )

    # Scanning options
    parser.add_argument('--dorks', nargs='+', help='Custom Google dorks to use')
    parser.add_argument('--no-dorks', action='store_true', help='Disable dorking')
    parser.add_argument('--no-crawl', action='store_true', help='Disable crawling')
    parser.add_argument('--depth', type=int, default=2, help='Crawler depth (default: 2)')
    parser.add_argument('--threads', type=int, default=10, help='Concurrent threads (default: 10)')

    # Proxy options
    parser.add_argument('--proxy-file', help='File containing proxies')
    parser.add_argument('--no-proxy-refresh', action='store_true', help='Disable automatic proxy refresh')
    parser.add_argument('--proxy-test-url', default='http://mail.whispr.dev:9876/', help='Custom proxy test endpoint')
    parser.add_argument('--max-proxies', type=int, default=1000, help='Maximum proxies to maintain')

    # Evasion options
    parser.add_argument('--captcha-key', help='2Captcha API key for solving CAPTCHAs')
    parser.add_argument('--bypass-paywall', action='store_true', help='Enable paywall bypass')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browsers in headless mode')

    # Protocol options
    parser.add_argument('--http-only', action='store_true', help='Only scan HTTP (skip HTTPS)')
    parser.add_argument('--no-https', action='store_true', dest='https_only', help='Only scan HTTPS (skip HTTP) - changed name for clarity')

    # Output options
    parser.add_argument('-o', '--output', default='omnidork_report.json', help='Output report file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

def fetch_proxy_list(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.text.strip():
            print(f"[+] Proxies loaded from: {url}")
            return response.text.splitlines()
    except Exception as e:
        print(f"[!] Failed to fetch proxies from {url}: {e}")
    return []

async def main():
    parser = argparse.ArgumentParser(
        description="OmniDork Unified Scanner - Quantum OSINT + Advanced Evasion"
    )

    # Target input
    parser.add_argument(
        'target',
        help='Target domain/IP or file containing targets. Supports wildcards (*) and CIDR ranges'
    )

    # Scanning options
    parser.add_argument('--dorks', nargs='+', help='Custom Google dorks to use')
    parser.add_argument('--no-dorks', action='store_true', help='Disable dorking')
    parser.add_argument('--no-crawl', action='store_true', help='Disable crawling')
    parser.add_argument('--depth', type=int, default=2, help='Crawler depth (default: 2)')
    parser.add_argument('--threads', type=int, default=10, help='Concurrent threads (default: 10)')

    # Proxy options
    parser.add_argument('--proxy-file', help='File containing proxies')
    parser.add_argument('--no-proxy-refresh', action='store_true', help='Disable automatic proxy refresh')
    parser.add_argument('--proxy-test-url', default='http://mail.whispr.dev:9876/', help='Custom proxy test endpoint')
    parser.add_argument('--max-proxies', type=int, default=1000, help='Maximum proxies to maintain')

    # Evasion options
    parser.add_argument('--captcha-key', help='2Captcha API key for solving CAPTCHAs')
    parser.add_argument('--bypass-paywall', action='store_true', help='Enable paywall bypass')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browsers in headless mode')

    # Protocol options
    parser.add_argument('--http-only', action='store_true', help='Only scan HTTP (skip HTTPS)')
    parser.add_argument('--no-https', action='store_true', dest='https_only', help='Only scan HTTPS (skip HTTP) - changed name for clarity')

    # Output options
    parser.add_argument('-o', '--output', default='omnidork_report.json', help='Output report file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    proxy_sources = [
        'http://list.didsoft.com/get?email=got.girl.camera@gmail.com&pass=3t8q44&pid=http1000&showcountry=no',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http',
    ]

    all_proxies = []
    for src in proxy_sources:
        proxies = fetch_proxy_list(src)
        if proxies:
            all_proxies.extend(proxies)
            if src.startswith("http://list.didsoft.com"):  # Premium, stop after success
                break
        time.sleep(2)  # Optional cooldown between sources

    # Build configuration dict
    config = {
        'enable_dorking': not args.no_dorks,
        'enable_crawling': not args.no_crawl,
        'enable_paywall_bypass': args.bypass_paywall,
        'crawler_depth': args.depth,
        'crawler_threads': args.threads,
        'disable_proxy_refresh': args.no_proxy_refresh,
        'proxy_test_url': args.proxy_test_url,
        'max_proxies': args.max_proxies,
        'captcha_api_key': args.captcha_key,
        'headless': args.headless,
        'check_https': not args.https_only,
        'check_http': not args.http_only,
        'verbose': args.verbose,
        'proxy_sources': proxy_sources,
        # Optionally, you can add 'all_proxies': all_proxies if you want to pre-populate somewhere
    }

    if args.dorks:
        config['dorks'] = args.dorks

    # Run scanner
    scanner = UnifiedScanner(config)

    try:
        # Load targets
        await scanner.load_targets(args.target)

        # Initialize proxies
        await scanner.initialize_proxies()

        # Scan all targets
        await scanner.scan_all_targets()

        # Generate report
        scanner.generate_report(args.output)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Scan interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Fatal error: {e}{Style.RESET_ALL}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
