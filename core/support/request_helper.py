import random
import requests
from Core.Support.ua_manager import UserAgentManager
from Core.Support.proxy_manager import ProxyManager

ua_mgr = UserAgentManager()
proxy_mgr = ProxyManager()

class RequestHelper:

    @staticmethod
    def get(url, max_retries=3, timeout=10):
        for attempt in range(max_retries):
            headers = {'User-Agent': ua_mgr.get_random_ua()}
            proxy = proxy_mgr.get_random_proxy()
            proxies = {"http": proxy, "https": proxy} if proxy else {}

            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                return response
            except requests.RequestException:
                continue  # Retry silently on error
        return None  # All attempts failed

    @staticmethod
    def post(url, data=None, json=None, max_retries=3, timeout=10):
        for attempt in range(max_retries):
            headers = {'User-Agent': ua_mgr.get_random_ua()}
            proxy = proxy_mgr.get_random_proxy()
            proxies = {"http": proxy, "https": proxy} if proxy else {}

            try:
                response = requests.post(url, data=data, json=json, headers=headers, proxies=proxies, timeout=timeout)
                return response
            except requests.RequestException:
                continue
        return None
