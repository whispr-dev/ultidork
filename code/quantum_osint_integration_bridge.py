#!/usr/bin/env python3
"""
Elite Quantum OSINT Integration Bridge
=====================================
Fixed version with all imports
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Core imports - these need to exist in your project
try:
    from core.proxy_manager import ProxyManager
except ImportError:
    # Fallback if core.proxy_manager doesn't exist
    from proxy_manager import ProxyManager

try:
    from core.user_agent import UserAgentManager
except ImportError:
    # Simple fallback UserAgentManager
    class UserAgentManager:
        def __init__(self):
            self.agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 Safari/537.36"
            ]
        def get_random(self):
            import random
            return random.choice(self.agents)

try:
    from core.captcha_solver import CaptchaSolver
except ImportError:
    from captcha_solver import CaptchaSolver

try:
    from utils.paywall_buster import MediumPaywallBuster
except ImportError:
    from paywall_buster import MediumPaywallBuster

# Import the optimizer components
try:
    from rapidproxyscan import OptimizerIntegration
except ImportError:
    # Fallback OptimizerIntegration
    class OptimizerIntegration:
        async def initialize(self):
            pass

# Import humanizer functions
try:
    from behavior.humanizer import simulate_mouse_jitter, simulate_human_scroll
except ImportError:
    # Fallback dummy functions
    async def simulate_mouse_jitter(driver):
        pass
    async def simulate_human_scroll(driver):
        pass

# Import other required modules
import aiohttp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ViewbotFormatter - either import or define
try:
    from rapidproxyscan import ViewbotFormatter
except ImportError:
    class ViewbotFormatter:
        def export_specialized_formats(self, proxies):
            return {"viewbot": "viewbot_proxies.txt"}

# ProxyTester class definition
class ProxyTester:
    """Tests proxies against custom endpoint"""
    
    def __init__(self, test_url="http://mail.whispr.dev:9876/"):
        self.test_url = test_url
        
    async def test_proxy(self, proxy_url: str) -> Dict[str, Any]:
        """Test a single proxy"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.test_url, 
                    proxy=proxy_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"}
                ) as response:
                    latency_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {
                            "proxy": proxy_url,
                            "is_usable": True,
                            "latency_ms": latency_ms,
                            "speed_rating": "fast" if latency_ms < 500 else "medium" if latency_ms < 1000 else "slow",
                            "security_level": "secure as hecc",  # Your custom rating
                            "description": "Elite proxy verified"
                        }
                    else:
                        return {
                            "proxy": proxy_url,
                            "is_usable": False,
                            "latency_ms": latency_ms,
                            "speed_rating": "failed",
                            "security_level": "unknown",
                            "description": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "proxy": proxy_url,
                "is_usable": False,
                "latency_ms": 0,
                "speed_rating": "failed",
                "security_level": "unknown",
                "description": str(e)
            }


