#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Backtesting Engine Module
Strategy testing and simulation using historical market data
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import requests
import time
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backtesting_engine.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"

class BacktestStatus(Enum):
    """Backtest status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class MarketData:
    """Market data point"""
    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    
@dataclass
class BacktestOrder:
    """Backtest order data structure"""
    id: str
    timestamp: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    status: str = "pending"
    strategy: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class BacktestTrade:
    """Backtest trade result"""
    id: str
    entry_time: str
    exit_time: Optional[str]
    symbol: str
    side: OrderSide
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float = 0.0
    pnl_percent: float = 0.0
    duration: Optional[float] = None  # in seconds
    strategy: Optional[str] = None
    slippage: float = 0.0
    commission: float = 0.0

@dataclass
class BacktestResult:
    """Backtest result summary"""
    id: str
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_duration: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    commission_paid: float
    slippage_cost: float
    trades: List[BacktestTrade]
    equity_curve: List[Tuple[str, float]]
    created_at: str

class StrategyEngine:
    """Strategy execution engine for backtesting"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.positions: Dict[str, float] = defaultdict(float)
        self.orders: List[BacktestOrder] = []
        self.trades: List[BacktestTrade] = []
        self.cash = config.get('initial_capital', 10000.0)
        self.equity_history: List[Tuple[str, float]] = []
        
    def on_data(self, data: MarketData) -> List[BacktestOrder]:
        """Process market data and generate orders"""
        # This method should be overridden by specific strategies
        return []
    
    def calculate_position_size(self, symbol: str, price: float, risk_percent: float = 0.02) -> float:
        """Calculate position size based on risk management"""
        risk_amount = self.cash * risk_percent
        return risk_amount / price
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value"""
        portfolio_value = self.cash
        for symbol, quantity in self.positions.items():
            if symbol in current_prices:
                portfolio_value += quantity * current_prices[symbol]
        return portfolio_value

class FVGMidpointStrategy(StrategyEngine):
    """Fair Value Gap Midpoint Strategy"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("FVG Midpoint", config)
        self.lookback_period = config.get('lookback_period', 20)
        self.fvg_threshold = config.get('fvg_threshold', 0.001)  # 0.1%
        self.position_size_percent = config.get('position_size_percent', 0.02)
        self.stop_loss_percent = config.get('stop_loss_percent', 0.02)
        self.take_profit_percent = config.get('take_profit_percent', 0.04)
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.lookback_period))
        
    def on_data(self, data: MarketData) -> List[BacktestOrder]:
        """FVG Midpoint strategy logic"""
        orders = []
        
        # Add current data to history
        self.price_history[data.symbol].append({
            'timestamp': data.timestamp,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume
        })
        
        # Need at least 3 candles to identify FVG
        if len(self.price_history[data.symbol]) < 3:
            return orders
        
        history = list(self.price_history[data.symbol])
        
        # Check for Fair Value Gap
        fvg = self.identify_fvg(history[-3:], data.symbol)
        if fvg:
            # Calculate midpoint
            midpoint = (fvg['high'] + fvg['low']) / 2
            
            # Check if current price is near midpoint
            price_diff = abs(data.close - midpoint) / midpoint
            if price_diff <= self.fvg_threshold:
                # Generate order based on FVG direction
                quantity = self.calculate_position_size(data.symbol, data.close, self.position_size_percent)
                
                if fvg['direction'] == 'bullish' and self.positions[data.symbol] <= 0:
                    # Buy order
                    order = BacktestOrder(
                        id=f"fvg_buy_{data.symbol}_{data.timestamp}",
                        timestamp=data.timestamp,
                        symbol=data.symbol,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                        price=data.close,
                        strategy=self.name,
                        metadata={
                            'fvg_midpoint': midpoint,
                            'fvg_direction': fvg['direction'],
                            'stop_loss': data.close * (1 - self.stop_loss_percent),
                            'take_profit': data.close * (1 + self.take_profit_percent)
                        }
                    )
                    orders.append(order)
                    
                elif fvg['direction'] == 'bearish' and self.positions[data.symbol] >= 0:
                    # Sell order
                    order = BacktestOrder(
                        id=f"fvg_sell_{data.symbol}_{data.timestamp}",
                        timestamp=data.timestamp,
                        symbol=data.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                        price=data.close,
                        strategy=self.name,
                        metadata={
                            'fvg_midpoint': midpoint,
                            'fvg_direction': fvg['direction'],
                            'stop_loss': data.close * (1 + self.stop_loss_percent),
                            'take_profit': data.close * (1 - self.take_profit_percent)
                        }
                    )
                    orders.append(order)
        
        return orders
    
    def identify_fvg(self, candles: List[Dict], symbol: str) -> Optional[Dict[str, Any]]:
        """Identify Fair Value Gap in price data"""
        if len(candles) < 3:
            return None
        
        candle1, candle2, candle3 = candles
        
        # Bullish FVG: candle1 low > candle3 high
        if candle1['low'] > candle3['high']:
            return {
                'direction': 'bullish',
                'high': candle1['low'],
                'low': candle3['high'],
                'timestamp': candle2['timestamp']
            }
        
        # Bearish FVG: candle1 high < candle3 low
        if candle1['high'] < candle3['low']:
            return {
                'direction': 'bearish',
                'high': candle3['low'],
                'low': candle1['high'],
                'timestamp': candle2['timestamp']
            }
        
        return None

