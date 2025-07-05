# proxy_starter_list.py
"""
Initial Proxy Sources and Elite Proxy Endpoints
==============================================
High-quality proxy sources for bootstrapping the scanner
"""

PROXY_SOURCES = {
    "elite_sources": [
        # Private/elite proxy endpoints (replace with your actual sources)
        "http://11.22.33.44:3128/elite.txt",  # Your elite proxy source
        "http://proxy-test.fastping.it.com/proxies.txt",  # Your custom endpoint
    ],
    
    "premium_free_sources": [
        # Higher quality free sources
        "https://www.proxy-list.download/api/v1/get?type=http&anon=elite",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=elite",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    ],
    
    "general_sources": [
        # Standard free proxy sources
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
        "https://raw.githubusercontent.com/proxy4free/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
    ],
    
    "api_endpoints": [
        # API-based sources
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
        "https://www.proxyscan.io/api/proxy?format=textplain&type=http",
        "https://api.openproxylist.xyz/http.txt",
        "http://pubproxy.com/api/proxy?format=txt&type=http",
    ],
    
    "specialized_sources": [
        # Sources for specific proxy types
        "https://www.sslproxies.org/",  # SSL proxies
        "https://free-proxy-list.net/",  # General list
        "https://www.us-proxy.org/",  # US proxies
        "https://free-proxy-list.net/uk-proxy.html",  # UK proxies
        "https://www.socks-proxy.net/",  # SOCKS proxies
    ],
    
    "backup_sources": [
        # Fallback sources if primary ones fail
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    ]
}

# Test endpoints optimized for speed
TEST_ENDPOINTS = {
    "fastest": [
        "http://proxy-test.fastping.it.com/", # This is your primary target for detailed info
        "https://www.google.com/",
        "https://ifconfig.me/ip",
    ],

    "cloudflare": [
        "https://cloudflare.com/cdn-cgi/trace",
        "https://1.1.1.1/cdn-cgi/trace",
    ],
    
    "regional": {
        # Region-specific test endpoints for better routing
        "us": ["https://api-us.ipify.org/", "http://checkip.amazonaws.com/"],
        "eu": ["https://api-eu.ipify.org/", "http://ident.me/"],
        "asia": ["https://api-asia.ipify.org/", "http://api.ipapi.com/check"],
    },
    
    "fallback": [
        # Fallback endpoints if primary ones fail
        "http://icanhazip.com/",
        "http://checkip.dyndns.org/",
        "http://whatismyipaddress.com/api/ip",
    ]
}

# Pre-validated elite proxies for bootstrapping
BOOTSTRAP_PROXIES = [
    # Add your known good proxies here
    # Format: "protocol://ip:port" or "ip:port"
    # "http://123.45.67.89:8080",
    # "https://98.76.54.32:3128",
]

# CDN endpoints for distributed testing
CDN_ENDPOINTS = {
    "cloudflare": [
        "https://cloudflare.com/cdn-cgi/trace",
        "https://1.1.1.1/cdn-cgi/trace",
    ],
    "cloudfront": [
        "https://d111111abcdef8.cloudfront.net/test",
    ],
    "fastly": [
        "https://fastly.com/test",
    ],
    "akamai": [
        "https://akamai.com/test",
    ]
}

def get_all_sources():
    """Get all proxy sources as a flat list"""
    all_sources = []
    for source_list in PROXY_SOURCES.values():
        if isinstance(source_list, list):
            all_sources.extend(source_list)
    return all_sources

def get_elite_sources():
    """Get only elite/premium sources"""
    return PROXY_SOURCES.get("elite_sources", []) + PROXY_SOURCES.get("premium_free_sources", [])

def get_test_endpoints(category="fastest"):
    """Get test endpoints by category"""
    return TEST_ENDPOINTS.get(category, TEST_ENDPOINTS["fastest"])

def get_regional_endpoint(region="us"):
    """Get region-specific test endpoint"""
    regional = TEST_ENDPOINTS.get("regional", {})
    endpoints = regional.get(region, regional.get("us", []))
    return endpoints[0] if endpoints else TEST_ENDPOINTS["fastest"][0]

if __name__ == "__main__":
    print(f"Total proxy sources: {len(get_all_sources())}")
    print(f"Elite sources: {len(get_elite_sources())}")
    print(f"Test endpoints: {len(TEST_ENDPOINTS['fastest'])}")
    print("\nSample sources:")
    for src in get_all_sources()[:5]:
        print(f"  - {src}")