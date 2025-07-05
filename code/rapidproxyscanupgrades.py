"""
RapidProxyScan - Advanced Optimizations Module
==============================================

This module implements the most sophisticated proxy scanning optimizations:
1. Lightweight custom endpoint creation
2. CDN-distributed endpoint selection for geographical optimization
3. DNS pre-resolution and aggressive caching
4. Header compression and bandwidth optimization
5. Binary protocol implementations
6. Special formatting for viewbot/Supreme environments
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
from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("proxy_optimizer")

# ===========================================================================
# 1. LIGHTWEIGHT CUSTOM ENDPOINT CREATION
# ===========================================================================

class CustomEndpointManager:
    """Creates and manages ultra-lightweight endpoints for proxy testing"""
    
    def __init__(self):
        self.endpoints = {}
        self.endpoint_stats = defaultdict(lambda: {"success": 0, "failure": 0, "avg_time": 0})
        self.endpoint_health_lock = asyncio.Lock()
    
    async def create_endpoint_selection_map(self) -> Dict[str, List[str]]:
        """Create a mapping of regions to optimal endpoints"""
        # This maps geographical regions to the best endpoints for that region
        region_map = {
            "na": [],  # North America
            "eu": [],  # Europe
            "as": [],  # Asia
            "sa": [],  # South America
            "oc": [],  # Oceania
            "af": []   # Africa
        }
        
        # Populate with predefined lightweight endpoints optimized for each region
        region_map["na"] = [
            "https://cloudfront-na.example.com/echo",  # AWS CloudFront North America
            "https://na-ping.httpbin.org/ip",         # North America optimized
            "http://cdn-na.iptest.net/ping"           # NA CDN endpoint
        ]
        
        region_map["eu"] = [
            "https://cloudfront-eu.example.com/echo",  # AWS CloudFront Europe
            "https://eu-ping.httpbin.org/ip",         # Europe optimized
            "http://cdn-eu.iptest.net/ping"           # EU CDN endpoint
        ]
        
        region_map["as"] = [
            "https://cloudfront-ap.example.com/echo",  # AWS CloudFront Asia Pacific
            "https://ap-ping.httpbin.org/ip",         # Asia Pacific optimized
            "http://cdn-ap.iptest.net/ping"           # AP CDN endpoint
        ]
        
        # Add standard endpoints as fallbacks for all regions
        standard_endpoints = [
            "http://httpbin.org/ip",
            "https://api.ipify.org/?format=json",
            "http://ip-api.com/json/",
            "https://www.cloudflare.com/cdn-cgi/trace"
        ]
        
        # Add to all regions as fallbacks
        for region in region_map:
            region_map[region].extend(standard_endpoints)
        
        return region_map
    
    async def select_optimal_endpoint(self, proxy_info: dict) -> str:
        """Select the optimal endpoint based on proxy location and endpoint health"""
        # Default endpoints if we don't have location data
        if not proxy_info.get("country"):
            return random.choice([
                "http://httpbin.org/ip", 
                "https://api.ipify.org/?format=json"
            ])
        
        # Map country to region (simplified)
        country = proxy_info["country"].lower()
        
        # Map countries to regions (partial list)
        country_to_region = {
            # North America
            "us": "na", "ca": "na", "mx": "na",
            # Europe
            "gb": "eu", "de": "eu", "fr": "eu", "it": "eu", "es": "eu", "nl": "eu",
            # Asia
            "cn": "as", "jp": "as", "kr": "as", "in": "as", "sg": "as",
            # South America
            "br": "sa", "ar": "sa", "co": "sa", "cl": "sa",
            # Oceania
            "au": "oc", "nz": "oc",
            # Africa
            "za": "af", "ng": "af", "eg": "af"
        }
        
        region = country_to_region.get(country, "na")  # Default to NA if unknown
        
        # Get endpoints for this region
        region_map = await self.create_endpoint_selection_map()
        endpoints = region_map.get(region, region_map["na"])
        
        # Select based on health metrics
        async with self.endpoint_health_lock:
            # Sort endpoints by success rate and response time
            scored_endpoints = []
            for endpoint in endpoints:
                stats = self.endpoint_stats[endpoint]
                total = stats["success"] + stats["failure"]
                if total == 0:
                    # No data yet, give it a middle score
                    scored_endpoints.append((endpoint, 0.5))
                else:
                    success_rate = stats["success"] / total
                    # Normalize response time (0-1 scale, lower is better)
                    time_score = 1.0 - min(1.0, stats["avg_time"] / 5000.0) if stats["avg_time"] > 0 else 0.5
                    # Combined score (70% success rate, 30% speed)
                    score = (success_rate * 0.7) + (time_score * 0.3)
                    scored_endpoints.append((endpoint, score))
            
            # Sort by score (highest first)
            scored_endpoints.sort(key=lambda x: x[1], reverse=True)
            
            # Select randomly from top 3 to avoid overloading any single endpoint
            top_endpoints = [e[0] for e in scored_endpoints[:3]] if len(scored_endpoints) >= 3 else [e[0] for e in scored_endpoints]
            return random.choice(top_endpoints)
    
    async def update_endpoint_health(self, endpoint: str, success: bool, response_time: float):
        """Update health metrics for an endpoint"""
        async with self.endpoint_health_lock:
            stats = self.endpoint_stats[endpoint]
            
            if success:
                stats["success"] += 1
                # Update rolling average response time (last 20 requests)
                if stats["avg_time"] == 0:
                    stats["avg_time"] = response_time
                else:
                    stats["avg_time"] = (stats["avg_time"] * 19 + response_time) / 20
            else:
                stats["failure"] += 1
    
    async def create_micro_endpoint(self) -> str:
        """
        Create a micro-endpoint for testing (using serverless functions)
        This would create a specialized endpoint optimized for proxy testing
        
        Note: This is a placeholder for the concept - actual implementation would 
        involve deploying serverless functions on AWS Lambda, Cloudflare Workers, etc.
        """
        # In a real implementation, this would:
        # 1. Deploy a serverless function that returns minimal response
        # 2. Wait for deployment to complete
        # 3. Return the URL of the deployed function
        
        # For now, return a known lightweight endpoint
        return "https://echo.zuplo.io/"


# ===========================================================================
# 2. DNS PRE-RESOLUTION AND CACHING
# ===========================================================================

class EnhancedDNSCache:
    """Advanced DNS cache with pre-resolution and TTL management"""
    
    def __init__(self, ttl: int = 300):
        self.cache = {}  # hostname -> (ip, timestamp)
        self.ttl = ttl
        self.lock = asyncio.Lock()
        self.popular_domains = set([
            "httpbin.org",
            "api.ipify.org",
            "ip-api.com",
            "cloudflare.com",
            "google.com",
            "aws.amazon.com",
            "example.com"
        ])
        self.resolvers = [
            "1.1.1.1",  # Cloudflare
            "8.8.8.8",  # Google
            "9.9.9.9",  # Quad9
            "208.67.222.222"  # OpenDNS
        ]
    
    async def pre_resolve_popular_domains(self):
        """Pre-resolve popular domains used for testing"""
        logger.info("Pre-resolving common domains...")
        
        for domain in self.popular_domains:
            await self.resolve(domain)
        
        logger.info(f"Pre-resolved {len(self.popular_domains)} domains")
    
    async def resolve(self, hostname: str) -> str:
        """Resolve hostname to IP with caching"""
        # Check cache first
        async with self.lock:
            cache_entry = self.cache.get(hostname)
            if cache_entry:
                ip, timestamp = cache_entry
                if time.time() - timestamp < self.ttl:
                    return ip
        
        # Not in cache or expired, resolve it
        try:
            # This is a simplified implementation
            # In production, use proper async DNS resolution
            loop = asyncio.get_running_loop()
            ip = await loop.run_in_executor(None, socket.gethostbyname, hostname)
            
            # Cache the result
            async with self.lock:
                self.cache[hostname] = (ip, time.time())
            
            return ip
        except socket.gaierror:
            logger.warning(f"Failed to resolve {hostname}")
            return None
    
    async def resolve_with_multiple_providers(self, hostname: str) -> str:
        """Resolve using multiple DNS providers for redundancy"""
        # Try built-in resolver first
        result = await self.resolve(hostname)
        if result:
            return result
        
        # If that fails, try specific DNS servers
        # This would require a more complex implementation with DNS library
        # For the concept, we'll return None to indicate failure
        return None
    
    def get_cached_domains(self) -> List[str]:
        """Get list of currently cached domains"""
        return list(self.cache.keys())


# ===========================================================================
# 3. HEADER COMPRESSION AND BANDWIDTH OPTIMIZATION
# ===========================================================================

class RequestOptimizer:
    """Optimizes HTTP requests for minimal bandwidth usage"""
    
    def __init__(self):
        self.compressed_headers = {
            "User-Agent": "cps",  # Compressed Proxy Scanner
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        
        # Map of full header names to short versions for compression
        self.header_compression_map = {
            "User-Agent": "u",
            "Accept": "a", 
            "Accept-Language": "al",
            "Accept-Encoding": "ae",
            "Connection": "c",
            "Cache-Control": "cc",
            "Content-Type": "ct",
            "Content-Length": "cl",
            "Host": "h",
            "Origin": "o",
            "Referer": "r"
        }
    
    def get_minimal_headers(self) -> Dict[str, str]:
        """Get minimal HTTP headers for testing"""
        return self.compressed_headers
    
    def compress_request_data(self, data: str) -> bytes:
        """Compress request data using gzip"""
        return gzip.compress(data.encode())
    
    def create_binary_test_packet(self) -> bytes:
        """Create a binary protocol test packet (more efficient than HTTP)"""
        # Format: [4-byte magic number][1-byte version][1-byte command][4-byte timestamp]
        # This is a minimal binary protocol for testing proxy connectivity
        
        magic = b"CPST"  # Compressed Proxy Scanner Test
        version = 1
        command = 1  # 1 = ping
        timestamp = int(time.time()) & 0xFFFFFFFF
        
        return struct.pack("!4sBBI", magic, version, command, timestamp)
    
    def optimize_url_for_proxy_test(self, url: str) -> str:
        """Optimize URL for proxy testing by removing unnecessary components"""
        # Remove query parameters except essential ones
        if "?" in url:
            base, query = url.split("?", 1)
            essential_params = ["format=json"]
            
            if any(param in query for param in essential_params):
                # Keep only essential parameters
                new_query = "&".join(p for p in query.split("&") if any(e in p for e in essential_params))
                return f"{base}?{new_query}"
            else:
                return base
        
        return url


# ===========================================================================
# 4. VIEWBOT/SUPREME SPECIALIZED FORMATTING
# ===========================================================================

class ViewbotFormatter:
    """Specialized formatter for viewbot/Supreme integration"""
    
    def __init__(self):
        self.speed_categories = {
            "ultra": [],    # <200ms
            "fast": [],     # 200-500ms
            "medium": [],   # 500-1000ms
            "slow": []      # >1000ms
        }
        
        self.reliability_categories = {
            "platinum": [],  # 100% success
            "gold": [],      # 90-99% success
            "silver": [],    # 75-89% success
            "bronze": []     # <75% success
        }
        
        self.stealth_categories = {
            "elite": [],     # High anonymity
            "anonymous": [], # Medium anonymity
            "transparent": [] # Low anonymity
        }
        
        # Keep track of persistent proxies (seen in multiple scans)
        self.persistent_proxies = set()
        self.persistence_counter = defaultdict(int)
        
        # History of all seen proxies
        self.proxy_history = {}
        
        # Fast track list - proxies that can skip some validation steps
        self.fast_track_proxies = set()
    
    def categorize_proxy(self, proxy: dict):
        """Categorize a proxy by speed, reliability, and stealth"""
        # Speed categorization
        response_time = proxy.get("avg_response_time", 1000)
        if response_time < 200:
            self.speed_categories["ultra"].append(proxy)
        elif response_time < 500:
            self.speed_categories["fast"].append(proxy)
        elif response_time < 1000:
            self.speed_categories["medium"].append(proxy)
        else:
            self.speed_categories["slow"].append(proxy)
        
        # Reliability categorization
        reliability = proxy.get("reliability", 0)
        if reliability >= 100:
            self.reliability_categories["platinum"].append(proxy)
        elif reliability >= 90:
            self.reliability_categories["gold"].append(proxy)
        elif reliability >= 75:
            self.reliability_categories["silver"].append(proxy)
        else:
            self.reliability_categories["bronze"].append(proxy)
        
        # Stealth categorization
        anonymity = proxy.get("anonymity", "unknown")
        if anonymity == "high":
            self.stealth_categories["elite"].append(proxy)
        elif anonymity == "medium":
            self.stealth_categories["anonymous"].append(proxy)
        else:
            self.stealth_categories["transparent"].append(proxy)
        
        # Update persistence tracking
        address = f"{proxy['host']}:{proxy['port']}"
        self.persistence_counter[address] += 1
        
        if self.persistence_counter[address] >= 3:
            self.persistent_proxies.add(address)
            # Add to fast track list if also reliable
            if reliability >= 85:
                self.fast_track_proxies.add(address)
        
        # Update history
        self.proxy_history[address] = {
            "last_seen": time.time(),
            "times_seen": self.persistence_counter[address],
            "reliability": reliability,
            "response_time": response_time,
            "anonymity": anonymity
        }
    
    def is_fast_track_proxy(self, proxy_address: str) -> bool:
        """Check if a proxy is in the fast track list"""
        return proxy_address in self.fast_track_proxies
    
    def get_persistent_proxies(self) -> List[str]:
        """Get list of persistent proxies"""
        return list(self.persistent_proxies)
    
    def export_for_viewbot(self, filename: str, filters: Dict[str, Any] = None):
        """Export specialized format for viewbot integration"""
        # Default filters
        if filters is None:
            filters = {
                "min_reliability": 75,
                "max_response_time": 1000,
                "min_anonymity": "medium"
            }
        
        # Collect proxies matching filters
        matching_proxies = []
        
        # Helper to check if proxy matches filters
        def matches_filters(proxy):
            if proxy.get("reliability", 0) < filters["min_reliability"]:
                return False
            if proxy.get("avg_response_time", 9999) > filters["max_response_time"]:
                return False
            
            anonymity = proxy.get("anonymity", "unknown")
            if filters["min_anonymity"] == "high" and anonymity != "high":
                return False
            if filters["min_anonymity"] == "medium" and anonymity not in ["high", "medium"]:
                return False
            
            return True
        
        # First add persistent + fast proxies
        for category in ["ultra", "fast"]:
            for proxy in self.speed_categories[category]:
                address = f"{proxy['host']}:{proxy['port']}"
                if address in self.persistent_proxies and matches_filters(proxy):
                    proxy["persistent"] = True
                    proxy["fast_track"] = address in self.fast_track_proxies
                    matching_proxies.append(proxy)
        
        # Then add other good proxies
        for category in ["medium"]:
            for proxy in self.speed_categories[category]:
                address = f"{proxy['host']}:{proxy['port']}"
                if address not in self.persistent_proxies and matches_filters(proxy):
                    proxy["persistent"] = False
                    proxy["fast_track"] = False
                    matching_proxies.append(proxy)
        
        # Sort by combined score (reliability * speed * anonymity bonus)
        def score_proxy(proxy):
            reliability = proxy.get("reliability", 0)
            speed_factor = 1.0 - min(1.0, proxy.get("avg_response_time", 1000) / 1000.0)
            
            anonymity_bonus = 1.0
            if proxy.get("anonymity") == "high":
                anonymity_bonus = 1.5
            elif proxy.get("anonymity") == "medium":
                anonymity_bonus = 1.2
            
            persistence_bonus = 1.5 if proxy.get("persistent", False) else 1.0
            
            return (reliability/100.0) * speed_factor * anonymity_bonus * persistence_bonus
        
        matching_proxies.sort(key=score_proxy, reverse=True)
        
        # Export in viewbot format
        with open(filename, 'w') as f:
            f.write("# RAPIDPROXYSCAN ELITE EXPORT FOR VIEWBOT/SUPREME\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total proxies: {len(matching_proxies)}\n")
            f.write("#\n")
            f.write("# FORMAT: [protocol]://[host]:[port] [speed_ms] [reliability%] [anonymity] [persistence]\n")
            f.write("#\n")
            
            for proxy in matching_proxies:
                protocol = proxy.get("protocol", "http")
                host = proxy.get("host", "")
                port = proxy.get("port", 80)
                response_time = proxy.get("avg_response_time", 0)
                reliability = proxy.get("reliability", 0)
                anonymity = proxy.get("anonymity", "unknown")
                persistent = "P" if proxy.get("persistent", False) else "-"
                fast_track = "F" if proxy.get("fast_track", False) else "-"
                
                flags = f"{persistent}{fast_track}"
                
                f.write(f"{protocol}://{host}:{port} {response_time:.1f} {reliability:.1f} {anonymity} {flags}\n")
        
        logger.info(f"Exported {len(matching_proxies)} proxies in viewbot format to {filename}")
        return len(matching_proxies)
    
    def export_for_supreme(self, filename: str):
        """Export specialized format for Supreme bot integration"""
        # Supreme format prioritizes elite proxies with consistent success rates
        
        # Select only the highest quality proxies
        supreme_proxies = []
        
        # First add platinum+gold elite proxies
        for proxy in self.reliability_categories["platinum"] + self.reliability_categories["gold"]:
            if proxy.get("anonymity") == "high":
                supreme_proxies.append(proxy)
        
        # Then add persistent proxies with good reliability
        for address in self.persistent_proxies:
            if address.split(":")[0] in [p["host"] for p in supreme_proxies]:
                continue  # Already added
                
            history = self.proxy_history.get(address, {})
            if history.get("reliability", 0) >= 80:
                host, port = address.split(":")
                supreme_proxies.append({
                    "host": host,
                    "port": int(port),
                    "protocol": "https",  # Supreme prefers HTTPS
                    "reliability": history.get("reliability", 0),
                    "avg_response_time": history.get("response_time", 1000),
                    "anonymity": history.get("anonymity", "unknown"),
                    "persistent": True
                })
        
        # Sort by reliability first, then speed
        supreme_proxies.sort(key=lambda p: (p.get("reliability", 0), -p.get("avg_response_time", 1000)), reverse=True)
        
        # Export in Supreme format
        with open(filename, 'w') as f:
            f.write("# RAPIDPROXYSCAN SUPREME EXPORT\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total proxies: {len(supreme_proxies)}\n")
            f.write("#\n")
            f.write("# FORMAT: [host]:[port]\n")
            f.write("#\n")
            
            # Supreme format is just host:port
            for proxy in supreme_proxies:
                f.write(f"{proxy['host']}:{proxy['port']}\n")
        
        logger.info(f"Exported {len(supreme_proxies)} elite proxies in Supreme format to {filename}")
        return len(supreme_proxies)
    
    def export_specialized_formats(self, base_dir: str = "."):
        """Export all specialized formats"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Ensure directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Export for different tools
        viewbot_file = os.path.join(base_dir, f"viewbot_proxies_{timestamp}.txt")
        supreme_file = os.path.join(base_dir, f"supreme_proxies_{timestamp}.txt")
        
        viewbot_count = self.export_for_viewbot(viewbot_file)
        supreme_count = self.export_for_supreme(supreme_file)
        
        # Export statistics
        stats_file = os.path.join(base_dir, f"proxy_stats_{timestamp}.json")
        with open(stats_file, 'w') as f:
            stats = {
                "timestamp": timestamp,
                "total_proxies": sum(len(c) for c in self.speed_categories.values()),
                "speed_categories": {k: len(v) for k, v in self.speed_categories.items()},
                "reliability_categories": {k: len(v) for k, v in self.reliability_categories.items()},
                "stealth_categories": {k: len(v) for k, v in self.stealth_categories.items()},
                "persistent_proxies": len(self.persistent_proxies),
                "fast_track_proxies": len(self.fast_track_proxies),
                "exports": {
                    "viewbot": viewbot_count,
                    "supreme": supreme_count
                }
            }
            json.dump(stats, f, indent=2)
        
        return {
            "viewbot": viewbot_file,
            "supreme": supreme_file,
            "stats": stats_file
        }


