## D:\osint\ultidork\code\core\user_agent.py
import random
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class UserAgentManager:
    """
    Manages a pool of user agents for rotating requests.
    This can be expanded to categorize by OS, browser, etc.
    """
    def __init__(self, user_agents: Optional[List[str]] = None):
        if user_agents:
            self.user_agents = user_agents
        else:
            # Default list of common user agents if none provided
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/126.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/126.0",
                "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36"
            ]
        logger.debug(f"UserAgentManager initialized with {len(self.user_agents)} user agents.")

    def get_random_user_agent(self) -> str:
        """Returns a random user agent from the pool."""
        if not self.user_agents:
            logger.warning("User agent pool is empty. Returning a generic user agent.")
            return "Mozilla/5.0 (compatible; MyCustomScanner/1.0)"
        return random.choice(self.user_agents)

    def add_user_agent(self, user_agent: str):
        """Adds a new user agent to the pool."""
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
            logger.debug(f"Added user agent: {user_agent}")
        else:
            logger.debug(f"User agent already in pool: {user_agent}")

    def add_user_agents(self, user_agent_list: List[str]):
        """Adds multiple user agents to the pool."""
        for ua in user_agent_list:
            self.add_user_agent(ua)
