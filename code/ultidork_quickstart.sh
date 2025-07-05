#!/bin/bash
# OmniDork Quick Start Script
# ==========================
# This script sets up and runs the integrated OmniDork system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Banner
echo -e "${CYAN}"
cat << "EOF"
   ____                  _ _____             _    
  / __ \                (_)  __ \           | |   
 | |  | |_ __ ___  _ __  _| |  | | ___  _ __| | __
 | |  | | '_ ` _ \| '_ \| | |  | |/ _ \| '__| |/ /
 | |__| | | | | | | | | | | |__| | (_) | |  |   < 
  \____/|_| |_| |_|_| |_|_|_____/ \___/|_|  |_|\_\
                                                   
        Unified Scanner & Evasion Framework
EOF
echo -e "${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create directory if it doesn't exist
ensure_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}[+]${NC} Created directory: $1"
    fi
}

# Check prerequisites
echo -e "${YELLOW}[*]${NC} Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    echo -e "${RED}[!]${NC} Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check Rust (for OmniDork)
if ! command_exists cargo; then
    echo -e "${YELLOW}[!]${NC} Rust is not installed. Installing via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

# Check Chrome/Chromium
if ! command_exists google-chrome && ! command_exists chromium-browser; then
    echo -e "${YELLOW}[!]${NC} Chrome/Chromium not found. Installing Chromium..."
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y chromium-browser
    elif command_exists brew; then
        brew install --cask chromium
    else
        echo -e "${RED}[!]${NC} Please install Chrome or Chromium manually"
    fi
fi

# Setup directory structure
echo -e "${YELLOW}[*]${NC} Setting up directory structure..."
ensure_dir "data/proxies"
ensure_dir "data/findings"
ensure_dir "data/exports"
ensure_dir "data/logs"
ensure_dir "data/accounts"
ensure_dir "config"
ensure_dir "exported_proxies"
ensure_dir "logs"

# Install Python dependencies
echo -e "${YELLOW}[*]${NC} Installing Python dependencies..."
pip3 install -r requirements.txt 2>/dev/null || {
    echo -e "${YELLOW}[!]${NC} requirements.txt not found, installing common dependencies..."
    pip3 install aiohttp beautifulsoup4 colorama selenium selenium-wire \
                 undetected-chromedriver cryptography discord.py requests \
                 flask gunicorn asyncio argparse
}

# Build Rust components (if source available)
if [ -f "Cargo.toml" ]; then
    echo -e "${YELLOW}[*]${NC} Building Rust components..."
    cargo build --release
fi

# Create default configuration files if they don't exist
echo -e "${YELLOW}[*]${NC} Creating default configuration files..."

# Create proxy sources file
if [ ! -f "config/proxy_sources.txt" ]; then
    cat > config/proxy_sources.txt << 'EOF'
https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt
https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt
https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt
https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt
https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt
https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all
https://www.proxy-list.download/api/v1/get?type=http
EOF
    echo -e "${GREEN}[+]${NC} Created config/proxy_sources.txt"
fi

# Create user agents file
if [ ! -f "config/user_agents.txt" ]; then
    cat > config/user_agents.txt << 'EOF'
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0
Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1
Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1
Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0
Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.116 Mobile Safari/537.36
EOF
    echo -e "${GREEN}[+]${NC} Created config/user_agents.txt"
fi

# Create example accounts file
if [ ! -f "data/accounts/my_accounts.json" ]; then
    cat > data/accounts/my_accounts.json << 'EOF'
[
  {
    "email": "example@email.com",
    "password": "example_password",
    "notes": "Replace with real accounts"
  }
]
EOF
    echo -e "${GREEN}[+]${NC} Created data/accounts/my_accounts.json (UPDATE WITH REAL ACCOUNTS!)"
fi

# Create crawl targets file
if [ ! -f "config/crawl_targets.txt" ]; then
    cat > config/crawl_targets.txt << 'EOF'
# Bug Bounty Platforms
https://hackerone.com/directory/programs
https://bugcrowd.com/programs
https://www.intigriti.com/programs
https://www.yeswehack.com/programs

# Security Resources
https://owasp.org/www-project-top-ten/
https://portswigger.net/web-security
https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html