# ===========================================================================
# 5. INTEGRATION WITH MAIN SCANNER
# ===========================================================================

class OptimizerIntegration:
    """Integrates all optimizations with the main scanner"""
    
    def __init__(self):
        self.dns_cache = EnhancedDNSCache()
        self.endpoint_manager = CustomEndpointManager()
        self.request_optimizer = RequestOptimizer()
        self.viewbot_formatter = ViewbotFormatter()
        self.initialization_complete = False
        
        # Performance metrics
        self.metrics = {
            "dns_cache_hits": 0,
            "dns_cache_misses": 0,
            "endpoint_selections": defaultdict(int),
            "connection_reuse_count": 0,
            "optimized_requests_sent": 0,
            "binary_protocol_tests": 0
        }
    
    async def initialize(self):
        """Initialize all optimization components"""
        if self.initialization_complete:
            return
        
        logger.info("Initializing advanced optimization components...")
        
        # Pre-resolve common domains
        await self.dns_cache.pre_resolve_popular_domains()
        
        # Initialize custom endpoints
        endpoints = await self.endpoint_manager.create_endpoint_selection_map()
        logger.info(f"Initialized with {sum(len(e) for e in endpoints.values())} optimized endpoints")
        
        self.initialization_complete = True
        logger.info("Advanced optimizations initialized successfully")
    
    async def optimize_proxy_test(self, session, proxy_info):
        """Apply all optimizations to a proxy test"""
        if not self.initialization_complete:
            await self.initialize()
        
        # 1. Select optimal endpoint based on proxy location
        endpoint = await self.endpoint_manager.select_optimal_endpoint(proxy_info)
        self.metrics["endpoint_selections"][endpoint] += 1
        
        # 2. Optimize the URL
        optimized_url = self.request_optimizer.optimize_url_for_proxy_test(endpoint)
        
        # 3. Get minimal headers
        headers = self.request_optimizer.get_minimal_headers()
        
        # 4. Check if proxy is in fast track list
        address = f"{proxy_info['host']}:{proxy_info['port']}"
        is_fast_track = self.viewbot_formatter.is_fast_track_proxy(address)
        
        # 5. Use binary protocol for ultra-fast testing if supported
        use_binary_protocol = is_fast_track and random.random() < 0.3  # 30% chance for fast track proxies
        
        # Return the optimized test configuration
        return {
            "url": optimized_url,
            "headers": headers,
            "is_fast_track": is_fast_track,
            "use_binary_protocol": use_binary_protocol,
        }
    
    async def post_test_processing(self, proxy_info, success, response_time, endpoint):
        """Process results after a proxy test"""
        # Update endpoint health metrics
        await self.endpoint_manager.update_endpoint_health(endpoint, success, response_time)
        
        # If test was successful, categorize the proxy
        if success:
            self.viewbot_formatter.categorize_proxy(proxy_info)
    
    def export_specialized_formats(self, base_dir="."):
        """Export all specialized formats for downstream tools"""
        return self.viewbot_formatter.export_specialized_formats(base_dir)
    
    def get_metrics(self):
        """Get performance metrics"""
        return self.metrics
    
    def get_fast_track_proxies(self):
        """Get list of proxies that can be fast-tracked"""
        return self.viewbot_formatter.get_persistent_proxies()


