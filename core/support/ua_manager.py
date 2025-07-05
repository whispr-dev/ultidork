import random

class UserAgentManager:
    def __init__(self, ua_file="Useragent.txt"):
        self.ua_file = ua_file
        self.user_agents = self.load_user_agents()

    def load_user_agents(self):
        try:
            with open(self.ua_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def get_random_ua(self):
        if not self.user_agents:
            return "Mozilla/5.0 (compatible; YourScanner/1.0)"
        return random.choice(self.user_agents)
