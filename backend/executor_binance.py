import os
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

from base_executor import BaseExecutor
import os
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

class BinanceExecutor(BaseExecutor):
    def __init__(self, signal=None, stopLoss=None, takeProfit=None):
        super().__init__(signal, stopLoss, takeProfit)
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        if not self.api_key or not self.api_secret:
            raise ValueError('Binance API key and secret must be set in .env file')
        self.client = Client(self.api_key, self.api_secret)
        self.trade_log_file = 'logs/binance_trades.log'
        self.daily_trade_limit = 10
        self.trade_count = 0
        self.trade_reset_time = datetime.now(timezone.utc) + timedelta(days=1)

        logging.basicConfig(filename=self.trade_log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

    def _reset_trade_count_if_needed(self):
        if datetime.now(timezone.utc) >= self.trade_reset_time:
            self.trade_count = 0
            self.trade_reset_time = datetime.now(timezone.utc) + timedelta(days=1)

    def log_trade(self, symbol, side, quantity, price):
        logging.info(f'Trade executed: {symbol} {side} {quantity} @ {price}')

    def get_balance(self, asset):
        try:
            balance = self.client.get_asset_balance(asset)
            return float(balance['free']) if balance else 0.0
        except Exception as e:
            logging.error(f'Error fetching balance for {asset}: {e}')
            return 0.0

    def get_open_orders(self, symbol):
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            return orders
        except Exception as e:
            logging.error(f'Error fetching open orders for {symbol}: {e}')
            return []

    def place_order(self, symbol, side, quantity, order_type='MARKET'):
        self._reset_trade_count_if_needed()
        if self.trade_count >= self.daily_trade_limit:
            logging.warning('Daily trade limit reached, skipping order')
            return None
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity
            )
            self.trade_count += 1
            self.log_trade(symbol, side, quantity, order.get('fills', [{}])[0].get('price', 'N/A'))
            return order
        except Exception as e:
            logging.error(f'Error placing order for {symbol}: {e}')
            return None

    def execute_trade(self):
        confidence_threshold = 0.7
        if not self.signal or self.signal.get('confidence', 0) < confidence_threshold:
            logging.info('Signal confidence too low, skipping trade')
            return None

        symbol = self.signal.get('symbol')
        side = self.signal.get('side')
        quantity = self.signal.get('quantity')

        if not symbol or not side or not quantity:
            logging.warning('Incomplete signal data, skipping trade')
            return None

        order = self.place_order(symbol, side, quantity)

        if order:
            self.log_trade(symbol, side, quantity, order.get('fills', [{}])[0].get('price', 'N/A'))
            if self.stopLoss or self.takeProfit:
                logging.info(f"Stop Loss: {self.stopLoss}, Take Profit: {self.takeProfit} for {symbol}")
        return order

    def health(self):
        try:
            # Simple health check by fetching account info
            account_info = self.client.get_account()
            return {"status": "ok", "details": "Connected to Binance API"}
        except Exception as e:
            return {"status": "error", "details": str(e)}


if __name__ == '__main__':
    executor = BinanceExecutor()
    print('BinanceExecutor is ready to execute trades.')