class BreakoutMomentumStrategy(StrategyEngine):
    """Breakout Momentum Strategy"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Breakout Momentum", config)
        self.lookback_period = config.get('lookback_period', 20)
        self.breakout_threshold = config.get('breakout_threshold', 0.02)  # 2%
        self.volume_threshold = config.get('volume_threshold', 1.5)  # 1.5x average volume
        self.position_size_percent = config.get('position_size_percent', 0.03)
        self.stop_loss_percent = config.get('stop_loss_percent', 0.03)
        self.take_profit_percent = config.get('take_profit_percent', 0.06)
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.lookback_period))
        
    def on_data(self, data: MarketData) -> List[BacktestOrder]:
        """Breakout momentum strategy logic"""
        orders = []
        
        # Add current data to history
        self.price_history[data.symbol].append({
            'timestamp': data.timestamp,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume
        })
        
        # Need sufficient history
        if len(self.price_history[data.symbol]) < self.lookback_period:
            return orders
        
        history = list(self.price_history[data.symbol])
        
        # Calculate resistance and support levels
        highs = [candle['high'] for candle in history[:-1]]  # Exclude current candle
        lows = [candle['low'] for candle in history[:-1]]
        volumes = [candle['volume'] for candle in history[:-1]]
        
        resistance = max(highs)
        support = min(lows)
        avg_volume = sum(volumes) / len(volumes)
        
        # Check for breakout
        current_volume_ratio = data.volume / avg_volume if avg_volume > 0 else 1
        
        # Bullish breakout
        if (data.close > resistance and 
            (data.close - resistance) / resistance >= self.breakout_threshold and
            current_volume_ratio >= self.volume_threshold and
            self.positions[data.symbol] <= 0):
            
            quantity = self.calculate_position_size(data.symbol, data.close, self.position_size_percent)
            
            order = BacktestOrder(
                id=f"breakout_buy_{data.symbol}_{data.timestamp}",
                timestamp=data.timestamp,
                symbol=data.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=quantity,
                price=data.close,
                strategy=self.name,
                metadata={
                    'breakout_level': resistance,
                    'volume_ratio': current_volume_ratio,
                    'stop_loss': data.close * (1 - self.stop_loss_percent),
                    'take_profit': data.close * (1 + self.take_profit_percent)
                }
            )
            orders.append(order)
        
        # Bearish breakout
        elif (data.close < support and 
              (support - data.close) / support >= self.breakout_threshold and
              current_volume_ratio >= self.volume_threshold and
              self.positions[data.symbol] >= 0):
            
            quantity = self.calculate_position_size(data.symbol, data.close, self.position_size_percent)
            
            order = BacktestOrder(
                id=f"breakout_sell_{data.symbol}_{data.timestamp}",
                timestamp=data.timestamp,
                symbol=data.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=quantity,
                price=data.close,
                strategy=self.name,
                metadata={
                    'breakout_level': support,
                    'volume_ratio': current_volume_ratio,
                    'stop_loss': data.close * (1 + self.stop_loss_percent),
                    'take_profit': data.close * (1 - self.take_profit_percent)
                }
            )
            orders.append(order)
        
        return orders

class BacktestingEngine:
    """Main backtesting engine"""
    
    def __init__(self, config_path: str = "automation/config/backtesting.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.db_path = Path("logs/backtests.db")
        self.data_cache: Dict[str, List[MarketData]] = {}
        self.strategies: Dict[str, StrategyEngine] = {}
        self.running_backtests: Dict[str, BacktestResult] = {}
        
        # Initialize database
        self.init_database()
        
        # Load strategies
        self.load_strategies()
        
        logger.info("BacktestingEngine initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load backtesting configuration"""
        default_config = {
            "data_sources": {
                "default": {
                    "type": "csv",
                    "path": "data/market_data",
                    "format": "OHLCV"
                },
                "alpha_vantage": {
                    "type": "api",
                    "api_key": "",
                    "base_url": "https://www.alphavantage.co/query"
                },
                "yahoo_finance": {
                    "type": "api",
                    "base_url": "https://query1.finance.yahoo.com/v8/finance/chart"
                }
            },
            "execution_settings": {
                "commission_rate": 0.001,  # 0.1%
                "slippage_rate": 0.0005,   # 0.05%
                "min_trade_amount": 10.0,
                "max_position_size": 0.1,  # 10% of portfolio
                "risk_free_rate": 0.02     # 2% annual
            },
            "strategies": {
                "fvg_midpoint": {
                    "enabled": True,
                    "initial_capital": 10000.0,
                    "lookback_period": 20,
                    "fvg_threshold": 0.001,
                    "position_size_percent": 0.02,
                    "stop_loss_percent": 0.02,
                    "take_profit_percent": 0.04
                },
                "breakout_momentum": {
                    "enabled": True,
                    "initial_capital": 10000.0,
                    "lookback_period": 20,
                    "breakout_threshold": 0.02,
                    "volume_threshold": 1.5,
                    "position_size_percent": 0.03,
                    "stop_loss_percent": 0.03,
                    "take_profit_percent": 0.06
                }
            },
            "backtest_settings": {
                "default_timeframe": "1h",
                "max_concurrent_backtests": 3,
                "save_detailed_logs": True,
                "generate_charts": True
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Deep merge with default config
                    self._deep_merge(default_config, config)
                    logger.info(f"Backtesting configuration loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading backtesting config: {e}, using defaults")
        else:
            # Create default config file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default backtesting configuration created at {self.config_path}")
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def init_database(self):
        """Initialize backtesting database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backtests (
                        id TEXT PRIMARY KEY,
                        strategy_name TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        initial_capital REAL NOT NULL,
                        final_capital REAL NOT NULL,
                        total_return REAL NOT NULL,
                        total_return_percent REAL NOT NULL,
                        max_drawdown REAL NOT NULL,
                        max_drawdown_percent REAL NOT NULL,
                        sharpe_ratio REAL NOT NULL,
                        win_rate REAL NOT NULL,
                        profit_factor REAL NOT NULL,
                        total_trades INTEGER NOT NULL,
                        winning_trades INTEGER NOT NULL,
                        losing_trades INTEGER NOT NULL,
                        avg_trade_duration REAL NOT NULL,
                        avg_win REAL NOT NULL,
                        avg_loss REAL NOT NULL,
                        largest_win REAL NOT NULL,
                        largest_loss REAL NOT NULL,
                        commission_paid REAL NOT NULL,
                        slippage_cost REAL NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        completed_at TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_trades (
                        id TEXT PRIMARY KEY,
                        backtest_id TEXT NOT NULL,
                        entry_time TEXT NOT NULL,
                        exit_time TEXT,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        quantity REAL NOT NULL,
                        pnl REAL NOT NULL,
                        pnl_percent REAL NOT NULL,
                        duration REAL,
                        strategy TEXT,
                        slippage REAL NOT NULL,
                        commission REAL NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (backtest_id) REFERENCES backtests (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        source TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(timestamp, symbol, source)
                    )
                """)
                
                conn.commit()
                logger.info("Backtesting database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing backtesting database: {e}")
    
    def load_strategies(self):
        """Load available strategies"""
        strategies_config = self.config.get('strategies', {})
        
        for strategy_name, config in strategies_config.items():
            if config.get('enabled', False):
                try:
                    if strategy_name == 'fvg_midpoint':
                        strategy = FVGMidpointStrategy(config)
                    elif strategy_name == 'breakout_momentum':
                        strategy = BreakoutMomentumStrategy(config)
                    else:
                        logger.warning(f"Unknown strategy: {strategy_name}")
                        continue
                    
                    self.strategies[strategy_name] = strategy
                    logger.info(f"Strategy '{strategy_name}' loaded")
                    
                except Exception as e:
                    logger.error(f"Error loading strategy '{strategy_name}': {e}")
    
    async def load_market_data(self, symbol: str, start_date: str, end_date: str, 
                              timeframe: str = "1h", source: str = "default") -> List[MarketData]:
        """Load market data for backtesting"""
        try:
            cache_key = f"{symbol}_{start_date}_{end_date}_{timeframe}_{source}"
            
            # Check cache first
            if cache_key in self.data_cache:
                logger.info(f"Using cached data for {symbol}")
                return self.data_cache[cache_key]
            
            # Check database
            data = await self.load_data_from_db(symbol, start_date, end_date, source)
            if data:
                self.data_cache[cache_key] = data
                return data
            
            # Load from external source
            data_source_config = self.config.get('data_sources', {}).get(source, {})
            
            if data_source_config.get('type') == 'csv':
                data = await self.load_data_from_csv(symbol, start_date, end_date, data_source_config)
            elif data_source_config.get('type') == 'api':
                data = await self.load_data_from_api(symbol, start_date, end_date, data_source_config)
            else:
                logger.error(f"Unsupported data source type: {data_source_config.get('type')}")
                return []
            
            # Cache and store in database
            if data:
                self.data_cache[cache_key] = data
                await self.store_data_in_db(data, source)
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading market data for {symbol}: {e}")
            return []
    
    async def load_data_from_db(self, symbol: str, start_date: str, end_date: str, 
                               source: str) -> List[MarketData]:
        """Load market data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, symbol, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = ? AND timestamp >= ? AND timestamp <= ? AND source = ?
                    ORDER BY timestamp
                """, (symbol, start_date, end_date, source))
                
                data = []
                for row in cursor.fetchall():
                    data.append(MarketData(
                        timestamp=row[0],
                        symbol=row[1],
                        open=row[2],
                        high=row[3],
                        low=row[4],
                        close=row[5],
                        volume=row[6]
                    ))
                
                return data
                
        except Exception as e:
            logger.error(f"Error loading data from database: {e}")
            return []
    
    async def load_data_from_csv(self, symbol: str, start_date: str, end_date: str, 
                                config: Dict[str, Any]) -> List[MarketData]:
        """Load market data from CSV files"""
        try:
            data_path = Path(config.get('path', 'data/market_data'))
            csv_file = data_path / f"{symbol}.csv"
            
            if not csv_file.exists():
                logger.warning(f"CSV file not found: {csv_file}")
                return []
            
            # Read CSV data
            df = pd.read_csv(csv_file)
            
            # Filter by date range
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
            
            # Convert to MarketData objects
            data = []
            for _, row in df.iterrows():
                data.append(MarketData(
                    timestamp=row['timestamp'].isoformat(),
                    symbol=symbol,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume'])
                ))
            
            logger.info(f"Loaded {len(data)} data points from CSV for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data from CSV: {e}")
            return []
    
    async def load_data_from_api(self, symbol: str, start_date: str, end_date: str, 
                                config: Dict[str, Any]) -> List[MarketData]:
        """Load market data from API"""
        try:
            # This is a simplified example - you would implement specific API calls
            # for different data providers (Alpha Vantage, Yahoo Finance, etc.)
            
            if 'alphavantage' in config.get('base_url', ''):
                return await self.load_from_alpha_vantage(symbol, start_date, end_date, config)
            elif 'yahoo' in config.get('base_url', ''):
                return await self.load_from_yahoo_finance(symbol, start_date, end_date, config)
            else:
                logger.error(f"Unsupported API source: {config.get('base_url')}")
                return []
                
        except Exception as e:
            logger.error(f"Error loading data from API: {e}")
            return []
    
    async def load_from_yahoo_finance(self, symbol: str, start_date: str, end_date: str, 
                                     config: Dict[str, Any]) -> List[MarketData]:
        """Load data from Yahoo Finance API (simplified example)"""
        try:
            # Convert dates to timestamps
            start_ts = int(pd.to_datetime(start_date).timestamp())
            end_ts = int(pd.to_datetime(end_date).timestamp())
            
            url = f"{config['base_url']}/{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': '1h',
                'includePrePost': 'false'
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                logger.error(f"API request failed: {response.status_code}")
                return []
            
            data_json = response.json()
            result = data_json.get('chart', {}).get('result', [])
            
            if not result:
                logger.warning(f"No data returned for {symbol}")
                return []
            
            # Parse the response
            timestamps = result[0].get('timestamp', [])
            ohlcv = result[0].get('indicators', {}).get('quote', [{}])[0]
            
            data = []
            for i, ts in enumerate(timestamps):
                if (i < len(ohlcv.get('open', [])) and 
                    ohlcv['open'][i] is not None and
                    ohlcv['high'][i] is not None and
                    ohlcv['low'][i] is not None and
                    ohlcv['close'][i] is not None and
                    ohlcv['volume'][i] is not None):
                    
                    data.append(MarketData(
                        timestamp=datetime.fromtimestamp(ts).isoformat(),
                        symbol=symbol,
                        open=float(ohlcv['open'][i]),
                        high=float(ohlcv['high'][i]),
                        low=float(ohlcv['low'][i]),
                        close=float(ohlcv['close'][i]),
                        volume=float(ohlcv['volume'][i])
                    ))
            
            logger.info(f"Loaded {len(data)} data points from Yahoo Finance for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading from Yahoo Finance: {e}")
            return []
    
    async def store_data_in_db(self, data: List[MarketData], source: str):
        """Store market data in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for item in data:
                    conn.execute("""
                        INSERT OR IGNORE INTO market_data 
                        (timestamp, symbol, open, high, low, close, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.timestamp,
                        item.symbol,
                        item.open,
                        item.high,
                        item.low,
                        item.close,
                        item.volume,
                        source
                    ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing data in database: {e}")
    
    async def run_backtest(self, strategy_name: str, symbol: str, start_date: str, 
                          end_date: str, initial_capital: float = 10000.0) -> Optional[str]:
        """Run a backtest for a specific strategy"""
        try:
            if strategy_name not in self.strategies:
                logger.error(f"Strategy not found: {strategy_name}")
                return None
            
            # Generate backtest ID
            backtest_id = f"backtest_{strategy_name}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Load market data
            logger.info(f"Loading market data for {symbol} from {start_date} to {end_date}")
            market_data = await self.load_market_data(symbol, start_date, end_date)
            
            if not market_data:
                logger.error(f"No market data available for {symbol}")
                return None
            
            # Initialize strategy
            strategy = self.strategies[strategy_name]
            strategy.cash = initial_capital
            strategy.positions.clear()
            strategy.orders.clear()
            strategy.trades.clear()
            strategy.equity_history.clear()
            
            # Run backtest
            logger.info(f"Running backtest {backtest_id}")
            result = await self.execute_backtest(backtest_id, strategy, market_data, initial_capital)
            
            if result:
                # Store result in database
                await self.store_backtest_result(result)
                self.running_backtests[backtest_id] = result
                logger.info(f"Backtest {backtest_id} completed successfully")
                return backtest_id
            else:
                logger.error(f"Backtest {backtest_id} failed")
                return None
                
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return None
    
    async def execute_backtest(self, backtest_id: str, strategy: StrategyEngine, 
                              market_data: List[MarketData], initial_capital: float) -> Optional[BacktestResult]:
        """Execute the actual backtest"""
        try:
            execution_settings = self.config.get('execution_settings', {})
            commission_rate = execution_settings.get('commission_rate', 0.001)
            slippage_rate = execution_settings.get('slippage_rate', 0.0005)
            
            open_positions: Dict[str, BacktestTrade] = {}
            completed_trades: List[BacktestTrade] = []
            equity_curve: List[Tuple[str, float]] = []
            
            # Process each data point
            for i, data_point in enumerate(market_data):
                # Generate orders from strategy
                orders = strategy.on_data(data_point)
                
                # Execute orders
                for order in orders:
                    await self.execute_order(order, data_point, strategy, open_positions, 
                                           completed_trades, commission_rate, slippage_rate)
                
                # Update equity curve
                current_prices = {data_point.symbol: data_point.close}
                portfolio_value = strategy.get_portfolio_value(current_prices)
                equity_curve.append((data_point.timestamp, portfolio_value))
                
                # Log progress
                if i % 100 == 0:
                    logger.info(f"Processed {i}/{len(market_data)} data points")
            
            # Close any remaining open positions
            final_data = market_data[-1]
            for trade in open_positions.values():
                trade.exit_time = final_data.timestamp
                trade.exit_price = final_data.close
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
                if trade.side == OrderSide.SELL:
                    trade.pnl = -trade.pnl
                trade.pnl_percent = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
                trade.duration = (pd.to_datetime(trade.exit_time) - pd.to_datetime(trade.entry_time)).total_seconds()
                completed_trades.append(trade)
            
            # Calculate performance metrics
            result = await self.calculate_performance_metrics(
                backtest_id, strategy.name, market_data[0].timestamp, market_data[-1].timestamp,
                initial_capital, completed_trades, equity_curve
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing backtest: {e}")
            return None
    
    async def execute_order(self, order: BacktestOrder, current_data: MarketData, 
                           strategy: StrategyEngine, open_positions: Dict[str, BacktestTrade],
                           completed_trades: List[BacktestTrade], commission_rate: float, 
                           slippage_rate: float):
        """Execute a backtest order"""
        try:
            # Calculate execution price with slippage
            if order.order_type == OrderType.MARKET:
                if order.side == OrderSide.BUY:
                    execution_price = current_data.close * (1 + slippage_rate)
                else:
                    execution_price = current_data.close * (1 - slippage_rate)
            else:
                execution_price = order.price or current_data.close
            
            # Calculate commission
            commission = order.quantity * execution_price * commission_rate
            
            # Check if we have enough cash (for buy orders)
            if order.side == OrderSide.BUY:
                total_cost = order.quantity * execution_price + commission
                if strategy.cash < total_cost:
                    logger.warning(f"Insufficient cash for order {order.id}")
                    return
                
                strategy.cash -= total_cost
                strategy.positions[order.symbol] += order.quantity
                
                # Create new trade
                trade = BacktestTrade(
                    id=f"trade_{order.id}",
                    entry_time=order.timestamp,
                    exit_time=None,
                    symbol=order.symbol,
                    side=order.side,
                    entry_price=execution_price,
                    exit_price=None,
                    quantity=order.quantity,
                    strategy=order.strategy,
                    commission=commission,
                    slippage=abs(execution_price - current_data.close) * order.quantity
                )
                
                open_positions[order.id] = trade
                
            else:  # SELL order
                if strategy.positions[order.symbol] < order.quantity:
                    logger.warning(f"Insufficient position for sell order {order.id}")
                    return
                
                strategy.positions[order.symbol] -= order.quantity
                strategy.cash += (order.quantity * execution_price) - commission
                
                # Find matching buy trade to close
                # This is simplified - in reality you'd need more sophisticated position tracking
                for trade_id, trade in list(open_positions.items()):
                    if (trade.symbol == order.symbol and 
                        trade.side == OrderSide.BUY and 
                        trade.quantity == order.quantity):
                        
                        # Close the trade
                        trade.exit_time = order.timestamp
                        trade.exit_price = execution_price
                        trade.pnl = (execution_price - trade.entry_price) * trade.quantity - trade.commission - commission
                        trade.pnl_percent = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
                        trade.duration = (pd.to_datetime(trade.exit_time) - pd.to_datetime(trade.entry_time)).total_seconds()
                        trade.commission += commission
                        trade.slippage += abs(execution_price - current_data.close) * order.quantity
                        
                        completed_trades.append(trade)
                        del open_positions[trade_id]
                        break
            
            logger.debug(f"Executed order {order.id}: {order.side.value} {order.quantity} {order.symbol} at {execution_price}")
            
        except Exception as e:
            logger.error(f"Error executing order {order.id}: {e}")
    
    async def calculate_performance_metrics(self, backtest_id: str, strategy_name: str, 
                                          start_date: str, end_date: str, initial_capital: float,
                                          trades: List[BacktestTrade], 
                                          equity_curve: List[Tuple[str, float]]) -> BacktestResult:
        """Calculate performance metrics for backtest"""
        try:
            final_capital = equity_curve[-1][1] if equity_curve else initial_capital
            total_return = final_capital - initial_capital
            total_return_percent = (total_return / initial_capital) * 100
            
            # Calculate drawdown
            peak = initial_capital
            max_drawdown = 0.0
            max_drawdown_percent = 0.0
            
            for _, equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = peak - equity
                drawdown_percent = (drawdown / peak) * 100
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                if drawdown_percent > max_drawdown_percent:
                    max_drawdown_percent = drawdown_percent
            
            # Trade statistics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl > 0])
            losing_trades = len([t for t in trades if t.pnl < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # P&L statistics
            wins = [t.pnl for t in trades if t.pnl > 0]
            losses = [t.pnl for t in trades if t.pnl < 0]
            
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            largest_win = max(wins) if wins else 0
            largest_loss = min(losses) if losses else 0
            
            # Profit factor
            gross_profit = sum(wins)
            gross_loss = abs(sum(losses))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Sharpe ratio (simplified)
            if len(equity_curve) > 1:
                returns = []
                for i in range(1, len(equity_curve)):
                    prev_equity = equity_curve[i-1][1]
                    curr_equity = equity_curve[i][1]
                    returns.append((curr_equity - prev_equity) / prev_equity)
                
                if returns:
                    avg_return = np.mean(returns)
                    std_return = np.std(returns)
                    risk_free_rate = self.config.get('execution_settings', {}).get('risk_free_rate', 0.02)
                    sharpe_ratio = (avg_return - risk_free_rate / 252) / std_return if std_return > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0
            
            # Other metrics
            avg_trade_duration = np.mean([t.duration for t in trades if t.duration]) if trades else 0
            commission_paid = sum([t.commission for t in trades])
            slippage_cost = sum([t.slippage for t in trades])
            
            result = BacktestResult(
                id=backtest_id,
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=total_return,
                total_return_percent=total_return_percent,
                max_drawdown=max_drawdown,
                max_drawdown_percent=max_drawdown_percent,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                avg_trade_duration=avg_trade_duration,
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss,
                commission_paid=commission_paid,
                slippage_cost=slippage_cost,
                trades=trades,
                equity_curve=equity_curve,
                created_at=datetime.now().isoformat()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return None
    
    async def store_backtest_result(self, result: BacktestResult):
        """Store backtest result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store main backtest record
                conn.execute("""
                    INSERT INTO backtests (
                        id, strategy_name, start_date, end_date, initial_capital, final_capital,
                        total_return, total_return_percent, max_drawdown, max_drawdown_percent,
                        sharpe_ratio, win_rate, profit_factor, total_trades, winning_trades,
                        losing_trades, avg_trade_duration, avg_win, avg_loss, largest_win,
                        largest_loss, commission_paid, slippage_cost, status, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.id, result.strategy_name, result.start_date, result.end_date,
                    result.initial_capital, result.final_capital, result.total_return,
                    result.total_return_percent, result.max_drawdown, result.max_drawdown_percent,
                    result.sharpe_ratio, result.win_rate, result.profit_factor, result.total_trades,
                    result.winning_trades, result.losing_trades, result.avg_trade_duration,
                    result.avg_win, result.avg_loss, result.largest_win, result.largest_loss,
                    result.commission_paid, result.slippage_cost, BacktestStatus.COMPLETED.value,
                    datetime.now().isoformat()
                ))
                
                # Store individual trades
                for trade in result.trades:
                    conn.execute("""
                        INSERT INTO backtest_trades (
                            id, backtest_id, entry_time, exit_time, symbol, side, entry_price,
                            exit_price, quantity, pnl, pnl_percent, duration, strategy,
                            slippage, commission, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trade.id, result.id, trade.entry_time, trade.exit_time, trade.symbol,
                        trade.side.value, trade.entry_price, trade.exit_price, trade.quantity,
                        trade.pnl, trade.pnl_percent, trade.duration, trade.strategy,
                        trade.slippage, trade.commission, json.dumps({})
                    ))
                
                conn.commit()
                logger.info(f"Backtest result {result.id} stored in database")
                
        except Exception as e:
            logger.error(f"Error storing backtest result: {e}")
    
    def get_backtest_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent backtest results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM backtests 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'strategy_name': row[1],
                        'start_date': row[2],
                        'end_date': row[3],
                        'initial_capital': row[4],
                        'final_capital': row[5],
                        'total_return': row[6],
                        'total_return_percent': row[7],
                        'max_drawdown': row[8],
                        'max_drawdown_percent': row[9],
                        'sharpe_ratio': row[10],
                        'win_rate': row[11],
                        'profit_factor': row[12],
                        'total_trades': row[13],
                        'winning_trades': row[14],
                        'losing_trades': row[15],
                        'avg_trade_duration': row[16],
                        'avg_win': row[17],
                        'avg_loss': row[18],
                        'largest_win': row[19],
                        'largest_loss': row[20],
                        'commission_paid': row[21],
                        'slippage_cost': row[22],
                        'status': row[23],
                        'created_at': row[24],
                        'completed_at': row[25]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting backtest results: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get backtesting engine status"""
        return {
            'available_strategies': list(self.strategies.keys()),
            'running_backtests': len(self.running_backtests),
            'cached_data_symbols': len(self.data_cache),
            'config_loaded': self.config_path.exists()
        }