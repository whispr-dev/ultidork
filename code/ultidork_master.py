#!/usr/bin/env python3
"""
OmniDork Master Controller
=========================
Unified interface for all OmniDork components
"""

import asyncio
import argparse
import sys
import os
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import configurations and components
from integrated_config import get_config, INTEGRATED_CONFIG
from extended_user_agents import get_random_user_agent
from proxy_starter_list import get_elite_sources, get_test_endpoints, get_all_sources
from crawl_targets import get_targets_by_category, get_all_targets

from scanner_interface import UnifiedScanner
from quantum_osint_integration_bridge import QuantumOSINTBridge

# Import scanner components
try:
    from rapidproxyscan import ProxyScanManager
    RAPIDPROXY_AVAILABLE = True
except ImportError:
    RAPIDPROXY_AVAILABLE = False
    print(f"{Fore.YELLOW}[!] RapidProxyScan not available{Style.RESET_ALL}")

# Use scanner_interface for OmniDork
try:
    from scanner_interface import UnifiedScanner as OmniDorkScanner
    OMNIDORK_AVAILABLE = True
except ImportError:
    OMNIDORK_AVAILABLE = False
    print(f"{Fore.YELLOW}[!] OmniDork scanner not available{Style.RESET_ALL}")

# Create viewbot wrapper
try:
    from core.bot_worker import BotWorker
    from core.account import AccountManager
    from core.proxy_manager import ProxyManager
    VIEWBOT_AVAILABLE = True
    
    async def viewbot_main(target: str, mode: str = "view", count: int = 1):
        """Simple viewbot wrapper function"""
        account_mgr = AccountManager()
        proxy_mgr = ProxyManager()
        
        worker = BotWorker(
            mode=mode,
            target=target,
            count=count,
            proxy=proxy_mgr.get_proxy(),
            account_mgr=account_mgr
        )
        worker.start()
        worker.join()
        
except ImportError as e:
    VIEWBOT_AVAILABLE = False
    print(f"{Fore.YELLOW}[!] Viewbot not available: {e}{Style.RESET_ALL}")