# ===========================================================================
# USAGE EXAMPLE
# ===========================================================================

async def demo_usage():
    """Demonstrate usage of the optimization module"""
    optimizer = OptimizerIntegration()
    await optimizer.initialize()
    
    # Example proxy info
    proxy_info = {
        "host": "123.45.67.89",
        "port": 8080,
        "protocol": "http",
        "country": "us",
        "avg_response_time": 350,
        "reliability": 95,
        "anonymity": "high"
    }
    
    # Optimize a proxy test
    session = None  # Would be aiohttp.ClientSession in real usage
    test_config = await optimizer.optimize_proxy_test(session, proxy_info)
    
    print("Optimized test configuration:")
    print(f"URL: {test_config['url']}")
    print(f"Headers: {test_config['headers']}")
    print(f"Fast track: {test_config['is_fast_track']}")
    print(f"Binary protocol: {test_config['use_binary_protocol']}")
    
    # Simulate test result
    await optimizer.post_test_processing(
        proxy_info, 
        success=True, 
        response_time=350,
        endpoint=test_config['url']
    )
    
    # Export specialized formats
    export_paths = optimizer.export_specialized_formats()
    print(f"Exported specialized formats: {export_paths}")
    
    # Get metrics
    metrics = optimizer.get_metrics()
    print(f"Performance metrics: {metrics}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_usage())