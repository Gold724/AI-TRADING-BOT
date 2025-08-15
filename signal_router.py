# signal_router.py

import os
import json
import time
import logging
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import re
import threading
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("signal_router.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SignalRouter")

# Try to import from other modules
try:
    from sentinel_decider import SentinelDecider
except ImportError:
    logger.warning("Could not import SentinelDecider, using minimal version")
    # Define a minimal version if the import fails
    class SentinelDecider:
        def get_trade_decision(self, strategy, symbol, direction, entry_price, stop_loss, take_profit):
            return 50, "Take Trade", "Placeholder decision"

try:
    from strategy_manager import StrategyManager
except ImportError:
    logger.warning("Could not import StrategyManager, using minimal version")
    # Define a minimal version if the import fails
    class StrategyManager:
        def get_enabled_strategies(self):
            return []
        def get_strategy_config(self, strategy_name):
            return {}

try:
    from risk_control import RiskController
except ImportError:
    logger.warning("Could not import RiskController, using minimal version")
    # Define a minimal version if the import fails
    class RiskController:
        def is_trading_allowed(self, strategy_name):
            return True

try:
    from news_guard import NewsGuard
except ImportError:
    logger.warning("Could not import NewsGuard, using minimal version")
    # Define a minimal version if the import fails
    class NewsGuard:
        def is_trading_allowed(self, symbol):
            return True