class OmniDorkMaster:
    """Main scanner interface combining all capabilities"""

    def __init__(self, config: dict = None):
        self.config = config or get_config()
        self.rapidproxy_manager = None
        self.omnidork_scanner = None

        # Ensure proper config structure
        if 'quantum_osint_bridge' not in self.config:
            self.config['quantum_osint_bridge'] = {}
        if 'scanner' not in self.config['quantum_osint_bridge']:
            self.config['quantum_osint_bridge']['scanner'] = {'timeout': 30}

        # Initialize quantum OSINT bridge
        self.quantum_bridge = QuantumOSINTBridge(self.config['quantum_osint_bridge'])

        # Initialize RapidProxyScanManager if available
        if RAPIDPROXY_AVAILABLE:
            try:
                # Fix the config access
                proxy_config = self.config.get('rapidproxy', {})
                self.rapidproxy_manager = ProxyScanManager(
                    check_interval=proxy_config.get('check_interval', 30),
                    connection_limit=proxy_config.get('connection_limit', 50),
                    validation_rounds=proxy_config.get('validation_rounds', 3),
                    validation_mode=proxy_config.get('validation_mode', 'majority'),
                    timeout=proxy_config.get('timeout', 5.0),
                    check_anonymity=proxy_config.get('check_anonymity', True),
                    force_fetch=proxy_config.get('force_fetch', False),
                    verbose=proxy_config.get('verbose', False),
                    single_run=proxy_config.get('single_run', False),
                    proxy_sources=get_all_sources(),
                    proxy_test_workers=proxy_config.get('proxy_test_workers', 50),
                    proxy_fetch_interval=proxy_config.get('proxy_fetch_interval', 60),
                    proxy_test_timeout=proxy_config.get('proxy_test_timeout', 5.0),
                    proxy_test_retries=proxy_config.get('proxy_test_retries', 3),
                    max_proxies_to_keep=proxy_config.get('max_proxies_to_keep', 1000),
                    proxy_refresh_min_interval=proxy_config.get('proxy_refresh_min_interval', 300),
                    test_url=get_test_endpoints("fastest")[0] if get_test_endpoints("fastest") else "http://httpbin.org/ip",
                    export_interval=proxy_config.get('export_interval', 300),
                    max_fetch_attempts=proxy_config.get('max_fetch_attempts', 5),
                    fetch_retry_delay=proxy_config.get('fetch_retry_delay', 5)
                )
            except Exception as e:
                print(f"{Fore.RED}[!] Failed to initialize RapidProxyScan: {e}{Style.RESET_ALL}")
                self.rapidproxy_manager = None

        # Initialize OmniDork Scanner
        if OMNIDORK_AVAILABLE:
            try:
                self.omnidork_scanner = OmniDorkScanner(self.config)
            except Exception as e:
                print(f"{Fore.RED}[!] Failed to initialize OmniDork scanner: {e}{Style.RESET_ALL}")
                self.omnidork_scanner = None

    async def banner(self):
        """Display ASCII banner and system info."""
        banner_text = r"""
             _         || _____            
      __   _| ||     _ ||/ / \ \            
     | |  | | ||_   ( )||| |  \ \  _   _   __  __
     | |  | | '| |__| |||| |  | |/ _ \| )_ | |/ /
     | |__| | || | || |||| |__/ |     |  _)| || |<
      \____/|_| \__||_||||_____/ \___/|_|  |_|\_\

            Unified Scanner & Evasion Framework
    """
        print(f"{Fore.CYAN}{banner_text}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] OmniDork Master Controller Initialized{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Python Version: {sys.version.split()[0]}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Platform: {sys.platform}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] RapidProxyScan: {'Available' if RAPIDPROXY_AVAILABLE else 'Not Available'}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] OmniDork Scanner: {'Available' if OMNIDORK_AVAILABLE else 'Not Available'}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Viewbot: {'Available' if VIEWBOT_AVAILABLE else 'Not Available'}{Style.RESET_ALL}")
        print("-" * 60)

    async def get_proxies(self, force_refresh=False):
        """Acquire and test proxies via RapidProxyScan."""
        if not self.rapidproxy_manager:
            print(f"{Fore.RED}[!] RapidProxyScan manager not initialized{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}[*] Fetching and testing proxies...{Style.RESET_ALL}")
        try:
            await self.rapidproxy_manager.initialize()
            print(f"{Fore.GREEN}[+] Proxy manager initialized{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error fetching proxies: {e}{Style.RESET_ALL}")
            if self.config.get('verbose', False):
                traceback.print_exc()

    async def run_omnidork_scan(self, target: str, mode: str):
        """Run OmniDork scanner on a target."""
        if not self.omnidork_scanner:
            print(f"{Fore.RED}[!] OmniDork scanner not available{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}[*] Running OmniDork scan (mode: {mode}) on: {target}{Style.RESET_ALL}")
        try:
            await self.omnidork_scanner.load_targets(target)
            await self.omnidork_scanner.initialize_proxies()
            await self.omnidork_scanner.scan_all_targets()
            
            # Generate report
            report_file = f'omnidork_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            self.omnidork_scanner.generate_report(report_file)
            print(f"{Fore.GREEN}[+] OmniDork scan complete. Report: {report_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error during OmniDork scan: {e}{Style.RESET_ALL}")
            if self.config.get('verbose', False):
                traceback.print_exc()

    async def run_integrated_scan(self, target: str):
        """Run a full integrated scan combining all capabilities."""
        print(f"{Fore.CYAN}[*] Running full integrated scan on: {target}{Style.RESET_ALL}")
        
        results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "omnidork_results": None,
            "quantum_results": None,
            "errors": []
        }
        
        try:
            # Run OmniDork Scanner
            if self.omnidork_scanner:
                print(f"{Fore.CYAN}[*] Running OmniDork Scanner...{Style.RESET_ALL}")
                await self.omnidork_scanner.load_targets(target)
                await self.omnidork_scanner.initialize_proxies()
                await self.omnidork_scanner.scan_all_targets()
                results["omnidork_results"] = self.omnidork_scanner.results

            # Run Quantum OSINT Bridge
            print(f"{Fore.CYAN}[*] Running Quantum OSINT Bridge...{Style.RESET_ALL}")
            await self.quantum_bridge.initialize()
            quantum_scan_results = await self.quantum_bridge.quantum_scan_target(target)
            results["quantum_results"] = quantum_scan_results
            
            print(f"{Fore.GREEN}[+] Integrated scan complete for {target}{Style.RESET_ALL}")
            
        except Exception as e:
            error_msg = f"Error during integrated scan: {e}"
            print(f"{Fore.RED}[!] {error_msg}{Style.RESET_ALL}")
            results["errors"].append(error_msg)
            if self.config.get('verbose', False):
                traceback.print_exc()
        
        # Save integrated results
        report_file = f"integrated_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{Fore.GREEN}[+] Integrated report saved: {report_file}{Style.RESET_ALL}")

    async def run_viewbot(self, target: str, mode: str = "view", count: int = 1):
        """Run viewbot on a target."""
        if not VIEWBOT_AVAILABLE:
            print(f"{Fore.RED}[!] Viewbot not available{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}[*] Running viewbot on: {target} (mode: {mode}, count: {count}){Style.RESET_ALL}")
        try:
            await viewbot_main(target=target, mode=mode, count=count)
            print(f"{Fore.GREEN}[+] Viewbot run complete for {target}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error during viewbot run: {e}{Style.RESET_ALL}")
            if self.config.get('verbose', False):
                traceback.print_exc()

    async def interactive_menu(self):
        """Interactive menu for OmniDork operations."""
        while True:
            print(f"\n{Fore.BLUE}{'='*40}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}  OmniDork Interactive Menu{Style.RESET_ALL}")
            print(f"{Fore.BLUE}{'='*40}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}1. Run Proxy Scanner (Update Proxy Pool){Style.RESET_ALL}")
            print(f"{Fore.CYAN}2. Run OmniDork Quick Scan (OSINT){Style.RESET_ALL}")
            print(f"{Fore.CYAN}3. Run OmniDork Deep Scan (OSINT + Crawl){Style.RESET_ALL}")
            print(f"{Fore.CYAN}4. Run Full Integrated Scan{Style.RESET_ALL}")
            print(f"{Fore.CYAN}5. Run Viewbot{Style.RESET_ALL}")
            print(f"{Fore.CYAN}6. System Status{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}7. Exit{Style.RESET_ALL}")
            print(f"{Fore.BLUE}{'='*40}{Style.RESET_ALL}")

            choice = input(f"{Fore.GREEN}Enter your choice: {Style.RESET_ALL}").strip()

            if choice == '1':
                await self.get_proxies(force_refresh=True)
            elif choice == '2':
                target = input(f"{Fore.GREEN}Enter target domain: {Style.RESET_ALL}").strip()
                if target:
                    await self.run_omnidork_scan(target, mode="osint")
            elif choice == '3':
                target = input(f"{Fore.GREEN}Enter target domain: {Style.RESET_ALL}").strip()
                if target:
                    await self.run_omnidork_scan(target, mode="full")
            elif choice == '4':
                target = input(f"{Fore.GREEN}Enter target domain: {Style.RESET_ALL}").strip()
                if target:
                    await self.run_integrated_scan(target)
            elif choice == '5':
                target = input(f"{Fore.GREEN}Enter target URL: {Style.RESET_ALL}").strip()
                mode = input(f"{Fore.GREEN}Enter mode (medium/youtube/vote) [view]: {Style.RESET_ALL}").strip() or "view"
                count = int(input(f"{Fore.GREEN}Enter count [1]: {Style.RESET_ALL}").strip() or "1")
                if target:
                    await self.run_viewbot(target, mode, count)
            elif choice == '6':
                await self.check_system()
            elif choice == '7':
                print(f"{Fore.YELLOW}Exiting OmniDork Master Controller. Happy hunting!{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}[!] Invalid option. Please try again.{Style.RESET_ALL}")

    async def check_system(self):
        """Check system status."""
        print(f"\n{Fore.CYAN}=== System Status ==={Style.RESET_ALL}")
        print(f"RapidProxyScan: {'✓' if self.rapidproxy_manager else '✗'}")
        print(f"OmniDork Scanner: {'✓' if self.omnidork_scanner else '✗'}")
        print(f"Viewbot: {'✓' if VIEWBOT_AVAILABLE else '✗'}")
        print(f"Quantum Bridge: {'✓' if self.quantum_bridge else '✗'}")
        
        if self.rapidproxy_manager:
            try:
                pool_size = len(self.rapidproxy_manager.proxies) if hasattr(self.rapidproxy_manager, 'proxies') else 0
                print(f"Proxy Pool Size: {pool_size}")
            except:
                print("Proxy Pool Size: Unknown")