# Tech News Sites (for testing paywall bypass)
https://medium.com/topic/technology
https://www.wired.com/
https://techcrunch.com/

# Add your own targets below:
EOF
    echo -e "${GREEN}[+]${NC} Created config/crawl_targets.txt"
fi

# Function to run proxy scanner
run_proxy_scanner() {
    echo -e "${CYAN}[*] Starting RapidProxyScan...${NC}"
    python3 rapidproxyscan-v-0-4-0.py --single-run --connections 1000 --validation-rounds 2
}

# Function to run OmniDork scanner
run_omnidork_scanner() {
    if [ -f "target/release/omnidork" ]; then
        echo -e "${CYAN}[*] Starting OmniDork Scanner...${NC}"
        ./target/release/omnidork
    else
        echo -e "${YELLOW}[!]${NC} OmniDork binary not found. Using Python unified scanner..."
        python3 omnidork_scanner.py "$@"
    fi
}

# Function to run viewbot
run_viewbot() {
    echo -e "${CYAN}[*] Starting Supreme Viewbot...${NC}"
    echo -e "${YELLOW}Enter target URL:${NC}"
    read -r target_url
    echo -e "${YELLOW}Enter mode (medium/youtube/vote):${NC}"
    read -r mode
    python3 main.py --mode "$mode" --target "$target_url" --count 5
}

# Main menu
show_menu() {
    echo -e "\n${CYAN}=== OmniDork Main Menu ===${NC}"
    echo -e "${YELLOW}1.${NC} Run Proxy Scanner (RapidProxyScan)"
    echo -e "${YELLOW}2.${NC} Run OSINT Scanner (OmniDork)"
    echo -e "${YELLOW}3.${NC} Run Viewbot/Engagement Bot"
    echo -e "${YELLOW}4.${NC} Run Full Integrated Scan"
    echo -e "${YELLOW}5.${NC} Update Proxy Lists"
    echo -e "${YELLOW}6.${NC} Check System Status"
    echo -e "${YELLOW}7.${NC} Exit"
    echo -e "${CYAN}========================${NC}"
    echo -n "Select option: "
}

# System status check
check_status() {
    echo -e "\n${CYAN}=== System Status ===${NC}"
    
    # Check proxy count
    if [ -d "exported_proxies" ]; then
        proxy_count=$(find exported_proxies -name "proxies_*.txt" -mtime -1 | wc -l)
        echo -e "${GREEN}[+]${NC} Recent proxy lists: $proxy_count"
    fi
    
    # Check Python dependencies
    echo -e "${GREEN}[+]${NC} Python version: $(python3 --version)"
    
    # Check Rust installation
    if command_exists cargo; then
        echo -e "${GREEN}[+]${NC} Rust version: $(rustc --version)"
    fi
    
    # Check Chrome
    if command_exists google-chrome; then
        echo -e "${GREEN}[+]${NC} Chrome installed"
    elif command_exists chromium-browser; then
        echo -e "${GREEN}[+]${NC} Chromium installed"
    fi
    
    # Check disk space
    echo -e "${GREEN}[+]${NC} Free disk space: $(df -h . | awk 'NR==2 {print $4}')"
}

# Main loop
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            run_proxy_scanner
            ;;
        2)
            echo -e "${YELLOW}Enter target domain:${NC}"
            read -r target
            run_omnidork_scanner "$target"
            ;;
        3)
            run_viewbot
            ;;
        4)
            echo -e "${YELLOW}Enter target domain for full scan:${NC}"
            read -r target
            echo -e "${CYAN}[*] Running integrated scan...${NC}"
            
            # First get proxies
            run_proxy_scanner
            
            # Then run OmniDork with proxies
            run_omnidork_scanner "$target"
            ;;
        5)
            echo -e "${CYAN}[*] Updating proxy lists...${NC}"
            run_proxy_scanner
            ;;
        6)
            check_status
            ;;
        7)
            echo -e "${GREEN}[+]${NC} Exiting OmniDork. Happy hunting!"
            exit 0
            ;;
        *)
            echo -e "${RED}[!]${NC} Invalid option"
            ;;
    esac
done