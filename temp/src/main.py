import sys
import json
import time
import socket
from pathlib import Path
from urllib.parse import urlparse
from colorama import Fore, Style, init

init(autoreset=True)  # Colorama init

TARGET_JSON = "target_list.json"
TARGET_TXT = "target_list.txt"


def load_targets():
    """Load domain targets from .json or .txt"""
    targets = []

    json_path = Path(TARGET_JSON)
    txt_path = Path(TARGET_TXT)

    if json_path.exists():
        print(f"{Fore.CYAN}[+] Loading targets from {json_path}{Style.RESET_ALL}")
        with open(json_path, "r") as f:
            try:
                raw = json.load(f)
                # Defensive clean-up: remove blank or invalid entries
                targets = [t.strip() for t in raw if isinstance(t, str) and t.strip()]
            except Exception as e:
                print(f"{Fore.RED}[-] JSON load error: {e}{Style.RESET_ALL}")
                sys.exit(1)
    elif txt_path.exists():
        print(f"{Fore.CYAN}[+] Loading targets from {txt_path}{Style.RESET_ALL}")
        with open(txt_path, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    else:
        print(f"{Fore.RED}[-] No target list found (.json or .txt).{Style.RESET_ALL}")
        sys.exit(1)

    if not targets:
        print(f"{Fore.RED}[-] No valid targets to scan.{Style.RESET_ALL}")
        sys.exit(1)

    return targets


def basic_scan(domain):
    """Simple reachability check, resolves domain and pings port 80"""
    print(f"{Fore.YELLOW}[>] Scanning: {domain}{Style.RESET_ALL}")
    try:
        parsed = urlparse(domain)  # Handles raw domains or full URLs
        host = parsed.netloc or parsed.path

        ip = socket.gethostbyname(host)
        print(f"{Fore.GREEN}[+] Resolved {host} to {ip}{Style.RESET_ALL}")

        with socket.create_connection((ip, 80), timeout=5):
            print(f"{Fore.GREEN}[✔] Port 80 reachable on {host}{Style.RESET_ALL}")

    except socket.gaierror:
        print(f"{Fore.RED}[-] DNS resolution failed for {domain}{Style.RESET_ALL}")
    except (ConnectionRefusedError, TimeoutError):
        print(f"{Fore.RED}[-] Port 80 unreachable on {domain}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[-] Unexpected error scanning {domain}: {e}{Style.RESET_ALL}")


def main():
    if len(sys.argv) > 1:
        domain = sys.argv[1]
        print(f"{Fore.CYAN}[>] Single domain scan mode: {domain}{Style.RESET_ALL}")
        basic_scan(domain)
    else:
        targets = load_targets()
        print(f"{Fore.CYAN}[+] Loaded {len(targets)} targets.{Style.RESET_ALL}\n")

        for domain in targets:
            basic_scan(domain)
            time.sleep(1)  # Optional pause between scans

    print(f"\n{Fore.GREEN}[✓] Scanning complete.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
