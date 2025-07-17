import json
import datetime
import os
from dotenv import load_dotenv

class ExecutorMulti:
    def __init__(self, risk_percent=1.0, max_trades_per_day=6, accounts_file="accounts.json"):
        self.risk_percent = risk_percent
        self.max_trades_per_day = max_trades_per_day
        self.trades_executed = 0
        self.accounts_file = accounts_file
        self.accounts = self.load_accounts()
        self.log_file = "logs/multi_trades.json"

    def load_accounts(self):
        load_dotenv()
        accounts = []
        # Try to load from .env
        env_accounts = os.getenv("FUNDED_ACCOUNTS")
        if env_accounts:
            accounts = env_accounts.split(",")
        else:
            # Try to load from accounts.json
            try:
                with open(self.accounts_file, "r") as f:
                    accounts = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                accounts = []
        return accounts

    def place_order(self, account, order_details, reason):
        if self.trades_executed >= self.max_trades_per_day:
            print("Trade limit reached for multi-account. Skipping order.")
            return False
        # Implement order placement logic for the given account
        self.trades_executed += 1
        self.log_trade(account, order_details, reason)
        return True

    def log_trade(self, account, order_details, reason):
        trade_log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "account": account,
            "risk_percent": self.risk_percent,
            "order_details": order_details,
            "reason": reason,
            "profit_loss": None
        }
        try:
            with open(self.log_file, "r") as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        logs.append(trade_log)
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)