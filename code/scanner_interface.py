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
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
import re
from colorama import Fore, Style, init

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

    async def scan_target(self, target: str):
        """Perform comprehensive scan on a single target"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Scanning target: {target}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'dork_results': [],
            'vulnerabilities': [],
            'crawl_results': [],
            'paywall_content': [],
            'quantum_score': 0.0
        }

        # Ensure HTTPS support
        protocols = []
        if self.config.get('check_https', True) and not self.config.get('http_only', False):
            protocols.append('https')
        if self.config.get('check_http', True) and not self.config.get('https_only', False):
            protocols.append('http')
        if not protocols: # Fallback if neither is selected
            protocols = ['https', 'http']


        for protocol in protocols:
            full_target = f"{protocol}://{target}"

            # Select a proxy for this target/protocol if available
            proxy_to_use = None
            proxy_info_for_log = {}
            if self.proxies:
                proxy_info_for_log = self.proxies[self.current_proxy_index % len(self.proxies)]
                proxy_to_use = f"{proxy_info_for_log['protocol']}://{proxy_info_for_log['host']}:{proxy_info_for_log['port']}"
                self.current_proxy_index += 1
                print(f"  [>] Using proxy: {proxy_to_use} (Speed: {proxy_info_for_log['speed_rating']}, Security: {proxy_info_for_log['security_level']})")


            # 1. Dork scanning
            if self.config.get('enable_dorking', True):
                print(f"\n{Fore.YELLOW}[*] Running dork scans...{Style.RESET_ALL}")
                # Pass the selected proxy to DorkEngine's search method
                dork_results = await self.run_dork_scan(target, proxy_to_use)
                results['dork_results'].extend(dork_results)

            # 2. Crawling
            if self.config.get('enable_crawling', True):
                print(f"\n{Fore.YELLOW}[*] Crawling {full_target}...{Style.RESET_ALL}")
                # Pass the selected proxy to Crawler
                crawl_results = await self.run_crawler(full_target, proxy_to_use)
                results['crawl_results'].extend(crawl_results)

            # 3. Vulnerability analysis
            print(f"\n{Fore.YELLOW}[*] Analyzing for vulnerabilities...{Style.RESET_ALL}")
            vulnerabilities = await self.analyze_vulnerabilities(target, results)
            results['vulnerabilities'].extend(vulnerabilities)

            # 4. Paywall/content extraction if needed
            if self.config.get('enable_paywall_bypass', True):
                for result in results['crawl_results']:
                    if self.is_paywalled_url(result['url']):
                        print(f"{Fore.YELLOW}[*] Attempting paywall bypass for: {result['url']}{Style.RESET_ALL}")
                        # Pass the selected proxy to bypass_paywall if it supports it
                        content = await self.bypass_paywall(result['url'], proxy_to_use)
                        if content:
                            results['paywall_content'].append({
                                'url': result['url'],
                                'content': content[:1000] + '...'
                            })

        # 5. Calculate quantum score
        results['quantum_score'] = self.calculate_quantum_score(results)

        self.results[target] = results
        return results

    async def run_dork_scan(self, target: str, proxy: Optional[str] = None) -> List[Dict]:
        """Run Google dork scans, optionally using a proxy."""
        dorks = self.config.get('dorks', [
            'inurl:admin',
            'inurl:login',
            'intext:password',
            'filetype:pdf confidential',
            'filetype:xlsx',
            'filetype:sql',
            'inurl:backup',
            'inurl:wp-content',
            'inurl:.git',
            'inurl:api',
            'inurl:v1',
            'inurl:swagger',
            'intext:"api key"',
            'intext:"private key"'
        ])

        all_results = []
        for dork in dorks:
            try:
                print(f"  {Fore.CYAN}[>] Trying dork: {dork}{Style.RESET_ALL}")
                # Ensure DorkEngine.search accepts a 'proxy' argument
                results = await self.dork_engine.search(dork, target, max_results=10, proxy=proxy)
                all_results.extend(results)
                if results:
                    print(f"  {Fore.GREEN}[+] Found {len(results)} results{Style.RESET_ALL}")
            except Exception as e:
                print(f"  {Fore.RED}[!] Dork failed: {e}{Style.RESET_ALL}")

        return all_results

    async def run_crawler(self, url: str, proxy: Optional[str] = None) -> List[Dict]:
        """Run web crawler, optionally using a proxy."""
        crawler = Crawler(
            # Assuming Crawler can take a proxy directly or a proxy manager.
            # If your Crawler expects a ProxyManager object, you'll need to
            # update ProxyManager to be able to return a specific proxy for a single request.
            # For simplicity, if Crawler's __init__ or crawl method takes a proxy string:
            proxy_scanner=self.proxy_manager, # Still passing the manager if it's expected
            concurrent_requests=self.config.get('crawler_threads', 10),
            max_depth=self.config.get('crawler_depth', 2)
        )
        # Assuming Crawler.crawl can take an optional 'proxy' argument
        try:
            results = await crawler.crawl(url, depth=2, proxy=proxy)
            return [r.__dict__ for r in results]
        except Exception as e:
            print(f"  {Fore.RED}[!] Crawler error: {e}{Style.RESET_ALL}")
            return []

    async def analyze_vulnerabilities(self, target: str, scan_results: Dict) -> List[Dict]:
        """Analyze all results for vulnerabilities"""
        findings = await self.vulnerability_matcher.analyze_findings(
            target,
            scan_results.get('dork_results', []),
            [],  # Shodan results
            [],  # URLScan results
            [],  # DNS info
            [],  # JS analysis
            []   # Cloud storage
        )

        # Analyze crawled content
        for crawl_result in scan_results.get('crawl_results', []):
            matches = self.vulnerability_matcher.analyze_content(
                crawl_result.get('url', ''),
                crawl_result.get('content', '')
            )
            findings.extend(matches)

        return findings

    async def bypass_paywall(self, url: str, proxy: Optional[str] = None) -> Optional[str]:
        """Attempt to bypass paywall, optionally using a proxy."""
        try:
            # Assuming PaywallBuster's fetch_article_text can take a 'proxy' argument
            return await self.paywall_buster.fetch_article_text(url, proxy=proxy)
        except Exception as e:
            print(f"  {Fore.RED}[!] Paywall bypass failed: {e}{Style.RESET_ALL}")
            return None

    def is_paywalled_url(self, url: str) -> bool:
        """Check if URL is likely paywalled"""
        paywalled_domains = [
            'medium.com', 'wsj.com', 'nytimes.com', 'ft.com',
            'economist.com', 'bloomberg.com', 'businessinsider.com'
        ]
        return any(domain in url.lower() for domain in paywalled_domains)

    def calculate_quantum_score(self, results: Dict) -> float:
        """Calculate overall quantum score for findings"""
        score = 0.0

        # Score based on vulnerability severity
        for vuln in results.get('vulnerabilities', []):
            severity_scores = {'Critical': 10, 'High': 7, 'Medium': 4, 'Low': 1}
            score += severity_scores.get(vuln.get('severity', 'Low'), 0)

        # Bonus for dork results
        score += len(results.get('dork_results', [])) * 0.5

        # Bonus for successful paywall bypass
        score += len(results.get('paywall_content', [])) * 2

        return min(score, 100.0)  # Cap at 100

    async def scan_all_targets(self):
        """Scan all loaded targets"""
        print(f"\n{Fore.CYAN}[*] Starting scan of {len(self.targets)} targets{Style.RESET_ALL}")

        for i, target in enumerate(self.targets, 1):
            print(f"\n{Fore.YELLOW}[*] Progress: {i}/{len(self.targets)}{Style.RESET_ALL}")
            await self.scan_target(target)

    def generate_report(self, output_file: str):
        """Generate comprehensive report"""
        report = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'targets_scanned': len(self.targets),
                'total_vulnerabilities': sum(len(r.get('vulnerabilities', [])) for r in self.results.values()),
                'proxies_used': len(self.proxies) # This now reflects *usable* proxies
            },
            'results': self.results
        }

        # Save JSON report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate summary
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}SCAN SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        total_vulns = 0
        critical_vulns = 0

        for target, results in self.results.items():
            vulns = results.get('vulnerabilities', [])
            total_vulns += len(vulns)
            critical_vulns += sum(1 for v in vulns if v.get('severity') == 'Critical')

            print(f"\n{Fore.YELLOW}Target: {target}{Style.RESET_ALL}")
            print(f"  Vulnerabilities: {len(vulns)}")
            print(f"  Quantum Score: {results.get('quantum_score', 0):.2f}")
            print(f"  Dork Results: {len(results.get('dork_results', []))}")

        print(f"\n{Fore.GREEN}Total Vulnerabilities Found: {total_vulns}{Style.RESET_ALL}")
        print(f"{Fore.RED}Critical Vulnerabilities: {critical_vulns}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Full report saved to: {output_file}{Style.RESET_ALL}")


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
    parser.add_argument('--proxy-test-url', default='http://mail.whispr.dev:9876/', # Default to YOUR endpoint
                       help='Custom proxy test endpoint')
    parser.add_argument('--max-proxies', type=int, default=1000, help='Maximum proxies to maintain')

    # Evasion options
    parser.add_argument('--captcha-key', help='2Captcha API key for solving CAPTCHAs')
    parser.add_argument('--bypass-paywall', action='store_true', help='Enable paywall bypass')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browsers in headless mode')

    # Protocol options
    parser.add_argument('--http-only', action='store_true', help='Only scan HTTP (skip HTTPS)')
    parser.add_argument('--no-https', action='store_true', dest='https_only', help='Only scan HTTPS (skip HTTP) - changed name for clarity') # NOTE: RENAMED FOR CLARITY
    # parser.add_argument('--https-only', action='store_true', help='Only scan HTTPS (skip HTTP)') # Original line commented out

    # Output options
    parser.add_argument('-o', '--output', default='omnidork_report.json', help='Output report file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Build configuration
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
        'check_https': not args.https_only, # Use the new name here
        'check_http': not args.http_only,
        'verbose': args.verbose,

        def fetch_proxy_list(url):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200 and response.text.strip():
                    print(f"[+] Proxies loaded from: {url}")
                    return response.text.splitlines()
            except Exception as e:
                print(f"[!] Failed to fetch proxies from {url}: {e}")
            return []

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