async def main_cli():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OmniDork Master Controller - Unified OSINT & Evasion"
    )
    parser.add_argument('target', nargs='?', help='Target domain/IP for scan')
    parser.add_argument('--mode', choices=['quick', 'deep', 'full', 'proxy', 'viewbot'], 
                       default='quick', help='Scan mode')
    parser.add_argument('--config', help='Path to custom configuration JSON file')
    parser.add_argument('--no-banner', action='store_true', help='Suppress ASCII banner')
    parser.add_argument('--proxy-refresh', action='store_true', help='Force proxy refresh before scan')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # Load configuration
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to load config: {e}{Style.RESET_ALL}")

    # Initialize master controller
    master = OmniDorkMaster(config)

    # Display banner
    if not args.no_banner:
        await master.banner()

    # Handle command line mode
    if args.target:
        if args.proxy_refresh:
            await master.get_proxies(force_refresh=True)
            
        if args.mode == 'quick':
            await master.run_omnidork_scan(args.target, mode="osint")
        elif args.mode == 'deep':
            await master.run_omnidork_scan(args.target, mode="full")
        elif args.mode == 'full':
            await master.run_integrated_scan(args.target)
        elif args.mode == 'proxy':
            await master.get_proxies(force_refresh=True)
        elif args.mode == 'viewbot':
            await master.run_viewbot(args.target)
    else:
        # Interactive mode
        await master.interactive_menu()


if __name__ == "__main__":
    try:
        asyncio.run(main_cli())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Operation cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Fatal error: {e}{Style.RESET_ALL}")
        traceback.print_exc()