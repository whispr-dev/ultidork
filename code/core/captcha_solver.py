# core/captcha_solver.py

import time
import logging
import requests
import os

class CaptchaSolver:
    def __init__(self, api_key=None, max_retries=30, poll_delay=5):
        # Check for API key in multiple places
        self.api_key = (
            api_key or 
            os.getenv("2CAPTCHA_API") or  # Your specific env var
            os.getenv("CAPTCHA_API_KEY") or  # Original env var
            os.getenv("TWOCAPTCHA_API_KEY")  # Common alternative
        )

       
        self.max_retries = max_retries
        self.poll_delay = poll_delay
        
        # Make it optional - just warn if not found
        if not self.api_key:
            logging.warning("[CaptchaSolver] No captcha API key found. Captcha solving disabled.")
            # Don't raise exception - just disable functionality

    def solve(self, site_key, page_url):
        if not self.api_key:
            logging.warning("[CaptchaSolver] No API key configured. Cannot solve captcha.")
            return None
            
        logging.info(f"[CaptchaSolver] Requesting CAPTCHA solve for {page_url}")
        payload = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        try:
            response = requests.post('http://2captcha.com/in.php', data=payload)
            response_data = response.json()
            if response_data.get("status") != 1:
                raise Exception(f"[CaptchaSolver] Submission error: {response_data}")
            captcha_id = response_data["request"]

            result_payload = {
                'key': self.api_key,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }

            for attempt in range(self.max_retries):
                time.sleep(self.poll_delay)
                result = requests.get('http://2captcha.com/res.php', params=result_payload).json()
                if result.get("status") == 1:
                    logging.info("[CaptchaSolver] CAPTCHA solved successfully.")
                    return result["request"]
                logging.info(f"[CaptchaSolver] Attempt {attempt+1}/{self.max_retries}: {result.get('request')}")
        except Exception as e:
            logging.error(f"[CaptchaSolver] Exception during solving: {e}")
        return None

    def solve_and_inject(self, driver, site_key, page_url):
        if not self.api_key:
            logging.warning("[CaptchaSolver] No API key configured. Skipping captcha.")
            return False
            
        token = self.solve(site_key, page_url)
        if token:
            try:
                driver.execute_script(
                    f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
                )
                logging.info("[CaptchaSolver] CAPTCHA token injected into DOM.")
                return True
            except Exception as e:
                logging.error(f"[CaptchaSolver] Failed to inject CAPTCHA response: {e}")
        else:
            logging.error("[CaptchaSolver] Failed to solve CAPTCHA.")
        return False