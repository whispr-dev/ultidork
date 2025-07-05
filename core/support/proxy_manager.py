import random

class ProxyManager:
    def __init__(self, proxy_file="Proxy_list.txt"):
        self.proxy_file = proxy_file
        self.proxies = self.load_proxies()

    def load_proxies(self):
        try:
            with open(self.proxy_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
