#!/usr/bin/env python3
"""
Simple Proxy Fetcher for Windows
================================
Gets proxies without any fancy stuff
"""

import requests
import os
from pathlib import Path

def fetch_proxies():
    """Fetch proxies from reliable sources"""
    print("[*] Fetching proxies...")
    
    # These sources usually work
    sources = [
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    ]
    
    all_proxies = set()
    
    for source in sources:
        try:
            print(f"[*] Trying: {source}")
            response = requests.get(source, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                count = 0
                for line in lines:
                    line = line.strip()
                    # Basic validation
                    if ':' in line and '.' in line:
                        # Remove http:// or https:// if present
                        if line.startswith('http://'):
                            line = line[7:]
                        elif line.startswith('https://'):
                            line = line[8:]
                        
                        # Basic format check
                        parts = line.split(':')
                        if len(parts) == 2 and parts[1].isdigit():
                            all_proxies.add(line)
                            count += 1
                
                print(f"[+] Got {count} proxies from this source")
        except Exception as e:
            print(f"[-] Failed: {str(e)[:50]}")
    
    # Create directories
    Path("data/proxies").mkdir(parents=True, exist_ok=True)
    Path("exported_proxies").mkdir(exist_ok=True)
    
    # Save proxies to multiple locations
    locations = [
        "data/proxies/proxies.txt",
        "data/proxies/working_proxies.txt",
        "exported_proxies/proxies_latest.txt"
    ]
    
    proxy_list = sorted(list(all_proxies))
    
    for location in locations:
        with open(location, 'w') as f:
            for proxy in proxy_list:
                f.write(f"{proxy}\n")
        print(f"[+] Saved to: {location}")
    
    print(f"\n[+] Total unique proxies found: {len(proxy_list)}")
    
    # Show first 5 as examples
    if proxy_list:
        print("\n[*] Example proxies:")
        for proxy in proxy_list[:5]:
            print(f"    {proxy}")
    
    return proxy_list

def test_single_proxy(proxy, timeout=5):
    """Test a single proxy"""
    test_url = "http://httpbin.org/ip"
    
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        response = requests.get(test_url, proxies=proxies, timeout=timeout)
        if response.status_code == 200:
            return True
    except:
        pass
    
    return False

def main():
    print("=" * 50)
    print("Simple Proxy Fetcher")
    print("=" * 50)
    print()
    
    # Fetch proxies
    proxies = fetch_proxies()
    
    if not proxies:
        print("\n[-] No proxies found. Check internet connection.")
        return
    
    # Test a few
    print("\n[*] Testing first 5 proxies...")
    working = 0
    
    for i, proxy in enumerate(proxies[:5]):
        print(f"[*] Testing {i+1}/5: {proxy}...", end=' ')
        if test_single_proxy(proxy):
            print("[OK]")
            working += 1
        else:
            print("[FAIL]")
    
    print(f"\n[+] {working} out of 5 tested proxies are working")
    print("\n[+] Done! You can now run ultidork_master.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()