class SignalSource:
    """Base class for signal sources"""
    
    def __init__(self, name: str, config: Dict):
        """Initialize the signal source
        
        Args:
            name: Name of the signal source
            config: Configuration for the signal source
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.weight = config.get("weight", 1.0)
        self.last_update = None
        self.signals = []
        
    def update(self) -> List[Dict]:
        """Update signals from the source
        
        Returns:
            List[Dict]: List of signals
        """
        raise NotImplementedError("Subclasses must implement update()")
        
    def get_signals(self) -> List[Dict]:
        """Get signals from the source
        
        Returns:
            List[Dict]: List of signals
        """
        if not self.enabled:
            return []
            
        return self.signals

class TraeAISignalSource(SignalSource):
    """Signal source for Trae.AI internal signals"""
    
    def __init__(self, config: Dict):
        """Initialize the Trae.AI signal source
        
        Args:
            config: Configuration for the signal source
        """
        super().__init__("trae_ai", config)
        self.signals_file = config.get("signals_file", "data/trae_signals.json")
        
    def update(self) -> List[Dict]:
        """Update signals from the Trae.AI source
        
        Returns:
            List[Dict]: List of signals
        """
        try:
            if os.path.exists(self.signals_file):
                with open(self.signals_file, "r") as f:
                    self.signals = json.load(f)
                    
                # Add source information to signals
                for signal in self.signals:
                    signal["source"] = self.name
                    signal["source_weight"] = self.weight
                    
                self.last_update = datetime.now()
                logger.info(f"Updated {len(self.signals)} signals from Trae.AI")
            else:
                logger.warning(f"Signals file not found: {self.signals_file}")
                self.signals = []
        except Exception as e:
            logger.error(f"Error updating Trae.AI signals: {e}")
            self.signals = []
            
        return self.signals

class TradingViewSignalSource(SignalSource):
    """Signal source for TradingView alerts"""
    
    def __init__(self, config: Dict):
        """Initialize the TradingView signal source
        
        Args:
            config: Configuration for the signal source
        """
        super().__init__("tradingview", config)
        self.webhook_port = config.get("webhook_port", 5000)
        self.webhook_path = config.get("webhook_path", "/tradingview/webhook")
        self.signal_expiry = config.get("signal_expiry", 3600)  # 1 hour in seconds
        self.server_thread = None
        self.signal_queue = Queue()
        self.running = False
        
        # Start webhook server if enabled
        if self.enabled:
            self._start_webhook_server()
        
    def _start_webhook_server(self):
        """Start the webhook server to receive TradingView alerts"""
        try:
            from flask import Flask, request, jsonify
            
            app = Flask(__name__)
            
            @app.route(self.webhook_path, methods=["POST"])
            def webhook():
                try:
                    data = request.json
                    
                    # Process TradingView alert
                    signal = self._process_tradingview_alert(data)
                    
                    if signal:
                        self.signal_queue.put(signal)
                        logger.info(f"Received TradingView signal: {signal['symbol']} {signal['direction']}")
                        return jsonify({"status": "success"})
                    else:
                        logger.warning(f"Invalid TradingView alert: {data}")
                        return jsonify({"status": "error", "message": "Invalid alert format"})
                except Exception as e:
                    logger.error(f"Error processing TradingView webhook: {e}")
                    return jsonify({"status": "error", "message": str(e)})
            
            def run_server():
                app.run(host="0.0.0.0", port=self.webhook_port)
                
            self.server_thread = threading.Thread(target=run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.running = True
            logger.info(f"Started TradingView webhook server on port {self.webhook_port}")
        except ImportError:
            logger.error("Flask not installed, TradingView webhook server not started")
        except Exception as e:
            logger.error(f"Error starting TradingView webhook server: {e}")
    
    def _process_tradingview_alert(self, data: Dict) -> Optional[Dict]:
        """Process a TradingView alert
        
        Args:
            data: Alert data from TradingView
            
        Returns:
            Optional[Dict]: Processed signal or None if invalid
        """
        try:
            # Expected format from TradingView:
            # {
            #   "strategy": "MACD Crossover",
            #   "symbol": "EURUSD",
            #   "direction": "buy",
            #   "entry": 1.1050,
            #   "stop": 1.1000,
            #   "target": 1.1150,
            #   "timeframe": "1h"
            # }
            
            required_fields = ["symbol", "direction", "entry"]
            
            if not all(field in data for field in required_fields):
                logger.warning(f"Missing required fields in TradingView alert: {data}")
                return None
                
            # Create signal
            signal = {
                "timestamp": datetime.now().isoformat(),
                "source": self.name,
                "source_weight": self.weight,
                "strategy": data.get("strategy", "TradingView"),
                "symbol": data["symbol"],
                "direction": data["direction"].lower(),
                "entry_price": float(data["entry"]),
                "stop_loss": float(data.get("stop", 0)),
                "take_profit": float(data.get("target", 0)),
                "timeframe": data.get("timeframe", "")
            }
            
            # Calculate risk-reward ratio if stop and target are provided
            if signal["stop_loss"] > 0 and signal["take_profit"] > 0:
                if signal["direction"] == "buy":
                    risk = signal["entry_price"] - signal["stop_loss"]
                    reward = signal["take_profit"] - signal["entry_price"]
                else:  # sell
                    risk = signal["stop_loss"] - signal["entry_price"]
                    reward = signal["entry_price"] - signal["take_profit"]
                    
                if risk > 0:
                    signal["risk_reward_ratio"] = round(reward / risk, 2)
                else:
                    signal["risk_reward_ratio"] = 0
            else:
                signal["risk_reward_ratio"] = 0
                
            return signal
        except Exception as e:
            logger.error(f"Error processing TradingView alert: {e}")
            return None
    
    def update(self) -> List[Dict]:
        """Update signals from the TradingView source
        
        Returns:
            List[Dict]: List of signals
        """
        # Process signals from queue
        while not self.signal_queue.empty():
            signal = self.signal_queue.get()
            self.signals.append(signal)
            
        # Remove expired signals
        current_time = datetime.now()
        self.signals = [
            signal for signal in self.signals
            if datetime.fromisoformat(signal["timestamp"]) > current_time - timedelta(seconds=self.signal_expiry)
        ]
        
        self.last_update = current_time
        return self.signals

class TelegramSignalSource(SignalSource):
    """Signal source for Telegram signals"""
    
    def __init__(self, config: Dict):
        """Initialize the Telegram signal source
        
        Args:
            config: Configuration for the signal source
        """
        super().__init__("telegram", config)
        self.bot_token = config.get("bot_token", "")
        self.chat_ids = config.get("chat_ids", [])
        self.signal_patterns = config.get("signal_patterns", [])
        self.last_update_id = 0
        self.signal_expiry = config.get("signal_expiry", 3600)  # 1 hour in seconds
        
    def update(self) -> List[Dict]:
        """Update signals from the Telegram source
        
        Returns:
            List[Dict]: List of signals
        """
        if not self.bot_token or not self.chat_ids:
            logger.warning("Telegram bot token or chat IDs not configured")
            return []
            
        try:
            # Get updates from Telegram
            updates = self._get_telegram_updates()
            
            # Process updates
            for update in updates:
                if "message" in update and "text" in update["message"]:
                    message = update["message"]
                    
                    # Check if message is from a monitored chat
                    if str(message.get("chat", {}).get("id")) in self.chat_ids:
                        # Process message
                        signal = self._process_telegram_message(message["text"])
                        
                        if signal:
                            self.signals.append(signal)
                            logger.info(f"Received Telegram signal: {signal['symbol']} {signal['direction']}")
            
            # Remove expired signals
            current_time = datetime.now()
            self.signals = [
                signal for signal in self.signals
                if datetime.fromisoformat(signal["timestamp"]) > current_time - timedelta(seconds=self.signal_expiry)
            ]
            
            self.last_update = current_time
            return self.signals
        except Exception as e:
            logger.error(f"Error updating Telegram signals: {e}")
            return []
    
    def _get_telegram_updates(self) -> List[Dict]:
        """Get updates from Telegram API
        
        Returns:
            List[Dict]: List of updates
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {"offset": self.last_update_id + 1, "timeout": 30}
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("ok") and "result" in data:
                updates = data["result"]
                
                # Update last_update_id
                if updates:
                    self.last_update_id = max(update["update_id"] for update in updates)
                    
                return updates
            else:
                logger.warning(f"Error getting Telegram updates: {data}")
                return []
        except Exception as e:
            logger.error(f"Error getting Telegram updates: {e}")
            return []
    
    def _process_telegram_message(self, text: str) -> Optional[Dict]:
        """Process a Telegram message to extract signal
        
        Args:
            text: Message text
            
        Returns:
            Optional[Dict]: Extracted signal or None if no signal found
        """
        try:
            # Try each pattern until one matches
            for pattern in self.signal_patterns:
                match = re.search(pattern["regex"], text, re.IGNORECASE)
                
                if match:
                    # Extract signal components based on pattern
                    signal = {
                        "timestamp": datetime.now().isoformat(),
                        "source": self.name,
                        "source_weight": self.weight,
                        "strategy": pattern.get("strategy", "Telegram"),
                    }
                    
                    # Map regex groups to signal fields
                    field_mapping = pattern.get("field_mapping", {})
                    
                    for field, group in field_mapping.items():
                        try:
                            value = match.group(group)
                            
                            # Convert numeric values
                            if field in ["entry_price", "stop_loss", "take_profit"]:
                                try:
                                    value = float(value)
                                except ValueError:
                                    value = 0
                                    
                            signal[field] = value
                        except IndexError:
                            # Group not found in match
                            pass
                    
                    # Ensure required fields are present
                    required_fields = ["symbol", "direction", "entry_price"]
                    
                    if all(field in signal for field in required_fields):
                        # Normalize direction
                        signal["direction"] = signal["direction"].lower()
                        
                        # Calculate risk-reward ratio if stop and target are provided
                        if "stop_loss" in signal and "take_profit" in signal and signal["stop_loss"] > 0 and signal["take_profit"] > 0:
                            if signal["direction"] == "buy":
                                risk = signal["entry_price"] - signal["stop_loss"]
                                reward = signal["take_profit"] - signal["entry_price"]
                            else:  # sell
                                risk = signal["stop_loss"] - signal["entry_price"]
                                reward = signal["entry_price"] - signal["take_profit"]
                                
                            if risk > 0:
                                signal["risk_reward_ratio"] = round(reward / risk, 2)
                            else:
                                signal["risk_reward_ratio"] = 0
                        else:
                            signal["risk_reward_ratio"] = 0
                            
                        return signal
            
            # No pattern matched
            return None
        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}")
            return None

