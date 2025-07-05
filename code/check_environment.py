#!/usr/bin/env python3
"""
Environment Setup Checker for OmniDork
=====================================
Run this to verify all your environment variables and dependencies are set up correctly.
"""

import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)

def check_env():
    print(f"{Fore.CYAN}=== OmniDork Environment Check ==={Style.RESET_ALL}\n")
    
    # Check for captcha API key
    captcha_keys = [
        ("2CAPTCHA_API", os.getenv("2CAPTCHA_API")),
        ("CAPTCHA_API_KEY", os.getenv("CAPTCHA_API_KEY")),
        ("TWOCAPTCHA_API_KEY", os.getenv("TWOCAPTCHA_API_KEY"))
    ]
    
    print(f"{Fore.YELLOW}[*] Captcha API Keys:{Style.RESET_ALL}")
    captcha_found = False
    for key_name, key_value in captcha_keys:
        if key_value:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {key_name}: {'*' * 10}{key_value[-4:]}")  # Show last 4 chars
            captcha_found = True
        else:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {key_name}: Not set")
    
    if not captcha_found:
        print(f"\n  {Fore.YELLOW}ℹ{Style.RESET_ALL} No captcha API key found. Captcha solving will be disabled.")
        print(f"  {Fore.YELLOW}ℹ{Style.RESET_ALL} You have it as '2CAPTCHA_API' in your environment.")
    
    # Check for webhook URLs
    print(f"\n{Fore.YELLOW}[*] Webhook Configuration:{Style.RESET_ALL}")
    webhook_vars = [
        ("WEBHOOK_URL", os.getenv("WEBHOOK_URL")),
        ("DISCORD_WEBHOOK_URL", os.getenv("DISCORD_WEBHOOK_URL")),
        ("DISCORD_BOT_TOKEN", os.getenv("DISCORD_BOT_TOKEN"))
    ]
    
    for var_name, var_value in webhook_vars:
        if var_value:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {var_name}: Set")
        else:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {var_name}: Not set")
    
    # Check for proxy configuration
    print(f"\n{Fore.YELLOW}[*] Proxy Configuration:{Style.RESET_ALL}")
    if os.path.exists("data/working_proxies.txt"):
        with open("data/working_proxies.txt", "r") as f:
            proxy_count = len([line for line in f if line.strip()])
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Working proxies file: {proxy_count} proxies")
    else:
        print(f"  {Fore.RED}✗{Style.RESET_ALL} No working_proxies.txt found")
    
    if os.path.exists("exported_proxies"):
        import glob
        proxy_files = glob.glob("exported_proxies/proxies_*.txt")
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Exported proxy files: {len(proxy_files)} files")
    else:
        print(f"  {Fore.YELLOW}ℹ{Style.RESET_ALL} No exported_proxies directory")
    
    # Check for accounts
    print(f"\n{Fore.YELLOW}[*] Account Configuration:{Style.RESET_ALL}")
    if os.path.exists("data/accounts/my_accounts.json"):
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Accounts file exists")
    else:
        print(f"  {Fore.RED}✗{Style.RESET_ALL} No accounts file found at data/accounts/my_accounts.json")
    
    # Check Python dependencies
    print(f"\n{Fore.YELLOW}[*] Python Dependencies:{Style.RESET_ALL}")
    required_modules = [
        "aiohttp", "beautifulsoup4", "colorama", "selenium", 
        "requests", "cryptography"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {module}")
        except ImportError:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {module} - Not installed")
    
    print(f"\n{Fore.CYAN}=== Check Complete ==={Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}To use your 2CAPTCHA_API key, the system will automatically detect it.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}You can now run: python ultidork_master.py whispr.dev --mode full{Style.RESET_ALL}")

if __name__ == "__main__":
    check_env()