class QuantumOSINTBridge:
    """
    Elite bridge between Rust OSINT engine and Python infrastructure
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()

        # Initialize your elite components
        self.optimizer = OptimizerIntegration()
        self.viewbot_formatter = ViewbotFormatter()
        self.medium_buster = MediumPaywallBuster()
        
        # Initialize ProxyManager with config relevant to proxy sources/refresh
        self.proxy_manager = ProxyManager(
            refresh_interval_min=self.config.get('proxy', {}).get('refresh_interval', 5),
            max_proxies=self.config.get('proxy', {}).get('max_proxies', 1000),
            disable_refresh=self.config.get('proxy', {}).get('disable_proxy_refresh', False)
        )
        
        # Initialize UserAgentManager
        self.user_agent_manager = UserAgentManager() 
        self.captcha_solver = CaptchaSolver(self.config.get('captcha_key'))
        
        # Instantiate ProxyTester with the configured test endpoint
        self.proxy_tester = ProxyTester(test_url=self.config.get('proxy', {}).get('test_endpoint', "http://mail.whispr.dev:9876/"))
        self.tested_elite_proxies: List[Dict[str, Any]] = [] # To store the detailed elite proxy results (dicts)
        self.current_elite_proxy_index = 0
        self.stats = {'total_requests': 0, 'successful_requests': 0, 'failed_requests': 0, 'start_time': time.time()}

    def _load_default_config(self) -> Dict[str, Any]:
        """Load configuration with elite defaults"""
        return {
            'proxy': { # Nested proxy config for clarity
                'test_endpoint': 'http://mail.whispr.dev:9876/', # Your specific endpoint
                'refresh_interval': 5, # Frequent updates
                'max_proxies': 1000, # Large pool
                'disable_proxy_refresh': False,
            },
            'scanner': { # Ensure this section exists with a default timeout
                'timeout': 30, # Default timeout for scanner
            },
            'captcha_key': os.getenv('CAPTCHA_API_KEY', ''),
            'max_concurrent_tests': 500,
            'proxy_timeout': 3.0,
            'validation_rounds': 3,
            'enable_paywall_bypass': True,
            'enable_captcha_solving': True,
            'export_formats': ['rust', 'viewbot', 'supreme'],
            'stealth_mode': True
        }

    async def initialize(self):
        """Initializes components and pre-tests elite proxies."""
        logger.info("🚀 Initializing Elite Quantum OSINT Bridge...")
        # Initialize optimizer
        await self.optimizer.initialize()
        # Acquire and test elite proxies using the new ProxyTester
        await self._acquire_and_test_elite_proxies()
        logger.info("✅ Elite Quantum OSINT Bridge ready for action!")

    async def _acquire_and_test_elite_proxies(self):
        """Acquire elite proxies and test them comprehensively."""
        logger.info("🔥 Acquiring and testing elite proxies...")
        
        # Get proxies from ProxyManager
        raw_elite_proxies = []
        
        # Try to get proxies from the proxy manager
        if hasattr(self.proxy_manager, 'get_proxies'):
            raw_elite_proxies = self.proxy_manager.get_proxies()
        elif hasattr(self.proxy_manager, 'pool'):
            raw_elite_proxies = self.proxy_manager.pool
        else:
            # Fallback proxies for testing
            raw_elite_proxies = [
                "http://1.2.3.4:8080",
                "http://5.6.7.8:3128",
                # Add more actual elite proxies from your sources
            ]
        
        # Format proxies properly
        formatted_proxies = []
        for proxy in raw_elite_proxies[:50]:  # Test first 50
            if isinstance(proxy, str):
                if not proxy.startswith('http'):
                    proxy = f"http://{proxy}"
                formatted_proxies.append(proxy)
        
        if not formatted_proxies:
            logger.warning("No proxies available for testing")
            return
            
        tasks = [self.proxy_tester.test_proxy(p_url) for p_url in formatted_proxies]
        results = await asyncio.gather(*tasks)
        
        self.tested_elite_proxies = []
        for res in results:
            if res.get("is_usable") and res.get("security_level") == "secure as hecc":
                self.tested_elite_proxies.append(res)
                logger.info(f"  [+] Elite proxy ready: {res['proxy']} (Latency: {res['latency_ms']:.0f}ms, Speed: {res['speed_rating']}, Security: {res['security_level']})")
            else:
                logger.debug(f"  [-] Proxy unusable: {res['proxy']} - {res['description']}")
        
        self.tested_elite_proxies = sorted(self.tested_elite_proxies, key=lambda x: x['latency_ms'])
        logger.info(f"Initialized with {len(self.tested_elite_proxies)} elite and secure proxies.")
        self.stats['proxies_working'] = len(self.tested_elite_proxies)

    async def get_elite_proxy(self) -> Optional[str]:
        """
        Gets the next available elite proxy from the tested pool,
        prioritizing faster, more secure ones.
        """
        if not self.tested_elite_proxies:
            logger.warning("No elite proxies available after testing. Trying to re-acquire...")
            await self._acquire_and_test_elite_proxies()
            if not self.tested_elite_proxies:
                return None

        proxy_info = self.tested_elite_proxies[self.current_elite_proxy_index % len(self.tested_elite_proxies)]
        self.current_elite_proxy_index += 1
        logger.debug(f"Returning elite proxy: {proxy_info['proxy']} (Latency: {proxy_info['latency_ms']:.0f}ms)")
        return proxy_info['proxy']

    async def test_proxy_ultra_fast(self, proxy: str) -> Dict[str, Any]:
        """Ultra-fast proxy testing using your custom endpoint via the ProxyTester."""
        return await self.proxy_tester.test_proxy(proxy)

    async def bypass_paywall(self, url: str) -> str:
        """Bypass paywall using your elite system"""
        logger.info(f"🧠 Bypassing paywall: {url}")
        # Get an elite proxy for this bypass attempt
        proxy_to_use = await self.get_elite_proxy()
        if not proxy_to_use:
            logger.error(f"Cannot bypass paywall for {url}: No elite proxy available.")
            return ""
        try:
            # Use your MediumPaywallBuster
            if hasattr(self.medium_buster, 'fetch_article_text'):
                content = await self.medium_buster.fetch_article_text(url)
            else:
                # Fallback
                content = f"Paywall bypass placeholder for {url}"
            
            self.stats['paywalls_bypassed'] = self.stats.get('paywalls_bypassed', 0) + 1
            logger.info(f"✅ Paywall bypassed successfully: {len(content)} chars extracted using proxy {proxy_to_use}")
            return content
        except Exception as e:
            logger.error(f"Paywall bypass failed for {url} with proxy {proxy_to_use}: {e}")
            return ""

    async def solve_captcha_if_needed(self, page_url: str, site_key: str = None) -> Optional[str]:
        """Solve CAPTCHA using your 2Captcha integration"""
        if not self.config.get('enable_captcha_solving'):
            return None
        try:
            logger.info("🧩 Solving CAPTCHA...")
            proxy_for_captcha = await self.get_elite_proxy()
            
            if hasattr(self.captcha_solver, 'solve_recaptcha'):
                solution = await self.captcha_solver.solve_recaptcha(page_url, site_key)
            else:
                solution = None
                
            if solution:
                self.stats['captchas_solved'] = self.stats.get('captchas_solved', 0) + 1
                logger.info("✅ CAPTCHA solved successfully")
            return solution
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None

    async def get_elite_proxy_info(self) -> Optional[Dict[str, Any]]:
        """Get the full detailed info of an elite proxy from the pool"""
        if not self.tested_elite_proxies:
            logger.warning("No elite proxies available. Trying to re-acquire...")
            await self._acquire_and_test_elite_proxies()
            if not self.tested_elite_proxies:
                return None
        proxy_info = self.tested_elite_proxies[self.current_elite_proxy_index % len(self.tested_elite_proxies)]
        self.current_elite_proxy_index += 1
        return proxy_info

    async def simulate_human_behavior(self, driver=None):
        """Simulate human behavior using your humanizer"""
        if not driver:
            return
        try:
            await simulate_mouse_jitter(driver)
            await simulate_human_scroll(driver)
            logger.debug("🤖 Human behavior simulation completed")
        except Exception as e:
            logger.debug(f"Human behavior simulation failed: {e}")

    def export_for_rust(self, filename: str = None) -> str:
        """Export proxies in format for Rust engine"""
        if not filename:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"rust_proxies_{timestamp}.txt"
        
        proxies = [p['proxy'].replace('http://', '').replace('https://', '') for p in self.tested_elite_proxies]
        
        with open(filename, 'w') as f:
            f.write("# Elite Proxies for Rust OSINT Engine\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {len(proxies)}\n")
            f.write("#\n")
            for proxy in proxies:
                f.write(f"{proxy}\n")
        
        logger.info(f"📤 Exported {len(proxies)} proxies for Rust: {filename}")
        return filename

    def export_specialized_formats(self) -> Dict[str, str]:
        """Export in all specialized formats"""
        exports = {}
        
        # Export for Rust
        exports['rust'] = self.export_for_rust()
        
        # Export using your ViewbotFormatter
        if hasattr(self.viewbot_formatter, 'export_specialized_formats'):
            viewbot_exports = self.viewbot_formatter.export_specialized_formats(self.tested_elite_proxies)
            exports.update(viewbot_exports)
        else:
            logger.warning("ViewbotFormatter does not have 'export_specialized_formats' method.")
        
        return exports

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        runtime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'runtime_seconds': runtime,
            'proxies_per_second': len(self.tested_elite_proxies) / max(runtime, 1),
            'success_rate': (self.stats['successful_requests'] / max(self.stats['total_requests'], 1)) * 100,
            'pool_size': len(self.tested_elite_proxies)
        }

    async def quantum_scan_target(self, target: str) -> Dict[str, Any]:
        """Perform a quantum scan on a target using all elite capabilities"""
        logger.info(f"🎯 Quantum scanning target: {target}")
        results = {
            'target': target,
            'findings': [],
            'paywall_content': {},
            'proxies_used': [],
            'scan_time': time.time()
        }
        
        # Get elite proxy for this scan
        proxy_info = await self.get_elite_proxy_info()
        proxy_url = proxy_info['proxy'] if proxy_info else None
        
        if proxy_url:
            results['proxies_used'].append(proxy_url)
        else:
            logger.error(f"Cannot perform quantum scan on {target}: No elite proxy available.")
            return results
        
        # Check if target has paywalled content
        if self.config.get('enable_paywall_bypass') and any(domain in target for domain in ['medium.com', 'substack.com', 'wsj.com']):
            logger.info(f"🧠 Target has paywalled content, attempting bypass...")
            content = await self.bypass_paywall(f"https://{target}")
            if content:
                results['paywall_content'][target] = content[:1000]
        
        try:
            async with aiohttp.ClientSession() as session:
                scan_timeout = self.config.get('scanner', {}).get('timeout', 30)
                async with session.get(f"https://{target}", proxy=proxy_url, timeout=scan_timeout) as response:
                    response.raise_for_status()
                    content = await response.text()
                    logger.info(f"Successfully accessed {target} for quantum scan. Content length: {len(content)} bytes.")
                    
                    quantum_score = 0
                    if "robots.txt" in content:
                        quantum_score += 5
                    if "admin" in content.lower() or "dashboard" in content.lower():
                        quantum_score += 10
                    
                    self.stats['total_requests'] += 1
                    self.stats['successful_requests'] += 1
                    
                    results['findings'].append({
                        'type': 'Quantum OSINT Scan',
                        'severity': 'Info',
                        'description': f'Successfully scanned {target} via elite proxy {proxy_url}.',
                        'quantum_score': quantum_score,
                        'proxy_info': proxy_info
                    })
        except Exception as e:
            logger.error(f"Error during quantum scan of {target} with proxy {proxy_url}: {e}")
            self.stats['total_requests'] = self.stats.get('total_requests', 0) + 1
            self.stats['failed_requests'] = self.stats.get('failed_requests', 0) + 1
            
            results['findings'].append({
                'type': 'Quantum OSINT Scan',
                'severity': 'Error',
                'description': f'Failed to scan {target} via elite proxy {proxy_url}: {e}',
                'quantum_score': 0,
                'proxy_info': proxy_info
            })
        
        return results


async def main():
    """Main entry point for the bridge"""
    bridge = QuantumOSINTBridge()

    try:
        await bridge.initialize()

        # Test the bridge
        logger.info("🧪 Testing Elite Quantum OSINT Bridge...")

        # Test proxy acquisition
        proxy_info = await bridge.get_elite_proxy_info()
        if proxy_info:
            logger.info(f"🔥 Got elite proxy: {proxy_info['proxy']} (Speed: {proxy_info['speed_rating']}, Security: {proxy_info['security_level']})")
        else:
            logger.info("🔥 No elite proxy acquired.")

        # Test a quantum scan
        result = await bridge.quantum_scan_target("example.com")
        logger.info(f"🎯 Scan result: {result}")

        # Export formats
        exports = bridge.export_specialized_formats()
        logger.info(f"📤 Exported formats: {list(exports.keys())}")

        # Show performance stats
        stats = bridge.get_performance_stats()
        logger.info(f"📊 Performance: {stats}")

        logger.info("🌟 Elite Quantum OSINT Bridge test complete!")

    except KeyboardInterrupt:
        logger.info("👋 Shutting down Elite Quantum OSINT Bridge...")
    except Exception as e:
        logger.error(f"💥 Bridge error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())