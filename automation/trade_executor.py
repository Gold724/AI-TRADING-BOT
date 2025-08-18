#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Trade Executor Module
Automated trade execution with retry logic, strategy validation, and comprehensive logging
"""

import asyncio
import json
import logging
import requests
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trade_executor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradeStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"

@dataclass
class TradeRequest:
    """Trade request data structure"""
    id: str
    symbol: str
    action: str  # buy/sell
    amount: float
    price: Optional[float]
    order_type: str  # market/limit
    strategy: str
    timestamp: str
    curl_command: str
    status: TradeStatus = TradeStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    execution_time: Optional[float] = None
    response_data: Optional[Dict] = None

@dataclass
class StrategyRule:
    """Trading strategy rule definition"""
    name: str
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    risk_parameters: Dict[str, Any]
    symbol_filters: List[str]
    enabled: bool = True

class TradeExecutor:
    """Advanced trade execution engine with strategy validation and retry logic"""
    
    def __init__(self, config_path: str = "automation/config/trade_executor.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.db_path = Path("logs/trades.db")
        self.pending_trades: List[TradeRequest] = []
        self.active_trades: Dict[str, TradeRequest] = {}
        self.completed_trades: List[TradeRequest] = []
        self.strategies: Dict[str, StrategyRule] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_concurrent_trades', 3))
        self.running = False
        
        # Initialize database
        self.init_database()
        
        # Load strategies
        self.load_strategies()
        
        logger.info(f"TradeExecutor initialized with {len(self.strategies)} strategies")
    
    def load_config(self) -> Dict[str, Any]:
        """Load trade executor configuration"""
        default_config = {
            "max_concurrent_trades": 3,
            "retry_delay_seconds": [1, 3, 5],
            "timeout_seconds": 30,
            "enable_strategy_validation": True,
            "enable_risk_checks": True,
            "max_daily_trades": 50,
            "max_position_size": 10000,
            "allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY", "GOLD", "OIL"],
            "trading_hours": {
                "start": "09:00",
                "end": "17:00",
                "timezone": "UTC"
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                    logger.info(f"Configuration loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}, using defaults")
        else:
            # Create default config file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default configuration created at {self.config_path}")
        
        return default_config
    
    def init_database(self):
        """Initialize SQLite database for trade tracking"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL,
                    order_type TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    execution_time REAL,
                    response_data TEXT,
                    last_error TEXT,
                    curl_command TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    data TEXT,
                    FOREIGN KEY (trade_id) REFERENCES trades (id)
                )
            """)
            
            conn.commit()
            logger.info("Trade database initialized")
    
    def load_strategies(self):
        """Load trading strategies from configuration"""
        strategies_path = Path("automation/config/strategies.json")
        
        default_strategies = {
            "fvg_midpoint": {
                "name": "FVG Midpoint Strategy",
                "entry_conditions": {
                    "fvg_detected": True,
                    "price_at_midpoint": True,
                    "volume_confirmation": True
                },
                "exit_conditions": {
                    "profit_target_pips": 20,
                    "stop_loss_pips": 10,
                    "time_limit_minutes": 60
                },
                "risk_parameters": {
                    "max_risk_percent": 2.0,
                    "position_size_multiplier": 1.0
                },
                "symbol_filters": ["EURUSD", "GBPUSD", "USDJPY"],
                "enabled": True
            },
            "breakout_momentum": {
                "name": "Breakout Momentum Strategy",
                "entry_conditions": {
                    "breakout_confirmed": True,
                    "volume_spike": True,
                    "momentum_positive": True
                },
                "exit_conditions": {
                    "profit_target_pips": 30,
                    "stop_loss_pips": 15,
                    "trailing_stop": True
                },
                "risk_parameters": {
                    "max_risk_percent": 1.5,
                    "position_size_multiplier": 0.8
                },
                "symbol_filters": ["GOLD", "OIL", "EURUSD"],
                "enabled": True
            }
        }
        
        if strategies_path.exists():
            try:
                with open(strategies_path, 'r', encoding='utf-8') as f:
                    strategies_data = json.load(f)
                    for strategy_id, strategy_data in strategies_data.items():
                        self.strategies[strategy_id] = StrategyRule(**strategy_data)
                    logger.info(f"Loaded {len(self.strategies)} strategies from {strategies_path}")
            except Exception as e:
                logger.error(f"Error loading strategies: {e}, using defaults")
        else:
            # Create default strategies file
            strategies_path.parent.mkdir(parents=True, exist_ok=True)
            with open(strategies_path, 'w', encoding='utf-8') as f:
                json.dump(default_strategies, f, indent=2)
            
            # Load default strategies
            for strategy_id, strategy_data in default_strategies.items():
                self.strategies[strategy_id] = StrategyRule(**strategy_data)
            
            logger.info(f"Default strategies created and loaded: {len(self.strategies)} strategies")
    
    async def process_trade_request_from_curl(self, curl_file_path: str, strategy: str = "manual") -> Optional[TradeRequest]:
        """Process trade request from captured cURL command"""
        try:
            with open(curl_file_path, 'r', encoding='utf-8') as f:
                curl_command = f.read().strip()
            
            # Parse cURL command to extract trade details
            trade_data = self.parse_curl_command(curl_command)
            if not trade_data:
                logger.error(f"Failed to parse cURL command from {curl_file_path}")
                return None
            
            # Create trade request
            trade_request = TradeRequest(
                id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}",
                symbol=trade_data.get('symbol', 'UNKNOWN'),
                action=trade_data.get('action', 'buy'),
                amount=float(trade_data.get('amount', 0)),
                price=trade_data.get('price'),
                order_type=trade_data.get('order_type', 'market'),
                strategy=strategy,
                timestamp=datetime.now().isoformat(),
                curl_command=curl_command
            )
            
            # Validate trade request
            if await self.validate_trade_request(trade_request):
                self.pending_trades.append(trade_request)
                await self.log_trade_event(trade_request.id, "CREATED", "Trade request created from cURL")
                logger.info(f"Trade request created: {trade_request.id} - {trade_request.symbol} {trade_request.action} {trade_request.amount}")
                return trade_request
            else:
                logger.warning(f"Trade request validation failed: {trade_request.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing trade request from {curl_file_path}: {e}")
            return None
    
    def parse_curl_command(self, curl_command: str) -> Optional[Dict[str, Any]]:
        """Parse cURL command to extract trade parameters"""
        try:
            # Extract URL
            url_match = re.search(r"curl.*?'([^']+)'", curl_command)
            if not url_match:
                return None
            
            url = url_match.group(1)
            
            # Extract POST data
            data_match = re.search(r"-d\s+'([^']+)'", curl_command)
            if not data_match:
                return None
            
            post_data = data_match.group(1)
            
            # Try to parse as JSON
            try:
                data_json = json.loads(post_data)
            except:
                # If not JSON, try to parse as form data
                data_json = {}
                for pair in post_data.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        data_json[key] = value
            
            # Extract trade parameters
            trade_data = {
                'url': url,
                'symbol': data_json.get('symbol', data_json.get('instrument', 'UNKNOWN')),
                'action': data_json.get('action', data_json.get('side', 'buy')).lower(),
                'amount': data_json.get('amount', data_json.get('quantity', data_json.get('volume', 0))),
                'price': data_json.get('price'),
                'order_type': data_json.get('type', data_json.get('orderType', 'market')).lower()
            }
            
            return trade_data
            
        except Exception as e:
            logger.error(f"Error parsing cURL command: {e}")
            return None
    
    async def validate_trade_request(self, trade_request: TradeRequest) -> bool:
        """Validate trade request against strategy rules and risk parameters"""
        try:
            # Basic validation
            if not trade_request.symbol or trade_request.amount <= 0:
                await self.log_trade_event(trade_request.id, "VALIDATION_FAILED", "Invalid symbol or amount")
                return False
            
            # Check if trading is enabled
            if not self.config.get('enable_strategy_validation', True):
                return True
            
            # Check symbol whitelist
            allowed_symbols = self.config.get('allowed_symbols', [])
            if allowed_symbols and trade_request.symbol not in allowed_symbols:
                await self.log_trade_event(trade_request.id, "VALIDATION_FAILED", f"Symbol {trade_request.symbol} not in allowed list")
                return False
            
            # Check position size limits
            max_position = self.config.get('max_position_size', 10000)
            if trade_request.amount > max_position:
                await self.log_trade_event(trade_request.id, "VALIDATION_FAILED", f"Amount {trade_request.amount} exceeds max position size {max_position}")
                return False
            
            # Check daily trade limits
            daily_trades = await self.get_daily_trade_count()
            max_daily = self.config.get('max_daily_trades', 50)
            if daily_trades >= max_daily:
                await self.log_trade_event(trade_request.id, "VALIDATION_FAILED", f"Daily trade limit reached: {daily_trades}/{max_daily}")
                return False
            
            # Strategy-specific validation
            if trade_request.strategy in self.strategies:
                strategy = self.strategies[trade_request.strategy]
                if not strategy.enabled:
                    await self.log_trade_event(trade_request.id, "VALIDATION_FAILED", f"Strategy {trade_request.strategy} is disabled")
                    return False
                
                # Check symbol filters
                if strategy.symbol_filters and trade_request.symbol not in strategy.symbol_filters:
                    await self.log_trade_event(trade_request.id, "VALIDATION_FAILED", f"Symbol {trade_request.symbol} not allowed for strategy {trade_request.strategy}")
                    return False
            
            await self.log_trade_event(trade_request.id, "VALIDATION_PASSED", "Trade request validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating trade request {trade_request.id}: {e}")
            await self.log_trade_event(trade_request.id, "VALIDATION_ERROR", str(e))
            return False
    
    async def execute_trade(self, trade_request: TradeRequest) -> bool:
        """Execute trade with retry logic and comprehensive logging"""
        trade_request.status = TradeStatus.EXECUTING
        self.active_trades[trade_request.id] = trade_request
        
        await self.log_trade_event(trade_request.id, "EXECUTION_STARTED", f"Starting execution attempt {trade_request.attempts + 1}")
        
        for attempt in range(trade_request.max_attempts):
            trade_request.attempts = attempt + 1
            
            try:
                start_time = time.time()
                
                # Execute the cURL command
                result = await self.execute_curl_command(trade_request.curl_command)
                
                execution_time = time.time() - start_time
                trade_request.execution_time = execution_time
                
                if result['success']:
                    trade_request.status = TradeStatus.SUCCESS
                    trade_request.response_data = result['response']
                    
                    await self.log_trade_event(trade_request.id, "EXECUTION_SUCCESS", 
                                             f"Trade executed successfully in {execution_time:.2f}s")
                    
                    # Save to database
                    await self.save_trade_to_db(trade_request)
                    
                    # Move to completed trades
                    self.completed_trades.append(trade_request)
                    del self.active_trades[trade_request.id]
                    
                    logger.info(f"Trade {trade_request.id} executed successfully")
                    return True
                else:
                    trade_request.last_error = result['error']
                    
                    if attempt < trade_request.max_attempts - 1:
                        trade_request.status = TradeStatus.RETRYING
                        retry_delay = self.config.get('retry_delay_seconds', [1, 3, 5])[min(attempt, 2)]
                        
                        await self.log_trade_event(trade_request.id, "EXECUTION_RETRY", 
                                                 f"Attempt {attempt + 1} failed: {result['error']}. Retrying in {retry_delay}s")
                        
                        await asyncio.sleep(retry_delay)
                    else:
                        trade_request.status = TradeStatus.FAILED
                        
                        await self.log_trade_event(trade_request.id, "EXECUTION_FAILED", 
                                                 f"All {trade_request.max_attempts} attempts failed. Last error: {result['error']}")
            
            except Exception as e:
                trade_request.last_error = str(e)
                
                if attempt < trade_request.max_attempts - 1:
                    trade_request.status = TradeStatus.RETRYING
                    await self.log_trade_event(trade_request.id, "EXECUTION_EXCEPTION", 
                                             f"Exception on attempt {attempt + 1}: {e}. Retrying...")
                    await asyncio.sleep(2)
                else:
                    trade_request.status = TradeStatus.FAILED
                    await self.log_trade_event(trade_request.id, "EXECUTION_FAILED", 
                                             f"Exception after all attempts: {e}")
        
        # Save failed trade to database
        await self.save_trade_to_db(trade_request)
        
        # Move to completed trades
        self.completed_trades.append(trade_request)
        del self.active_trades[trade_request.id]
        
        logger.error(f"Trade {trade_request.id} failed after {trade_request.max_attempts} attempts")
        return False
    
    async def execute_curl_command(self, curl_command: str) -> Dict[str, Any]:
        """Execute cURL command and return result"""
        try:
            # Convert cURL to requests for better control
            session = requests.Session()
            session.timeout = self.config.get('timeout_seconds', 30)
            
            # Parse cURL command
            url_match = re.search(r"curl.*?'([^']+)'", curl_command)
            if not url_match:
                return {'success': False, 'error': 'Could not extract URL from cURL command'}
            
            url = url_match.group(1)
            
            # Extract headers
            headers = {}
            header_matches = re.findall(r"-H\s+'([^:]+):\s*([^']+)'", curl_command)
            for header_name, header_value in header_matches:
                headers[header_name] = header_value
            
            # Extract POST data
            data = None
            data_match = re.search(r"-d\s+'([^']+)'", curl_command)
            if data_match:
                data = data_match.group(1)
            
            # Execute request
            response = session.post(url, headers=headers, data=data)
            
            # Parse response
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text[:1000]  # Limit response text
            }
            
            if response.status_code == 200:
                return {'success': True, 'response': response_data}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:200]}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def log_trade_event(self, trade_id: str, event_type: str, message: str, data: Optional[Dict] = None):
        """Log trade event to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO trade_logs (trade_id, timestamp, event_type, message, data) VALUES (?, ?, ?, ?, ?)",
                    (trade_id, datetime.now().isoformat(), event_type, message, json.dumps(data) if data else None)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging trade event: {e}")
    
    async def save_trade_to_db(self, trade_request: TradeRequest):
        """Save trade request to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO trades 
                    (id, symbol, action, amount, price, order_type, strategy, timestamp, status, 
                     attempts, execution_time, response_data, last_error, curl_command)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_request.id,
                    trade_request.symbol,
                    trade_request.action,
                    trade_request.amount,
                    trade_request.price,
                    trade_request.order_type,
                    trade_request.strategy,
                    trade_request.timestamp,
                    trade_request.status.value,
                    trade_request.attempts,
                    trade_request.execution_time,
                    json.dumps(trade_request.response_data) if trade_request.response_data else None,
                    trade_request.last_error,
                    trade_request.curl_command
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving trade to database: {e}")
    
    async def get_daily_trade_count(self) -> int:
        """Get number of trades executed today"""
        try:
            today = datetime.now().date().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM trades WHERE date(timestamp) = ? AND status = ?",
                    (today, TradeStatus.SUCCESS.value)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting daily trade count: {e}")
            return 0
    
    async def start_processing(self):
        """Start processing pending trades"""
        self.running = True
        logger.info("Trade executor started")
        
        while self.running:
            try:
                # Process pending trades
                if self.pending_trades:
                    trade_request = self.pending_trades.pop(0)
                    
                    # Execute trade in background
                    asyncio.create_task(self.execute_trade(trade_request))
                
                # Check for new trade.sh file
                trade_sh_path = Path("trade.sh")
                if trade_sh_path.exists() and trade_sh_path.stat().st_mtime > time.time() - 60:
                    # New trade.sh detected, process it
                    await self.process_trade_request_from_curl(str(trade_sh_path), "auto_detected")
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in trade processing loop: {e}")
                await asyncio.sleep(5)
    
    async def stop_processing(self):
        """Stop processing trades"""
        self.running = False
        logger.info("Trade executor stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current executor status"""
        return {
            'running': self.running,
            'pending_trades': len(self.pending_trades),
            'active_trades': len(self.active_trades),
            'completed_trades': len(self.completed_trades),
            'strategies_loaded': len(self.strategies),
            'daily_trade_count': asyncio.run(self.get_daily_trade_count()) if not asyncio.get_event_loop().is_running() else 0
        }