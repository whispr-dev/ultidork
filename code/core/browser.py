# C:\Users\phine\Documents\ultidork\core\browser.py (or your new path)
import logging
import random
import asyncio
from typing import Optional, Dict, Any

# Selenium imports - ensure these are installed via requirements.txt
try:
    # IMPORTANT: We are NOT importing from seleniumwire here because we removed it.
    # We are importing from the standard `selenium` library.
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except ImportError:
        # If Selenium is not installed, provide a dummy class to avoid breaking
        logging.warning("Selenium or webdriver_manager not found. BrowserController will be a dummy.")
        webdriver = None
        ChromeService = None
        ChromeDriverManager = None
        ChromeOptions = None


logger = logging.getLogger(__name__)

class BrowserController:
        """
        Manages browser instances for web scraping, paywall bypass, and CAPTCHA solving.
        Uses Selenium with ChromeDriver.
        """
        def __init__(self, headless: bool = True, proxy: Optional[str] = None):
            self.headless = headless
            self.proxy = proxy # Optional proxy for the browser itself
            self.driver: Optional[Any] = None # Use Any since webdriver.Chrome might be None
            
            if webdriver: # Only try to initialize if selenium is available
                self._initialize_driver()
            else:
                logger.error("Selenium not installed. BrowserController cannot function.")


        def _initialize_driver(self):
            """Initializes the Chrome WebDriver."""
            if not ChromeDriverManager or not ChromeService or not ChromeOptions or not webdriver:
                logger.error("Cannot initialize WebDriver: Missing Selenium components or `webdriver` is None.")
                return

            logger.info(f"Initializing Chrome WebDriver (headless: {self.headless})...")
            chrome_options = ChromeOptions()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-browser-side-navigation")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument(f"user-agent={self._get_random_user_agent()}")

            if self.proxy:
                logger.info(f"Setting browser proxy to: {self.proxy}")
                chrome_options.add_argument(f"--proxy-server={self.proxy}")
                # Consider adding proxy authentication here if your proxies require it
                # chrome_options.add_argument(f"--proxy-auth={username}:{password}")

            try:
                service = ChromeService(executable_path=ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome WebDriver initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Chrome WebDriver: {e}")
                self.driver = None # Ensure driver is None on failure

        def _get_random_user_agent(self) -> str:
            """Provides a simple random user agent."""
            # This should ideally come from extended_user_agents.py
            # For a core component, a simple internal list is fine as a fallback
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
            ]
            return random.choice(user_agents)


        def get_driver(self) -> Optional[Any]: # Use Any for return type
            """Returns the WebDriver instance."""
            if not self.driver:
                logger.warning("WebDriver is not initialized. Attempting to re-initialize.")
                self._initialize_driver() # Try to re-initialize if it's None
            return self.driver

        def close_driver(self):
                """Closes the WebDriver instance."""
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                    logger.info("Chrome WebDriver closed.")

        async def get_page_content(self, url: str, wait_time: int = 5) -> str:
                """Navigates to a URL and returns page content."""
                if not self.driver:
                    logger.error(f"Cannot get page content for {url}: WebDriver not available.")
                    return ""
                try:
                    self.driver.get(url)
                    await asyncio.sleep(wait_time) # Simulate waiting for page load
                    return self.driver.page_source
                except Exception as e:
                    logger.error(f"Error getting page content for {url}: {e}")
                    return ""
    