# config.py - Working Configuration
import os

# Proxy Sources - These are actual working sources
PROXY_SOURCES = [
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt',
    'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all',
    'https://www.proxy-list.download/api/v1/get?type=http',
    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
]

# Scanner settings
CHECK_INTERVAL = 30
CONNECTION_LIMIT = 100
VALIDATION_ROUNDS = 2
VALIDATION_MODE = 'any'
TIMEOUT = 5.0
CHECK_ANONYMITY = False
FORCE_FETCH = True
SINGLE_RUN = True
VERBOSE = True