class SignalRouter:
    """A class to aggregate, filter, and route trading signals from multiple sources"""
    
    def __init__(self, config_path: str = "config/signal_router_config.json"):
        """Initialize the SignalRouter
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.sources = self._initialize_sources()
        self.filters = self.config.get("filters", {})
        self.routing_rules = self.config.get("routing_rules", {})
        
        # Initialize components
        self.data_dir = os.path.join("data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.sentinel = SentinelDecider()
        self.strategy_manager = StrategyManager()
        self.risk_controller = RiskController()
        self.news_guard = NewsGuard()
        
        # Signal history
        self.signal_history_path = os.path.join(self.data_dir, "signal_history.json")
        self.signal_history = self._load_signal_history()
        
        # Signal queue
        self.signal_queue = []
        
        # Start update thread
        self.update_interval = self.config.get("update_interval", 60)  # seconds
        self.running = False
        self.update_thread = None
        
        if self.config.get("auto_update", True):
            self.start_update_thread()
    
    def _load_config(self) -> Dict:
        """Load configuration from file
        
        Returns:
            Dict: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    return json.load(f)
            else:
                # Create default config
                default_config = self._create_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration
        
        Returns:
            Dict: Default configuration dictionary
        """
        return {
            "sources": {
                "trae_ai": {
                    "enabled": True,
                    "weight": 1.0,
                    "signals_file": "data/trae_signals.json"
                },
                "tradingview": {
                    "enabled": False,
                    "weight": 0.8,
                    "webhook_port": 5000,
                    "webhook_path": "/tradingview/webhook",
                    "signal_expiry": 3600
                },
                "telegram": {
                    "enabled": False,
                    "weight": 0.6,
                    "bot_token": "",
                    "chat_ids": [],
                    "signal_expiry": 3600,
                    "signal_patterns": [
                        {
                            "regex": "(?i)Signal Alert.*?\\s+Symbol:\\s+([A-Z]+/[A-Z]+).*?\\s+Direction:\\s+(Buy|Sell).*?\\s+Entry:\\s+([0-9.]+).*?\\s+Stop:\\s+([0-9.]+).*?\\s+Target:\\s+([0-9.]+)",
                            "strategy": "Telegram Signal",
                            "field_mapping": {
                                "symbol": 1,
                                "direction": 2,
                                "entry_price": 3,
                                "stop_loss": 4,
                                "take_profit": 5
                            }
                        }
                    ]
                }
            },
            "filters": {
                "min_risk_reward": 1.5,
                "max_daily_signals": 10,
                "allowed_symbols": [],  # Empty means all symbols allowed
                "allowed_strategies": [],  # Empty means all strategies allowed
                "min_source_weight": 0.6
            },
            "routing_rules": {
                "default_strategy": "Auto",
                "strategy_mapping": {
                    "MACD Crossover": "Momentum",
                    "RSI Divergence": "Mean Reversion",
                    "Fibonacci Retracement": "Fibonacci"
                },
                "symbol_preferences": {
                    "Momentum": ["EURUSD", "GBPUSD", "USDJPY"],
                    "Mean Reversion": ["AUDUSD", "NZDUSD", "USDCAD"],
                    "Fibonacci": ["EURUSD", "GBPUSD", "USDJPY"]
                }
            },
            "update_interval": 60,
            "auto_update": True,
            "max_signal_history": 1000,
            "max_queue_size": 100
        }
    
    def _initialize_sources(self) -> Dict[str, SignalSource]:
        """Initialize signal sources
        
        Returns:
            Dict[str, SignalSource]: Dictionary of signal sources
        """
        sources = {}
        
        for source_name, source_config in self.config.get("sources", {}).items():
            try:
                if source_name == "trae_ai":
                    sources[source_name] = TraeAISignalSource(source_config)
                elif source_name == "tradingview":
                    sources[source_name] = TradingViewSignalSource(source_config)
                elif source_name == "telegram":
                    sources[source_name] = TelegramSignalSource(source_config)
                else:
                    logger.warning(f"Unknown signal source: {source_name}")
            except Exception as e:
                logger.error(f"Error initializing signal source {source_name}: {e}")
                
        return sources
    
    def _load_signal_history(self) -> List[Dict]:
        """Load signal history from file
        
        Returns:
            List[Dict]: Signal history
        """
        try:
            if os.path.exists(self.signal_history_path):
                with open(self.signal_history_path, "r") as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading signal history: {e}")
            return []
    
    def _save_signal_history(self):
        """Save signal history to file"""
        try:
            # Limit history size
            max_history = self.config.get("max_signal_history", 1000)
            if len(self.signal_history) > max_history:
                self.signal_history = self.signal_history[-max_history:]
                
            with open(self.signal_history_path, "w") as f:
                json.dump(self.signal_history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving signal history: {e}")
    
    def start_update_thread(self):
        """Start the update thread"""
        if self.running:
            logger.warning("Update thread already running")
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info("Started signal update thread")
    
    def stop_update_thread(self):
        """Stop the update thread"""
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
            
        logger.info("Stopped signal update thread")
    
    def _update_loop(self):
        """Update loop for signal sources"""
        while self.running:
            try:
                self.update_signals()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Short delay before retrying
    
    def update_signals(self):
        """Update signals from all sources"""
        all_signals = []
        
        # Update each source
        for source_name, source in self.sources.items():
            try:
                if source.enabled:
                    signals = source.update()
                    all_signals.extend(signals)
                    logger.debug(f"Updated {len(signals)} signals from {source_name}")
            except Exception as e:
                logger.error(f"Error updating signals from {source_name}: {e}")
                
        # Filter signals
        filtered_signals = self.filter_signals(all_signals)
        
        # Add to queue
        self._add_to_queue(filtered_signals)
        
        logger.info(f"Updated signals: {len(all_signals)} total, {len(filtered_signals)} after filtering, {len(self.signal_queue)} in queue")
    
    def filter_signals(self, signals: List[Dict]) -> List[Dict]:
        """Filter signals based on configured filters
        
        Args:
            signals: List of signals to filter
            
        Returns:
            List[Dict]: Filtered signals
        """
        filtered_signals = []
        
        for signal in signals:
            # Check if signal passes all filters
            if self._passes_filters(signal):
                filtered_signals.append(signal)
                
        return filtered_signals
    
    def _passes_filters(self, signal: Dict) -> bool:
        """Check if a signal passes all filters
        
        Args:
            signal: Signal to check
            
        Returns:
            bool: True if signal passes all filters, False otherwise
        """
        # Check source weight
        min_source_weight = self.filters.get("min_source_weight", 0)
        if signal.get("source_weight", 0) < min_source_weight:
            logger.debug(f"Signal rejected: source weight {signal.get('source_weight', 0)} < {min_source_weight}")
            return False
            
        # Check risk-reward ratio
        min_risk_reward = self.filters.get("min_risk_reward", 0)
        if signal.get("risk_reward_ratio", 0) < min_risk_reward:
            logger.debug(f"Signal rejected: risk-reward {signal.get('risk_reward_ratio', 0)} < {min_risk_reward}")
            return False
            
        # Check allowed symbols
        allowed_symbols = self.filters.get("allowed_symbols", [])
        if allowed_symbols and signal.get("symbol") not in allowed_symbols:
            logger.debug(f"Signal rejected: symbol {signal.get('symbol')} not in allowed symbols")
            return False
            
        # Check allowed strategies
        allowed_strategies = self.filters.get("allowed_strategies", [])
        if allowed_strategies and signal.get("strategy") not in allowed_strategies:
            logger.debug(f"Signal rejected: strategy {signal.get('strategy')} not in allowed strategies")
            return False
            
        # Check news guard
        if not self.news_guard.is_trading_allowed(signal.get("symbol", "")):
            logger.debug(f"Signal rejected: news guard disallows trading for {signal.get('symbol')}")
            return False
            
        # Check daily signal limit
        max_daily_signals = self.filters.get("max_daily_signals", 0)
        if max_daily_signals > 0:
            # Count signals for today
            today = datetime.now().date()
            today_signals = sum(
                1 for s in self.signal_history
                if datetime.fromisoformat(s["timestamp"]).date() == today
            )
            
            if today_signals >= max_daily_signals:
                logger.debug(f"Signal rejected: daily limit reached ({today_signals} >= {max_daily_signals})")
                return False
                
        return True
    
    def _add_to_queue(self, signals: List[Dict]):
        """Add signals to the queue
        
        Args:
            signals: List of signals to add
        """
        # Add signals to queue
        for signal in signals:
            # Check if signal is already in queue (based on source, symbol, direction, and timestamp)
            is_duplicate = False
            
            for existing in self.signal_queue:
                if (
                    existing["source"] == signal["source"] and
                    existing["symbol"] == signal["symbol"] and
                    existing["direction"] == signal["direction"] and
                    abs((datetime.fromisoformat(existing["timestamp"]) - 
                         datetime.fromisoformat(signal["timestamp"])).total_seconds()) < 300  # 5 minutes
                ):
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                # Add routing information
                routed_signal = self._route_signal(signal)
                self.signal_queue.append(routed_signal)
                
        # Limit queue size
        max_queue_size = self.config.get("max_queue_size", 100)
        if len(self.signal_queue) > max_queue_size:
            self.signal_queue = self.signal_queue[-max_queue_size:]
    
    def _route_signal(self, signal: Dict) -> Dict:
        """Route a signal to the appropriate strategy
        
        Args:
            signal: Signal to route
            
        Returns:
            Dict: Routed signal with additional routing information
        """
        # Create a copy of the signal
        routed_signal = signal.copy()
        
        # Get source strategy
        source_strategy = signal.get("strategy", "")
        
        # Map to internal strategy if mapping exists
        strategy_mapping = self.routing_rules.get("strategy_mapping", {})
        mapped_strategy = strategy_mapping.get(source_strategy, source_strategy)
        
        # Check if mapped strategy is enabled
        enabled_strategies = self.strategy_manager.get_enabled_strategies()
        
        if mapped_strategy in enabled_strategies:
            target_strategy = mapped_strategy
        else:
            # Use default strategy
            target_strategy = self.routing_rules.get("default_strategy", "Auto")
            
        # Add routing information
        routed_signal["target_strategy"] = target_strategy
        routed_signal["routing_timestamp"] = datetime.now().isoformat()
        routed_signal["routing_source"] = "signal_router"
        
        # Check if strategy is allowed by risk controller
        routed_signal["trading_allowed"] = self.risk_controller.is_trading_allowed(target_strategy)
        
        # Get confidence score from sentinel
        try:
            confidence, recommendation, explanation = self.sentinel.get_trade_decision(
                strategy=target_strategy,
                symbol=routed_signal["symbol"],
                direction=routed_signal["direction"],
                entry_price=routed_signal["entry_price"],
                stop_loss=routed_signal.get("stop_loss", 0),
                take_profit=routed_signal.get("take_profit", 0)
            )
            
            routed_signal["confidence_score"] = confidence
            routed_signal["recommendation"] = recommendation
            routed_signal["explanation"] = explanation
        except Exception as e:
            logger.error(f"Error getting trade decision from sentinel: {e}")
            routed_signal["confidence_score"] = 0
            routed_signal["recommendation"] = "Skip Trade"
            routed_signal["explanation"] = f"Error: {str(e)}"
            
        return routed_signal
    
    def get_signals(self, limit: int = 10, include_processed: bool = False) -> List[Dict]:
        """Get signals from the queue
        
        Args:
            limit: Maximum number of signals to return
            include_processed: Whether to include processed signals
            
        Returns:
            List[Dict]: List of signals
        """
        if include_processed:
            # Return both queue and processed signals
            all_signals = self.signal_queue + self.signal_history
            
            # Sort by timestamp (newest first)
            sorted_signals = sorted(
                all_signals,
                key=lambda s: datetime.fromisoformat(s["timestamp"]),
                reverse=True
            )
            
            return sorted_signals[:limit]
        else:
            # Return only queue signals
            return self.signal_queue[:limit]
    
    def get_next_signal(self) -> Optional[Dict]:
        """Get the next signal from the queue
        
        Returns:
            Optional[Dict]: Next signal or None if queue is empty
        """
        if not self.signal_queue:
            return None
            
        # Sort by confidence score (highest first)
        sorted_queue = sorted(
            self.signal_queue,
            key=lambda s: s.get("confidence_score", 0),
            reverse=True
        )
        
        # Get highest confidence signal
        signal = sorted_queue[0]
        
        # Remove from queue
        self.signal_queue.remove(signal)
        
        # Add to history
        signal["processed_timestamp"] = datetime.now().isoformat()
        self.signal_history.append(signal)
        self._save_signal_history()
        
        return signal
    
    def process_signal(self, signal_id: str) -> Optional[Dict]:
        """Process a specific signal by ID
        
        Args:
            signal_id: ID of the signal to process
            
        Returns:
            Optional[Dict]: Processed signal or None if not found
        """
        # Find signal in queue
        for i, signal in enumerate(self.signal_queue):
            if signal.get("id") == signal_id:
                # Remove from queue
                processed_signal = self.signal_queue.pop(i)
                
                # Add to history
                processed_signal["processed_timestamp"] = datetime.now().isoformat()
                self.signal_history.append(processed_signal)
                self._save_signal_history()
                
                return processed_signal
                
        return None
    
    def reject_signal(self, signal_id: str, reason: str = "Manually rejected") -> Optional[Dict]:
        """Reject a specific signal by ID
        
        Args:
            signal_id: ID of the signal to reject
            reason: Reason for rejection
            
        Returns:
            Optional[Dict]: Rejected signal or None if not found
        """
        # Find signal in queue
        for i, signal in enumerate(self.signal_queue):
            if signal.get("id") == signal_id:
                # Remove from queue
                rejected_signal = self.signal_queue.pop(i)
                
                # Add rejection information
                rejected_signal["rejected"] = True
                rejected_signal["rejection_reason"] = reason
                rejected_signal["rejected_timestamp"] = datetime.now().isoformat()
                
                # Add to history
                self.signal_history.append(rejected_signal)
                self._save_signal_history()
                
                return rejected_signal
                
        return None
    
    def get_signal_stats(self) -> Dict:
        """Get statistics about signals
        
        Returns:
            Dict: Signal statistics
        """
        stats = {
            "queue_size": len(self.signal_queue),
            "history_size": len(self.signal_history),
            "sources": {},
            "strategies": {},
            "symbols": {},
            "directions": {},
            "recommendations": {},
            "avg_confidence": 0,
            "processed_today": 0,
            "rejected_count": 0
        }
        
        # Count signals by source, strategy, symbol, direction, and recommendation
        for signal in self.signal_history:
            source = signal.get("source", "unknown")
            strategy = signal.get("target_strategy", signal.get("strategy", "unknown"))
            symbol = signal.get("symbol", "unknown")
            direction = signal.get("direction", "unknown")
            recommendation = signal.get("recommendation", "unknown")
            
            # Count by source
            if source not in stats["sources"]:
                stats["sources"][source] = 0
            stats["sources"][source] += 1
            
            # Count by strategy
            if strategy not in stats["strategies"]:
                stats["strategies"][strategy] = 0
            stats["strategies"][strategy] += 1
            
            # Count by symbol
            if symbol not in stats["symbols"]:
                stats["symbols"][symbol] = 0
            stats["symbols"][symbol] += 1
            
            # Count by direction
            if direction not in stats["directions"]:
                stats["directions"][direction] = 0
            stats["directions"][direction] += 1
            
            # Count by recommendation
            if recommendation not in stats["recommendations"]:
                stats["recommendations"][recommendation] = 0
            stats["recommendations"][recommendation] += 1
            
            # Count rejected signals
            if signal.get("rejected", False):
                stats["rejected_count"] += 1
                
            # Count processed today
            if "processed_timestamp" in signal:
                processed_date = datetime.fromisoformat(signal["processed_timestamp"]).date()
                if processed_date == datetime.now().date():
                    stats["processed_today"] += 1
                    
        # Calculate average confidence
        confidence_scores = [signal.get("confidence_score", 0) for signal in self.signal_history if "confidence_score" in signal]
        if confidence_scores:
            stats["avg_confidence"] = sum(confidence_scores) / len(confidence_scores)
            
        return stats

# Example usage
if __name__ == "__main__":
    # Create signal router
    router = SignalRouter()
    
    # Start update thread
    router.start_update_thread()
    
    try:
        # Run for a while
        for _ in range(10):
            # Get signals
            signals = router.get_signals(limit=5)
            
            print(f"Current signals in queue: {len(signals)}")
            for signal in signals:
                print(f"  {signal['symbol']} {signal['direction']} (confidence: {signal.get('confidence_score', 0)})")
                
            # Process next signal
            next_signal = router.get_next_signal()
            if next_signal:
                print(f"Processed signal: {next_signal['symbol']} {next_signal['direction']}")
                
            # Wait
            time.sleep(5)
            
        # Get stats
        stats = router.get_signal_stats()
        print("\nSignal statistics:")
        print(json.dumps(stats, indent=2))
    finally:
        # Stop update thread
        router.stop_update_thread()