import json
import datetime

from base_executor import BaseExecutor
import json
import datetime

class ExecutorBulenox(BaseExecutor):
    def __init__(self, signal=None, stopLoss=None, takeProfit=None, risk_percent=1.0, max_trades_per_day=6):
        super().__init__(signal, stopLoss, takeProfit)
        self.risk_percent = risk_percent
        self.max_trades_per_day = max_trades_per_day
        self.trades_executed = 0
        self.log_file = "logs/bulenox_trades.json"

    def execute_trade(self):
        if not self.signal:
            print("No signal provided, skipping trade")
            return False

        symbol = self.signal.get('symbol')
        side = self.signal.get('side')
        quantity = self.signal.get('quantity')

        if not symbol or not side or not quantity:
            print("Incomplete signal data, skipping trade")
            return False

        order_details = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "stopLoss": self.stopLoss,
            "takeProfit": self.takeProfit
        }

        reason = "Trade executed from signal"

        if self.trades_executed >= self.max_trades_per_day:
            print("Trade limit reached for Bulenox. Skipping order.")
            return False

        self.trades_executed += 1
        self.log_trade(order_details, reason)
        return True

    def log_trade(self, order_details, reason):
        trade_log = {
            "timestamp": datetime.datetime.now().isoformat(),
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

    def health(self):
        # Placeholder health check logic
        try:
            # Implement actual health check logic here
            return {"status": "ok", "details": "Bulenox executor is healthy"}
        except Exception as e:
            return {"status": "error", "details": str(e)}