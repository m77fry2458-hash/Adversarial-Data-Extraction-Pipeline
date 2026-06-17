import time
import logging
from queue import Queue
from dataclasses import dataclass

@dataclass
class AccountState:
    username: str
    token: str
    queries_made: int
    is_banned: bool
    last_used: float

class DynamicAccountStateMachine:
    """
    Manages account rotation and query limits to prevent permanent bans.
    Hot-swaps accounts when limits are approached.
    """
    def __init__(self, max_queries_per_account: int):
        self.account_pool = Queue()
        self.max_queries = max_queries_per_account
        self.active_account = None

    def load_accounts(self, accounts_list: list):
        for acc in accounts_list:
            self.account_pool.put(AccountState(acc['user'], acc['token'], 0, False, 0.0))

    def get_active_session(self) -> AccountState:
        """Rotates to the next healthy account if the current one hits the threshold."""
        if not self.active_account or self.active_account.queries_made >= self.max_queries:
            self._rotate_account()
        return self.active_account

    def _rotate_account(self):
        if self.active_account and not self.active_account.is_banned:
            # Cool down the exhausted account
            self.active_account.last_used = time.time()
            self.account_pool.put(self.active_account)
        
        # Fetch a fresh account
        self.active_account = self.account_pool.get()
        self.active_account.queries_made = 0
        logging.info(f"Swapped to account: {self.active_account.username}")

    def report_ban(self):
        """Flags an account as burned and immediately rotates."""
        logging.warning(f"Account burned: {self.active_account.username}")
        self.active_account.is_banned = True
        self._rotate_account()
