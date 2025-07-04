# core/account.py
import json
from pathlib import Path

class AccountManager:
    def __init__(self, account_file="data/accounts/my_accounts.json"):
        self.accounts = []
        self.account_file = Path(account_file)
        self._load_accounts()
    
    def _load_accounts(self):
        if self.account_file.exists():
            try:
                with open(self.account_file, 'r') as f:
                    self.accounts = json.load(f)
            except:
                self.accounts = []
    
    def get_random_account(self):
        if self.accounts:
            import random
            return random.choice(self.accounts)
        return {"email": "test@example.com", "password": "password123"}
