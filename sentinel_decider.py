# sentinel_decider.py

import json
import logging
import os
import re
import requests
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum

# Import governance engine
try:
    from governance_engine import GovernanceEngine, GovernanceRole, VoteType
except ImportError:
    # Define minimal versions if import fails
    class GovernanceRole(Enum):
        STRATEGIST = "strategist"
        RISK_GOVERNOR = "risk_governor"
        PERFORMANCE_AUDITOR = "performance_auditor"
        PHASE_ORACLE = "phase_oracle"
    
    class VoteType(Enum):
        STRATEGY_CHANGE = "strategy_change"
        PARAMETER_ADJUSTMENT = "parameter_adjustment"
        PHASE_TRANSITION = "phase_transition"
        EMERGENCY_OVERRIDE = "emergency_override"
        ROLLBACK = "rollback"
    
    class GovernanceEngine:
        def __init__(self, config=None):
            pass
        
        def initiate_vote(self, vote_type, proposal, initiator_role):
            return None
        
        def cast_vote(self, vote_id, role, approve, reason=None):
            return False
        
        def execute_vote(self, vote_id):
            return False
        
        def log_role_action(self, role, action, details=None):
            return False

# Try to import from other modules
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_strategy_performance(self, strategy_name):
            return {}

try:
    from reinforcement_agent import ReinforcementAgent, MarketRegime
except ImportError:
    # Define minimal versions if import fails
    class MarketRegime:
        BULLISH = "bullish"
        BEARISH = "bearish"
        SIDEWAYS = "sideways"
        UNKNOWN = "unknown"
    
    class ReinforcementAgent:
        def __init__(self, *args, **kwargs):
            self.current_regime = MarketRegime.UNKNOWN
        
        def get_strategy_recommendations(self):
            return {}
        
        def update_market_regime(self, *args, **kwargs):
            return False
        
        def record_trade_result(self, *args, **kwargs):
            pass
        
        def update_volatility_index(self, *args, **kwargs):
            pass

try:
    from news_guard import NewsGuard
except ImportError:
    # Define a minimal version if the import fails
    class NewsGuard:
        def is_affected_by_news(self, currency_pair):
            return False, None
            
try:
    from agents.voting_system import VotingSystem
except ImportError:
    # Define a minimal version if the import fails
    class VotingSystem:
        def __init__(self, config_path=None):
            pass
            
        def decide_trade(self, context):
            return {
                "action": "hold",
                "confidence": 0,
                "reason": "VotingSystem not available"
            }

class DeciderMode(Enum):
    """Enum for different decider modes"""
    STANDARD = "standard"
    REINFORCEMENT = "reinforcement"
    MULTI_AGENT = "multi_agent"
    FLOW_CONSCIOUS = "flow-conscious"
    REFLECTIVE = "reflective"
    GOVERNANCE = "governance"
    LIVEOPS = "liveops"
    BULENOX_FUTURES = "bulenox-futures"  # Phase 13: Bulenox Futures Integration


class SentinelDecider:
    def __init__(self, phase=None):
        self.logger = logging.getLogger('sentinel_decider')
        self.config = self.load_decider_config()
        self.current_phase = phase or "10"  # Default to Phase 10 if not specified
        self.prompt_data = {}
        self.regime_awareness = False
        self.reinforcement_learning = False
        self.multi_agent_mode = True  # Multi-agent mode is still active
        self.flow_conscious_mode = True  # Flow-conscious mode is still active
        self.reflective_mode = True  # Enable reflective mode for Phase 8
        self.language_interface = True  # Enable language interface for Phase 8
        self.enable_self_questions = True  # Enable self-questioning for Phase 8
        self.governance_mode = True  # Enable governance mode for Phase 9
        self.roles_enabled = True  # Enable role-based delegation for Phase 9
        self.safeguard_core = True  # Enable protocol sovereignty for Phase 9
        self.liveops_mode = True  # Enable LiveOps mode for Phase 10
        self.automated_trading = True  # Enable automated trading for Phase 10
        self.multi_account = True  # Enable multi-account support for Phase 10
        self.passive_learning = True  # Enable passive learning for Phase 10
        self.bulenox_futures_mode = True  # Enable Bulenox Futures integration for Phase 13
        self.futures_trading = True  # Enable futures trading for Phase 13
        self.margin_calculation = True  # Enable margin calculation for Phase 13
        self.leverage_management = True  # Enable leverage management for Phase 13
        self.rl_agent = None
        self.voting_system = None
        self.liquidity_router = None
        self.intent_predictor = None
        self.language_reflection_engine = None
        self.governance_engine = None
        self.stealth_executor = None
        self.account_manager = None
        self.heartbeat_monitor = None
        self.bulenox_controller = None  # Bulenox AI Controller for Phase 13
        self.mode = DeciderMode.LIVEOPS  # Default to LiveOps mode
        
        # Load phase prompt if specified
        if self.current_phase is not None:
            try:
                self.load_phase_prompt(self.current_phase)
                self.logger.info(f"Loaded phase {self.current_phase} prompt successfully")
            except Exception as e:
                self.logger.error(f"Failed to load phase {self.current_phase} prompt: {e}")
        
        # Initialize reinforcement agent if needed
        if self.regime_awareness or self.reinforcement_learning:
            self.initialize_reinforcement_agent()
            if not self.multi_agent_mode:  # Only override if multi-agent is not enabled
                self.mode = DeciderMode.REINFORCEMENT
            
        # Initialize multi-agent system
        if self.multi_agent_mode:
            self.initialize_voting_system()
            if not self.flow_conscious_mode:  # Only set mode if flow-conscious is not enabled
                self.mode = DeciderMode.MULTI_AGENT
                self.logger.info("TRAE Phase 6: Multi-Agent Strategy Governance activated")
        
        # Initialize flow-conscious system for Phase 7
        if self.flow_conscious_mode:
            self.initialize_liquidity_router()
            self.initialize_intent_predictor()
            if not self.reflective_mode:  # Only set mode if reflective is not enabled
                self.mode = DeciderMode.FLOW_CONSCIOUS
                self.logger.info("TRAE Phase 7: Adaptive Liquidity Routing & Intent Prediction activated")
        
        # Initialize reflective system for Phase 8
        if self.reflective_mode:
            self.initialize_language_reflection_engine()
            if not self.governance_mode:  # Only set mode if governance is not enabled
                self.mode = DeciderMode.REFLECTIVE
                self.logger.info("TRAE Phase 8: Language Interface & Self-Reflection activated")
        
        # Initialize governance system for Phase 9
        if self.governance_mode:
            self.initialize_governance_engine()
            if not self.liveops_mode:  # Only set mode if liveops is not enabled
                self.mode = DeciderMode.GOVERNANCE
                self.logger.info("TRAE Phase 9: Governance & Sovereignty Layer activated")
        
        # Initialize LiveOps system for Phase 10
        if self.liveops_mode:
            self.initialize_liveops_system()
            if not self.bulenox_futures_mode:  # Only set mode if bulenox_futures is not enabled
                self.mode = DeciderMode.LIVEOPS
                self.logger.info("TRAE Phase 10: LiveOps Activation completed")
        
        # Initialize Bulenox Futures system for Phase 13
        if self.bulenox_futures_mode:
            self.initialize_bulenox_controller()
            self.mode = DeciderMode.BULENOX_FUTURES
            self.logger.info("TRAE Phase 13: Bulenox Futures Integration activated")
    
    def initialize_liquidity_router(self) -> None:
        """Initialize the adaptive liquidity routing system for Phase 7
        
        This system dynamically routes trades based on real-time liquidity conditions
        across different platforms (Exness, Bulenox, Binance).
        """
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Set up logging for liquidity routing
            liquidity_logger = logging.getLogger('liquidity_router')
            file_handler = logging.FileHandler('logs/liquidity_routing.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            liquidity_logger.addHandler(file_handler)
            
            # Initialize liquidity router with parameters from prompt data
            latency_limit = 120  # Default value
            if self.prompt_data and "parameters" in self.prompt_data:
                params = self.prompt_data["parameters"]
                if "latency_limit_ms" in params:
                    latency_limit = params["latency_limit_ms"]
            
            # For now, we'll use a simple dictionary to represent the router
            # In a real implementation, this would be a proper class
            self.liquidity_router = {
                "enabled": True,
                "latency_limit_ms": latency_limit,
                "platforms": ["Exness", "Bulenox", "Binance"],
                "logger": liquidity_logger,
                "metrics_file": "data/routing_metrics.json"
            }
            
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Initialize metrics file if it doesn't exist
            if not os.path.exists(self.liquidity_router["metrics_file"]):
                with open(self.liquidity_router["metrics_file"], "w") as f:
                    json.dump({
                        "total_reroutes": 0,
                        "successful_reroutes": 0,
                        "failed_reroutes": 0,
                        "average_latency_ms": 0,
                        "slippage_reduction": 0,
                        "platforms": {
                            "Exness": {"trades": 0, "avg_spread": 0, "avg_latency": 0},
                            "Bulenox": {"trades": 0, "avg_spread": 0, "avg_latency": 0},
                            "Binance": {"trades": 0, "avg_spread": 0, "avg_latency": 0}
                        }
                    }, f, indent=4)
            
            self.logger.info("Initialized adaptive liquidity routing system")
            
        except Exception as e:
            self.logger.error(f"Error initializing liquidity router: {e}")
            self.liquidity_router = None
    
    def initialize_bulenox_controller(self) -> None:
        """Initialize the Bulenox Futures controller for Phase 13
        
        This system integrates with Bulenox for futures trading, providing advanced
        margin calculation, leverage management, and futures-specific features.
        """
        try:
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.join("logs", "bulenox"), exist_ok=True)
            
            # Set up logging for Bulenox controller
            bulenox_logger = logging.getLogger('bulenox_controller')
            file_handler = logging.FileHandler('logs/bulenox/controller.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            bulenox_logger.addHandler(file_handler)
            
            # Import the BulenoxAIController class
            try:
                from bulenox_ai_controller import BulenoxAIController
                
                # Initialize the Bulenox controller
                self.bulenox_controller = BulenoxAIController()
                
                self.logger.info("Initialized Bulenox Futures controller")
                
            except ImportError as e:
                self.logger.error(f"Failed to import BulenoxAIController: {e}")
                self.bulenox_controller = None
                
        except Exception as e:
            self.logger.error(f"Error initializing Bulenox controller: {e}")
            self.bulenox_controller = None
    
    def initialize_intent_predictor(self) -> None:
        """Initialize the market intent prediction engine for Phase 7
        
        This system analyzes microstructure signals to predict short-term market intent
        and adjusts execution tactics accordingly.
        """
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Set up logging for intent prediction
            intent_logger = logging.getLogger('intent_predictor')
            file_handler = logging.FileHandler('logs/intent_signals.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            intent_logger.addHandler(file_handler)
            
            # Initialize intent predictor
            # For now, we'll use a simple dictionary to represent the predictor
            # In a real implementation, this would be a proper class
            self.intent_predictor = {
                "enabled": True,
                "intent_types": [
                    "Institutional Absorption",
                    "Spoofing / Fake Walls",
                    "Genuine Momentum",
                    "Exhaustion or Trap"
                ],
                "signals_file": "logs/intent_signals.json",
                "logger": intent_logger,
                "min_confidence": 70  # Minimum confidence threshold for intent classification
            }
            
            # Initialize signals file if it doesn't exist
            if not os.path.exists(self.intent_predictor["signals_file"]):
                with open(self.intent_predictor["signals_file"], "w") as f:
                    json.dump({
                        "total_signals": 0,
                        "classified_signals": 0,
                        "average_confidence": 0,
                        "signals_by_type": {
                            "Institutional Absorption": 0,
                            "Spoofing / Fake Walls": 0,
                            "Genuine Momentum": 0,
                            "Exhaustion or Trap": 0
                        }
                    }, f, indent=4)
            
            self.logger.info("Initialized market intent prediction engine")
            
        except Exception as e:
            self.logger.error(f"Error initializing intent predictor: {e}")
            self.intent_predictor = None
            
    def initialize_language_reflection_engine(self) -> None:
        """Initialize the language reflection engine for Phase 8
        
        This system enables natural language reasoning, self-reflection, and user interaction
        through a language-based interface.
        """
        try:
            # Import the LanguageReflectionEngine class
            from language_reflection_engine import LanguageReflectionEngine
            
            # Initialize language reflection engine with configuration
            config = {
                "enabled": True,
                "language_interface": self.language_interface,
                "enable_self_questions": self.enable_self_questions,
            }
            
            # Create the language reflection engine instance
            self.language_reflection_engine = LanguageReflectionEngine(config)
            
            self.logger.info("Initialized language reflection engine")
            
        except Exception as e:
            self.logger.error(f"Error initializing language reflection engine: {e}")
            self.language_reflection_engine = None
    
    def initialize_governance_engine(self) -> None:
        """Initialize the governance engine for Phase 9
        
        This system enables role-based delegation, voting on strategies, tracking rule changes,
        and protecting critical protocol elements.
        """
        try:
            # Create logs directory and governance subdirectory if they don't exist
            os.makedirs("logs/governance", exist_ok=True)
            os.makedirs("config_backups", exist_ok=True)
            
            # Set up logging for governance
            governance_logger = logging.getLogger('governance_engine')
            file_handler = logging.FileHandler('logs/governance/governance.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            governance_logger.addHandler(file_handler)
            
            # Initialize governance engine with parameters from prompt data
            config = {
                "enabled": True,
                "enable_voting": self.prompt_data.get("enable_voting", True),
                "roles_enabled": self.prompt_data.get("roles_enabled", True),
                "safeguard_core": self.prompt_data.get("safeguard_core", True),
                "quorum_threshold": self.prompt_data.get("quorum_threshold", 3),
                "votes_file": "logs/governance/votes.json",
                "role_actions_file": "logs/governance/role_actions.json",
                "protocol_changes_file": "logs/governance/protocol_changes.json",
                "immutable_configs": [
                    "config/core_security.yml",
                    "config/risk_limits.yml"
                ],
                "emergency_loss_threshold": 0.05,  # 5% loss triggers emergency mode
                "backup_frequency_days": 7  # Weekly backups
            }
            
            # Create the governance engine instance
            self.governance_engine = GovernanceEngine(config)
            
            # Log initial role actions
            self.governance_engine.log_role_action(
                GovernanceRole.PHASE_ORACLE, 
                "initialize_governance", 
                {"phase": self.current_phase, "timestamp": datetime.now().isoformat()}
            )
            
            self.logger.info("Initialized governance engine with role-based delegation")
            
        except Exception as e:
            self.logger.error(f"Error initializing governance engine: {e}")
            self.governance_engine = None
    
    def initialize_liveops_system(self) -> None:
        """Initialize the LiveOps system for Phase 10
        
        This system enables 24/7 automated trading operations, multi-account support,
        persistent deployment, and passive learning capabilities.
        """
        try:
            # Create logs directory and liveops subdirectory if they don't exist
            os.makedirs("logs/liveops", exist_ok=True)
            os.makedirs("data/accounts", exist_ok=True)
            os.makedirs("data/signals", exist_ok=True)
            
            # Set up logging for liveops
            liveops_logger = logging.getLogger('liveops')
            file_handler = logging.FileHandler('logs/liveops/operations.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            liveops_logger.addHandler(file_handler)
            
            # Load LiveOps configuration
            config_path = os.path.join("config", "liveops_config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)
                    self.logger.info(f"Loaded LiveOps configuration from {config_path}")
                except Exception as e:
                    self.logger.error(f"Error loading LiveOps configuration: {e}")
                    # Use default configuration
                    config = self._get_default_liveops_config()
            else:
                self.logger.warning(f"LiveOps configuration file {config_path} not found, using defaults")
                config = self._get_default_liveops_config()
            
            # Initialize stealth executor for broker interactions
            try:
                from liveops.stealth_executor import StealthExecutor
                self.stealth_executor = StealthExecutor(config_path)
                self.logger.info("Initialized stealth executor for broker interactions")
            except ImportError as e:
                self.logger.error(f"Error importing stealth executor: {e}")
                self.stealth_executor = None
            
            # Initialize account manager for multi-account support
            try:
                from liveops.account_manager import AccountManager
                self.account_manager = AccountManager(config_path)
                self.logger.info("Initialized account manager for multi-account support")
            except ImportError as e:
                self.logger.error(f"Error importing account manager: {e}")
                self.account_manager = None
            
            # Initialize heartbeat monitor for system health
            try:
                from liveops.heartbeat_monitor import HeartbeatMonitor
                heartbeat_interval = config.get("system", {}).get("heartbeat_interval_seconds", 60)
                self.heartbeat_monitor = HeartbeatMonitor(heartbeat_interval)
                self.logger.info("Initialized heartbeat monitor for system health")
            except ImportError as e:
                self.logger.error(f"Error importing heartbeat monitor: {e}")
                self.heartbeat_monitor = None
            
            # Initialize signal processor for handling trading signals
            try:
                from liveops.signal_processor import SignalProcessor
                signals_dir = config.get("system", {}).get("data_directory", "data")
                self.signal_processor = SignalProcessor(signals_dir, self.process_signal)
                self.logger.info("Initialized signal processor for handling trading signals")
            except ImportError as e:
                self.logger.error(f"Error importing signal processor: {e}")
                self.signal_processor = None
            
            # Initialize webhook handler for receiving signals via HTTP
            if config.get("signal_sources", {}).get("webhook", {}).get("enabled", False):
                try:
                    from liveops.webhook_handler import WebhookHandler
                    webhook_port = config.get("signal_sources", {}).get("webhook", {}).get("port", 5000)
                    self.webhook_handler = WebhookHandler(
                        port=webhook_port,
                        signals_dir=signals_dir,
                        signal_callback=self.signal_processor.add_signal if self.signal_processor else None
                    )
                    self.webhook_handler.start()
                    self.logger.info(f"Started webhook handler on port {webhook_port}")
                except ImportError as e:
                    self.logger.error(f"Error importing webhook handler: {e}")
                    self.webhook_handler = None
            
            # Initialize file handler for monitoring signal files
            if config.get("signal_sources", {}).get("file_drop", {}).get("enabled", False):
                try:
                    from liveops.file_handler import SignalFileHandler
                    watch_dir = config.get("signal_sources", {}).get("file_drop", {}).get("directory", "signals")
                    self.file_handler = SignalFileHandler(
                        watch_dir=watch_dir,
                        signals_dir=signals_dir,
                        signal_callback=self.signal_processor.add_signal if self.signal_processor else None
                    )
                    self.file_handler.start()
                    self.logger.info(f"Started file handler watching {watch_dir}")
                except ImportError as e:
                    self.logger.error(f"Error importing file handler: {e}")
                    self.file_handler = None
            
            # Start heartbeat monitor if available
            if self.heartbeat_monitor:
                self.heartbeat_monitor.start()
                self.logger.info("Started heartbeat monitor")
                
                # Register signal processor with heartbeat monitor
                if self.signal_processor:
                    self.heartbeat_monitor.register_callback(self.signal_processor.process_pending_signals)
                    self.logger.info("Registered signal processor with heartbeat monitor")
            
            self.logger.info("Initialized LiveOps system for 24/7 automated trading")
            
        except Exception as e:
            self.logger.error(f"Error initializing LiveOps system: {e}")
            self.stealth_executor = None
            self.account_manager = None
            self.heartbeat_monitor = None
            self.signal_processor = None
            self.webhook_handler = None
            self.file_handler = None
    
    def _get_default_liveops_config(self) -> Dict[str, Any]:
        """Get default LiveOps configuration.
        
        Returns:
            Dict[str, Any]: Default configuration
        """
        return {
            "system": {
                "heartbeat_interval_seconds": 60,
                "log_level": "INFO",
                "data_directory": "data"
            },
            "signal_sources": {
                "webhook": {
                    "enabled": True,
                    "port": 5000
                },
                "file_drop": {
                    "enabled": True,
                    "directory": "signals"
                },
                "tremius": {
                    "enabled": False,
                    "api_key": ""
                },
                "trae_ai": {
                    "enabled": False,
                    "api_key": ""
                }
            },
            "governance": {
                "max_daily_loss_percent": 2.0,
                "max_open_positions": 10,
                "trading_hours": {
                    "enabled": True,
                    "start_hour": 0,
                    "end_hour": 23,
                    "excluded_days": [5, 6]
                },
                "allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
                "allowed_strategies": ["trend_following", "breakout", "mean_reversion"]
            },
            "accounts": [
                {
                    "account_id": "default",
                    "broker": "Exness",
                    "lot_size": 0.01,
                    "max_daily_loss_percent": 2.0,
                    "enabled": True,
                    "locked": False,
                    "credentials_file": ".env"
                }
            ]
        }
    
    def decide_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Make a trade decision based on the signal.
        
        Args:
            signal (Dict[str, Any]): The trading signal
            
        Returns:
            Dict[str, Any]: Trade decision with action, tp_pips, sl_pips, and confidence
        """
        try:
            # Extract signal information
            symbol = signal.get("symbol", "").upper()
            direction = signal.get("direction", "").lower()
            strategy = signal.get("strategy", "").lower()
            entry_price = signal.get("entry_price")
            take_profit = signal.get("take_profit")
            stop_loss = signal.get("stop_loss")
            confidence = signal.get("confidence", 0.5)
            
            # Determine action based on direction
            action = "buy" if direction in ["buy", "long"] else "sell" if direction in ["sell", "short"] else "none"
            
            # Calculate TP/SL in pips if not provided
            tp_pips = signal.get("tp_pips")
            sl_pips = signal.get("sl_pips")
            
            if not tp_pips and entry_price and take_profit:
                # Convert price difference to pips
                if symbol.endswith("JPY"):
                    # For JPY pairs, 1 pip = 0.01
                    multiplier = 100
                else:
                    # For other pairs, 1 pip = 0.0001
                    multiplier = 10000
                    
                if action == "buy":
                    tp_pips = round((take_profit - entry_price) * multiplier)
                else:
                    tp_pips = round((entry_price - take_profit) * multiplier)
            
            if not sl_pips and entry_price and stop_loss:
                # Convert price difference to pips
                if symbol.endswith("JPY"):
                    # For JPY pairs, 1 pip = 0.01
                    multiplier = 100
                else:
                    # For other pairs, 1 pip = 0.0001
                    multiplier = 10000
                    
                if action == "buy":
                    sl_pips = round((entry_price - stop_loss) * multiplier)
                else:
                    sl_pips = round((stop_loss - entry_price) * multiplier)
            
            # Default TP/SL if not provided or calculated
            if not tp_pips:
                tp_pips = 50  # Default 50 pips take profit
            if not sl_pips:
                sl_pips = 30  # Default 30 pips stop loss
            
            # Ensure TP/SL are positive
            tp_pips = max(1, tp_pips)
            sl_pips = max(1, sl_pips)
            
            return {
                "action": action,
                "tp_pips": tp_pips,
                "sl_pips": sl_pips,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error making trade decision: {e}")
            return {
                "action": "none",
                "reason": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading signal.
        
        This method is called by the signal processor when a new signal is received.
        It validates the signal, makes a trade decision, and executes the trade if approved.
        
        Args:
            signal (Dict[str, Any]): The trading signal
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            self.logger.info(f"Processing signal: {signal.get('id')}")
            
            # Validate signal format
            required_fields = ["symbol", "direction", "strategy"]
            for field in required_fields:
                if field not in signal:
                    return {
                        "status": "rejected",
                        "reason": f"Missing required field: {field}",
                        "timestamp": datetime.now().isoformat(),
                        "signal_id": signal.get("id", "unknown")
                    }
            
            # Validate signal against governance rules
            if self.governance_mode and self.governance_engine:
                # Check if trading is allowed for this symbol
                symbol = signal.get("symbol", "").upper()
                allowed_symbols = self.config.get("governance", {}).get("allowed_symbols", [])
                if allowed_symbols and symbol not in allowed_symbols:
                    return {
                        "status": "rejected",
                        "reason": f"Symbol {symbol} not allowed by governance rules",
                        "timestamp": datetime.now().isoformat(),
                        "signal_id": signal.get("id", "unknown")
                    }
                
                # Check if strategy is allowed
                strategy = signal.get("strategy", "").lower()
                allowed_strategies = self.config.get("governance", {}).get("allowed_strategies", [])
                if allowed_strategies and strategy not in [s.lower() for s in allowed_strategies]:
                    return {
                        "status": "rejected",
                        "reason": f"Strategy {strategy} not allowed by governance rules",
                        "timestamp": datetime.now().isoformat(),
                        "signal_id": signal.get("id", "unknown")
                    }
                
                # Check trading hours
                trading_hours = self.config.get("governance", {}).get("trading_hours", {})
                if trading_hours.get("enabled", False):
                    now = datetime.now()
                    day_of_week = now.weekday()  # 0-6 (Monday-Sunday)
                    hour = now.hour
                    
                    # Check excluded days
                    excluded_days = trading_hours.get("excluded_days", [])
                    if day_of_week in excluded_days:
                        return {
                            "status": "rejected",
                            "reason": "Trading not allowed on this day",
                            "timestamp": datetime.now().isoformat(),
                            "signal_id": signal.get("id", "unknown")
                        }
                    
                    # Check trading hours
                    start_hour = trading_hours.get("start_hour", 0)
                    end_hour = trading_hours.get("end_hour", 23)
                    if hour < start_hour or hour >= end_hour:
                        return {
                            "status": "rejected",
                            "reason": "Trading not allowed at this hour",
                            "timestamp": datetime.now().isoformat(),
                            "signal_id": signal.get("id", "unknown")
                        }
            
            # Make trade decision
            decision = self.decide_trade(signal)
            
            # Execute trade if approved
            if decision.get("action") in ["buy", "sell"] and self.stealth_executor and self.account_manager:
                # Get active accounts
                active_accounts = self.account_manager.get_active_accounts()
                
                # Execute trade for each active account
                execution_results = []
                for account in active_accounts:
                    # Skip accounts that don't support this symbol
                    account_allowed_symbols = account.get("allowed_symbols", [])
                    if account_allowed_symbols and symbol not in account_allowed_symbols:
                        self.logger.info(f"Skipping account {account_id}: Symbol {symbol} not allowed")
                        continue
                    account_id = account.get("account_id")
                    broker = account.get("broker")
                    lot_size = account.get("lot_size", 0.01)
                    
                    # Execute the trade
                    result = self.stealth_executor.execute_trade(
                        broker=broker,
                        account_id=account_id,
                        symbol=signal.get("symbol", ""),
                        action=decision.get("action"),
                        position_size=lot_size,
                        tp_pips=decision.get("tp_pips"),
                        sl_pips=decision.get("sl_pips")
                    )
                    
                    execution_results.append({
                        "account_id": account_id,
                        "result": result
                    })
                
                return {
                    "status": "executed",
                    "decision": decision,
                    "execution_results": execution_results,
                    "timestamp": datetime.now().isoformat(),
                    "signal_id": signal.get("id", "unknown")
                }
            
            return {
                "status": "processed",
                "decision": decision,
                "timestamp": datetime.now().isoformat(),
                "signal_id": signal.get("id", "unknown")
            }
            
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            return {
                "status": "error",
                "reason": str(e),
                "timestamp": datetime.now().isoformat(),
                "signal_id": signal.get("id", "unknown")
            }
    
    def check_weekly_reflection_schedule(self) -> None:
        """Check if it's time to generate a weekly reflection and generate one if needed"""
        if not self.language_reflection_engine:
            return
            
        try:
            # The check is now handled by the LanguageReflectionEngine class
            self.language_reflection_engine.check_weekly_reflection_schedule()
        except Exception as e:
            self.logger.error(f"Error checking weekly reflection schedule: {e}")
    
    def generate_weekly_reflection(self) -> None:
        """Generate a weekly reflection report based on trade logs and metrics"""
        if not self.language_reflection_engine:
            return
            
        try:
            # The reflection generation is now handled by the LanguageReflectionEngine class
            self.language_reflection_engine.generate_weekly_reflection()
        except Exception as e:
            self.logger.error(f"Error generating weekly reflection: {e}")
    
    def _load_log_file(self, file_path: str) -> str:
        """Load a log file if it exists, return empty string otherwise"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    # Return last 100 lines for efficiency
                    lines = f.readlines()
                    return "".join(lines[-100:])
            return ""
        except Exception as e:
            self.logger.error(f"Error loading log file {file_path}: {e}")
            return ""
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load a JSON file if it exists, return empty dict otherwise"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading JSON file {file_path}: {e}")
            return {}
    
    def _generate_reflection_content(self, data_sources: Dict) -> str:
        """Generate the content for the weekly reflection"""
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Start with header
        content = f"# TRAE Weekly Self-Reflection\n\n"
        content += f"**Generated:** {timestamp}\n\n"
        content += f"**Current Phase:** {self.current_phase}\n\n"
        
        # Add sections for each reflection question
        for question in self.language_reflection_engine["reflection_questions"]:
            content += f"## {question}\n\n"
            
            # Generate answer based on available data
            # In a real implementation, this would use an LLM to generate insightful answers
            # For now, we'll just add placeholder text
            if question == "What trades performed best and why?":
                content += self._reflect_on_best_trades(data_sources)
            elif question == "What risk decisions failed or succeeded?":
                content += self._reflect_on_risk_decisions(data_sources)
            elif question == "What patterns or anomalies were detected?":
                content += self._reflect_on_patterns(data_sources)
            elif question == "What phase logic needs refinement?":
                content += self._reflect_on_phase_logic(data_sources)
            
            content += "\n\n"
        
        # Add summary section
        content += "## Summary and Next Steps\n\n"
        content += "Based on this week's performance, the system should focus on:\n\n"
        content += "1. [Generated recommendation based on data]\n"
        content += "2. [Generated recommendation based on data]\n"
        content += "3. [Generated recommendation based on data]\n\n"
        
        return content
    
    def _reflect_on_best_trades(self, data_sources: Dict) -> str:
        """Generate reflection on best performing trades"""
        # In a real implementation, this would analyze trade data and generate insights
        return "Analysis of trade performance data shows that [strategy X] performed best with a win rate of [Y]%. " \
               "This appears to be due to [reason Z] as evidenced by [observation].\n\n" \
               "The following specific trades were particularly successful:\n" \
               "- [Trade details]\n" \
               "- [Trade details]"
    
    def _reflect_on_risk_decisions(self, data_sources: Dict) -> str:
        """Generate reflection on risk decisions"""
        # In a real implementation, this would analyze risk management data
        return "Risk management decisions that succeeded:\n" \
               "- [Decision details]\n\n" \
               "Risk management decisions that failed:\n" \
               "- [Decision details]\n\n" \
               "The primary factor in successful risk management appears to be [factor]."
    
    def _reflect_on_patterns(self, data_sources: Dict) -> str:
        """Generate reflection on patterns and anomalies"""
        # In a real implementation, this would analyze pattern recognition data
        return "Notable patterns detected:\n" \
               "- [Pattern details]\n\n" \
               "Anomalies that require attention:\n" \
               "- [Anomaly details]\n\n" \
               "These patterns suggest [insight about market conditions]."
    
    def _reflect_on_phase_logic(self, data_sources: Dict) -> str:
        """Generate reflection on phase logic that needs refinement"""
        # In a real implementation, this would analyze phase performance data
        return "Current phase logic that could be improved:\n" \
               "- [Logic component] - [Reason for improvement]\n" \
               "- [Logic component] - [Reason for improvement]\n\n" \
               "Suggested modifications:\n" \
               "- [Specific modification details]"
    
    def _send_to_governance_channel(self, content: str) -> None:
        """Send reflection content to governance channel"""
        # In a real implementation, this would send the content to Slack, Telegram, etc.
        # For now, we'll just log it
        self.logger.info("Sending weekly reflection to governance channel")
        
        # Truncate content for logging
        log_content = content[:500] + "..." if len(content) > 500 else content
        self.logger.debug(f"Governance channel content: {log_content}")
    
    def process_user_query(self, query: str) -> str:
        """Process a natural language query from a user
        
        Args:
            query (str): The user's natural language query
            
        Returns:
            str: The response to the query
        """
        if not self.language_reflection_engine:
            return "Language interface is not enabled."
            
        try:
            # The query processing is now handled by the LanguageReflectionEngine class
            return self.language_reflection_engine.process_user_query(query)
                
        except Exception as e:
            self.logger.error(f"Error processing user query: {e}")
            return f"Error processing your query: {str(e)}"
    
    # Helper methods for query history and answering specific queries have been moved to the LanguageReflectionEngine class
        
    def _generate_decision_reasoning(self, context: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Generate natural language reasoning for a trade decision
        
        Args:
            context (Dict[str, Any]): The decision context with market data and signals
            decision (Dict[str, Any]): The trade decision with action and confidence
            
        Returns:
            str: Natural language explanation of the decision reasoning
        """
        try:
            # Extract key information from context and decision
            action = decision.get("action", "hold")
            confidence = decision.get("confidence", 0)
            market_intent = context.get("market_intent", {})
            liquidity_routing = context.get("liquidity_routing", {})
            market_data = context.get("market_data", {})
            
            # Build reasoning based on available information
            reasoning_parts = []
            
            # Explain the action
            if action == "buy":
                reasoning_parts.append(f"I decided to BUY with {confidence}% confidence.")
            elif action == "sell":
                reasoning_parts.append(f"I decided to SELL with {confidence}% confidence.")
            elif action == "exit":
                reasoning_parts.append(f"I decided to EXIT the position with {confidence}% confidence.")
            else:  # hold
                reasoning_parts.append(f"I decided to HOLD with {confidence}% confidence.")
            
            # Explain market intent if available
            if market_intent and "intent_type" in market_intent and market_intent["intent_type"] != "Unknown":
                intent_type = market_intent["intent_type"]
                intent_confidence = market_intent.get("confidence", 0)
                
                reasoning_parts.append(f"I detected {intent_type} market intent with {intent_confidence}% confidence.")
                
                # Add specific reasoning based on intent type
                if intent_type == "Institutional Absorption":
                    reasoning_parts.append("Large orders are absorbing liquidity, suggesting strong institutional interest.")
                elif intent_type == "Spoofing / Fake Walls":
                    reasoning_parts.append("Detected potential spoofing with rapid order placement and cancellation.")
                elif intent_type == "Genuine Momentum":
                    reasoning_parts.append("Price movement is supported by consistent volume and order flow.")
                elif intent_type == "Exhaustion or Trap":
                    reasoning_parts.append("Current price movement shows signs of exhaustion or potential trap setup.")
            
            # Explain liquidity routing if available
            if liquidity_routing and "platform" in liquidity_routing:
                platform = liquidity_routing["platform"]
                reason = liquidity_routing.get("reason", "optimal execution")
                
                reasoning_parts.append(f"I routed this trade through {platform} for {reason}.")
            
            # Add market condition context if available
            if market_data:
                if "market_condition" in market_data:
                    reasoning_parts.append(f"Current market condition: {market_data['market_condition']}.")
                
                if "volatility" in market_data:
                    volatility = market_data["volatility"]
                    if volatility > 0.8:
                        reasoning_parts.append("Market volatility is extremely high.")
                    elif volatility > 0.5:
                        reasoning_parts.append("Market volatility is elevated.")
                    elif volatility < 0.2:
                        reasoning_parts.append("Market volatility is unusually low.")
            
            # Join all reasoning parts
            reasoning = " ".join(reasoning_parts)
            
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Error generating decision reasoning: {e}")
            return f"Decision made with {decision.get('confidence', 0)}% confidence based on available market data."
    
    def initialize_voting_system(self, config_path: str = None) -> None:
        """Initialize the multi-agent voting system
        
        Args:
            config_path (str, optional): Path to agent registry config. Defaults to None.
        """
        try:
            # Use config path from prompt data if available
            if not config_path and self.prompt_data and "parameters" in self.prompt_data:
                config_path = self.prompt_data["parameters"].get("agent_registry_path")
            
            # Default path if not specified
            if not config_path:
                config_path = "config/agents_registry.yml"
            
            # Initialize voting system
            self.voting_system = VotingSystem(config_path)
            
            # Configure voting system based on prompt data
            if self.prompt_data and "parameters" in self.prompt_data:
                params = self.prompt_data["parameters"]
                
                # Set voting method
                if "voting_method" in params:
                    self.voting_system.voting_method = params["voting_method"]
                
                # Set veto enabled
                if "veto_enabled" in params:
                    self.voting_system.veto_enabled = params["veto_enabled"]
                
                # Set governance mode
                if "governance_mode" in params:
                    self.voting_system.governance_mode = params["governance_mode"]
                
                # Set quorum threshold
                if "quorum" in params:
                    self.voting_system.quorum_threshold = params["quorum"]
            
            self.logger.info(f"Initialized multi-agent voting system with {len(self.voting_system.agents)} agents")
            
        except Exception as e:
            self.logger.error(f"Error initializing voting system: {e}")
            self.voting_system = None
    
    def execute_bulenox_futures_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a futures trade through the Bulenox controller.
        
        Args:
            signal (Dict[str, Any]): Trading signal with market data and action
            
        Returns:
            Dict[str, Any]: Execution result with status and details
        """
        try:
            if not self.bulenox_controller:
                return {
                    "status": "error",
                    "message": "Bulenox controller not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Extract signal data
            symbol = signal.get("symbol", "")
            action = signal.get("action", "buy")
            lot_size = signal.get("lot_size", 1)  # Default to 1 contract
            tp_pips = signal.get("tp_pips")
            sl_pips = signal.get("sl_pips")
            
            # Ensure session is active
            if not self.bulenox_controller.session_active:
                self.logger.info("Starting Bulenox session for trade execution")
                session_result = self.bulenox_controller.start_session()
                if not session_result.get("success", False):
                    return {
                        "status": "error",
                        "message": f"Failed to start Bulenox session: {session_result.get('message', 'Unknown error')}",
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Execute the trade
            execution_result = self.bulenox_controller.execute_trade(
                symbol=symbol,
                direction=action,  # buy or sell
                quantity=lot_size,
                tp_pips=tp_pips,
                sl_pips=sl_pips
            )
            
            # Log the result
            if execution_result.get("success", False):
                self.logger.info(f"Successfully executed Bulenox futures trade: {symbol} {action} {lot_size} contracts")
            else:
                self.logger.error(f"Failed to execute Bulenox futures trade: {execution_result.get('message', 'Unknown error')}")
            
            return {
                "status": "success" if execution_result.get("success", False) else "error",
                "message": execution_result.get("message", ""),
                "trade_id": execution_result.get("trade_id", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing Bulenox futures trade: {e}")
            return {
                "status": "error",
                "message": f"Exception: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def decide_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Make a trading decision based on the provided signal."""
        market_data = signal.get("market_data", {})
        strategy = signal.get("strategy", "unknown")
        trade_type = signal.get("type", "entry")
        
        # Default decision
        decision = {
            "action": "hold",
            "confidence": 0,
            "reasoning": "Default decision due to insufficient data",
            "timestamp": datetime.now().isoformat()
        }
        
        # Use Bulenox Futures mode if enabled (Phase 13)
        if self.mode == DeciderMode.BULENOX_FUTURES and hasattr(self, 'bulenox_controller'):
            try:
                # Log the incoming signal
                self.logger.info(f"Bulenox Futures received signal: {strategy} for {trade_type}")
                
                # Execute the trade through Bulenox controller
                execution_result = self.execute_bulenox_futures_trade(signal)
                
                # Update decision based on execution result
                if execution_result["status"] == "success":
                    decision = {
                        "action": signal.get("action", "buy"),
                        "confidence": signal.get("confidence", 0.8),
                        "reasoning": f"Bulenox Futures trade executed: {execution_result.get('message', '')}",
                        "timestamp": datetime.now().isoformat(),
                        "trade_id": execution_result.get("trade_id", ""),
                        "execution": "bulenox_futures"
                    }
                else:
                    decision = {
                        "action": "hold",
                        "confidence": 0,
                        "reasoning": f"Bulenox Futures trade failed: {execution_result.get('message', '')}",
                        "timestamp": datetime.now().isoformat(),
                        "execution": "bulenox_futures"
                    }
                
                return decision
                
            except Exception as e:
                self.logger.error(f"Error in Bulenox Futures trade decision: {e}")
                decision["reasoning"] = f"Error in Bulenox Futures trade decision: {str(e)}"
                return decision
        
        # Use LiveOps mode if enabled (Phase 10)
        elif self.mode == DeciderMode.LIVEOPS and hasattr(self, 'stealth_executor') and hasattr(self, 'account_manager'):
            try:
                # Log the incoming signal
                self.logger.info(f"LiveOps received signal: {strategy} for {trade_type}")
                
                # Step 1: Validate signal against governance rules
                if hasattr(self, 'governance_engine'):
                    # Prepare context for governance validation
                    context = {
                        "market_data": market_data,
                        "strategy": strategy,
                        "trade_type": trade_type,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Add indicators if available
                    if "indicators" in signal:
                        context["indicators"] = signal["indicators"]
                    
                    # Add news data if available
                    if "news" in signal:
                        context["news"] = signal["news"]
                    
                    # Check if this trade violates any governance rules
                    validation_result = self.governance_engine.validate_trade(context)
                    
                    if not validation_result["valid"]:
                        # Trade violates governance rules, reject it
                        decision = {
                            "action": "hold",
                            "confidence": 0,
                            "reasoning": f"Trade rejected: {validation_result['reason']}",
                            "timestamp": datetime.now().isoformat(),
                            "governance": {
                                "status": "rejected",
                                "reason": validation_result['reason']
                            }
                        }
                        
                        # Log the rejection
                        self.logger.warning(f"LiveOps rejected trade due to governance rules: {validation_result['reason']}")
                        
                        # Record the violation
                        self._record_governance_violation(strategy, validation_result)
                        
                        return decision
                
                # Step 2: Get active accounts from account manager
                active_accounts = self.account_manager.get_active_accounts()
                
                if not active_accounts:
                    decision["reasoning"] = "No active accounts available for trading"
                    self.logger.warning("LiveOps: No active accounts available for trading")
                    return decision
                
                # Step 3: Process the signal for each active account
                execution_results = []
                
                for account in active_accounts:
                    # Check account-specific rules (max loss, time restrictions, etc.)
                    account_check = self._check_account_restrictions(account, signal)
                    
                    if not account_check["valid"]:
                        # Skip this account and log the reason
                        self.logger.info(f"Account {account['account_id']} skipped: {account_check['reason']}")
                        execution_results.append({
                            "account_id": account['account_id'],
                            "status": "skipped",
                            "reason": account_check['reason']
                        })
                        continue
                    
                    # Adjust position size based on account settings
                    position_size = self._calculate_position_size(account, signal)
                    
                    # Execute the trade using stealth executor
                    execution_result = self.stealth_executor.execute_trade(
                        broker=account["broker"],
                        account_id=account["account_id"],
                        symbol=signal.get("symbol", ""),
                        action=signal.get("action", "buy"),
                        position_size=position_size,
                        tp_pips=signal.get("tp_pips"),
                        sl_pips=signal.get("sl_pips")
                    )
                    
                    # Add to results
                    execution_results.append(execution_result)
                    
                    # Log the execution
                    if execution_result["status"] == "success":
                        self.logger.info(f"Trade executed for account {account['account_id']}: {execution_result['trade_id']}")
                    else:
                        self.logger.warning(f"Trade execution failed for account {account['account_id']}: {execution_result['reason']}")
                
                # Step 4: Update decision based on execution results
                successful_executions = [r for r in execution_results if r.get("status") == "success"]
                
                if successful_executions:
                    decision = {
                        "action": signal.get("action", "buy"),
                        "confidence": signal.get("confidence", 75),
                        "reasoning": signal.get("reasoning", "Automated execution via LiveOps"),
                        "timestamp": datetime.now().isoformat(),
                        "executions": execution_results,
                        "accounts_total": len(active_accounts),
                        "accounts_executed": len(successful_executions)
                    }
                else:
                    decision = {
                        "action": "hold",
                        "confidence": 0,
                        "reasoning": "Execution failed on all accounts",
                        "timestamp": datetime.now().isoformat(),
                        "executions": execution_results
                    }
                
                # Step 5: Record the trade in logs
                self._record_trade_execution(signal, decision)
                
                # Step 6: If passive learning is enabled, record signal for later analysis
                if hasattr(self, 'passive_learning') and self.passive_learning:
                    self._record_signal_for_learning(signal)
                
                return decision
                
            except Exception as e:
                self.logger.error(f"Error in LiveOps trade execution: {e}")
                decision["reasoning"] = f"Error in LiveOps execution: {str(e)}"
                return decision
        
        # Use governance mode if enabled (Phase 9)
        if self.mode == DeciderMode.GOVERNANCE and self.governance_engine:
            try:
                # Prepare context for governance decision
                context = {
                    "market_data": market_data,
                    "strategy": strategy,
                    "trade_type": trade_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add indicators if available
                if "indicators" in signal:
                    context["indicators"] = signal["indicators"]
                
                # Add news data if available
                if "news" in signal:
                    context["news"] = signal["news"]
                
                # Add account info if available
                if "account_info" in signal:
                    context["account_info"] = signal["account_info"]
                
                # Add trade info if available
                if "trade_info" in signal:
                    context["trade_info"] = signal["trade_info"]
                
                # Step 1: Check if this trade requires governance approval
                requires_approval = self.governance_engine.check_trade_requires_approval(context)
                
                # Step 2: If approval required, initiate a vote
                if requires_approval:
                    vote_id = self.governance_engine.initiate_vote(
                        vote_type=VoteType.STRATEGY_CHANGE,
                        description=f"Trade approval for {strategy} strategy",
                        context=context,
                        proposed_by=GovernanceRole.STRATEGIST
                    )
                    
                    # Check if we have enough votes for immediate decision
                    vote_result = self.governance_engine.check_vote_status(vote_id)
                    
                    if vote_result["status"] == "approved":
                        # Use the approved decision
                        approved_decision = vote_result["decision"]
                        decision = {
                            "action": approved_decision.get("action", "hold"),
                            "confidence": approved_decision.get("confidence", 50),
                            "reasoning": approved_decision.get("reasoning", "Approved by governance vote"),
                            "timestamp": datetime.now().isoformat(),
                            "governance": {
                                "vote_id": vote_id,
                                "status": "approved",
                                "roles_voted": vote_result.get("roles_voted", [])
                            }
                        }
                    elif vote_result["status"] == "rejected":
                        # Use hold action for rejected decisions
                        decision = {
                            "action": "hold",
                            "confidence": 0,
                            "reasoning": "Rejected by governance vote",
                            "timestamp": datetime.now().isoformat(),
                            "governance": {
                                "vote_id": vote_id,
                                "status": "rejected",
                                "roles_voted": vote_result.get("roles_voted", [])
                            }
                        }
                    else:
                        # Not enough votes yet, use default action with pending status
                        decision = {
                            "action": "hold",
                            "confidence": 0,
                            "reasoning": "Pending governance approval",
                            "timestamp": datetime.now().isoformat(),
                            "governance": {
                                "vote_id": vote_id,
                                "status": "pending",
                                "roles_voted": vote_result.get("roles_voted", [])
                            }
                        }
                else:
                    # No approval required, use reflective mode decision process
                    # Step 1: Predict market intent
                    intent = self.predict_market_intent(context)
                    
                    # Step 2: Get decision from voting system (still using multi-agent consensus)
                    vote_decision = self.voting_system.decide_trade(context) if self.voting_system else {
                        "action": "hold",
                        "confidence": 0,
                        "reason": "Voting system not available"
                    }
                    
                    # Step 3: Determine optimal liquidity routing
                    routing = self.determine_liquidity_routing(context, vote_decision["action"])
                    
                    # Step 4: Adjust execution based on intent and routing
                    adjusted_decision = self.adjust_execution(vote_decision, intent, routing)
                    
                    # Step 5: Check with RiskGovernor role for risk assessment
                    risk_assessment = self.governance_engine.assess_risk(adjusted_decision, context, GovernanceRole.RISK_GOVERNOR)
                    
                    if risk_assessment["approved"]:
                        # Map adjusted decision to our format with governance info
                        decision = {
                            "action": adjusted_decision["action"],
                            "confidence": adjusted_decision["confidence"],
                            "reasoning": adjusted_decision["reasoning"],
                            "timestamp": adjusted_decision.get("timestamp", datetime.now().isoformat()),
                            "voting_method": vote_decision.get("voting_method", "unknown"),
                            "votes": vote_decision.get("votes", []),
                            "market_intent": intent["intent_type"],
                            "intent_confidence": intent["confidence"],
                            "liquidity_routing": {
                                "platform": routing["platform"],
                                "reason": routing["reason"]
                            },
                            "governance": {
                                "risk_assessment": "approved",
                                "risk_score": risk_assessment.get("risk_score", 0),
                                "approving_role": "RISK_GOVERNOR"
                            }
                        }
                    else:
                        # Risk governor rejected the trade
                        decision = {
                            "action": "hold",
                            "confidence": 0,
                            "reasoning": risk_assessment.get("reason", "Rejected by Risk Governor"),
                            "timestamp": datetime.now().isoformat(),
                            "governance": {
                                "risk_assessment": "rejected",
                                "risk_score": risk_assessment.get("risk_score", 0),
                                "rejecting_role": "RISK_GOVERNOR"
                            }
                        }
                    
                    # Add regime info if available
                    if "regime" in vote_decision:
                        decision["market_regime"] = vote_decision["regime"]
                
                # Log the governance decision
                self.governance_engine.log_role_action(
                    role=GovernanceRole.PERFORMANCE_AUDITOR,
                    action="trade_decision_audit",
                    details={
                        "strategy": strategy,
                        "action": decision["action"],
                        "confidence": decision["confidence"],
                        "governance_status": decision.get("governance", {}).get("status", "direct")
                    }
                )
                
                self.logger.info(f"Governance decision: {decision['action']} with {decision['confidence']}% confidence")
                return decision
                
            except Exception as e:
                self.logger.error(f"Error in governance decision: {e}")
                # Fall back to reflective mode
        
        # Use reflective mode if enabled (Phase 8)
        if self.mode == DeciderMode.REFLECTIVE and self.reflective_mode:
            try:
                # Prepare context for reflective decision
                context = {
                    "market_data": market_data,
                    "strategy": strategy,
                    "trade_type": trade_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add indicators if available
                if "indicators" in signal:
                    context["indicators"] = signal["indicators"]
                
                # Add news data if available
                if "news" in signal:
                    context["news"] = signal["news"]
                
                # Add account info if available
                if "account_info" in signal:
                    context["account_info"] = signal["account_info"]
                
                # Add trade info if available
                if "trade_info" in signal:
                    context["trade_info"] = signal["trade_info"]
                
                # Use flow-conscious mode for the actual decision
                # Step 1: Predict market intent
                intent = self.predict_market_intent(context)
                
                # Step 2: Get decision from voting system (still using multi-agent consensus)
                vote_decision = self.voting_system.decide_trade(context) if self.voting_system else {
                    "action": "hold",
                    "confidence": 0,
                    "reason": "Voting system not available"
                }
                
                # Step 3: Determine optimal liquidity routing
                routing = self.determine_liquidity_routing(context, vote_decision["action"])
                
                # Step 4: Adjust execution based on intent and routing
                adjusted_decision = self.adjust_execution(vote_decision, intent, routing)
                
                # Map adjusted decision to our format
                decision = {
                    "action": adjusted_decision["action"],
                    "confidence": adjusted_decision["confidence"],
                    "reasoning": adjusted_decision["reasoning"],
                    "timestamp": adjusted_decision.get("timestamp", datetime.now().isoformat()),
                    "voting_method": vote_decision.get("voting_method", "unknown"),
                    "votes": vote_decision.get("votes", []),
                    "market_intent": intent["intent_type"],
                    "intent_confidence": intent["confidence"],
                    "liquidity_routing": {
                        "platform": routing["platform"],
                        "reason": routing["reason"]
                    }
                }
                
                # Add regime info if available
                if "regime" in vote_decision:
                    decision["market_regime"] = vote_decision["regime"]
                
                # Generate natural language reasoning for the decision
                if self.language_interface:
                    decision["natural_language_reasoning"] = self._generate_decision_reasoning(decision, intent, routing, market_data)
                
                # Check if we need to generate a weekly reflection
                if self.enable_self_questions and self.language_reflection_engine:
                    current_time = datetime.now()
                    # Generate weekly reflection on Sunday at midnight
                    if current_time.weekday() == 6 and current_time.hour == 0 and current_time.minute < 5:
                        self.language_reflection_engine.generate_weekly_reflection()
                
                self.logger.info(f"Reflective decision: {decision['action']} with {decision['confidence']}% confidence, routed to {routing['platform']}")
                return decision
                
            except Exception as e:
                self.logger.error(f"Error in reflective decision: {e}")
                # Fall back to flow-conscious mode
        
        # Use flow-conscious mode if enabled (Phase 7)
        if self.mode == DeciderMode.FLOW_CONSCIOUS and self.liquidity_router and self.intent_predictor:
            try:
                # Prepare context for flow-conscious decision
                context = {
                    "market_data": market_data,
                    "strategy": strategy,
                    "trade_type": trade_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add indicators if available
                if "indicators" in signal:
                    context["indicators"] = signal["indicators"]
                
                # Add news data if available
                if "news" in signal:
                    context["news"] = signal["news"]
                
                # Add account info if available
                if "account_info" in signal:
                    context["account_info"] = signal["account_info"]
                
                # Add trade info if available
                if "trade_info" in signal:
                    context["trade_info"] = signal["trade_info"]
                
                # Step 1: Predict market intent
                intent = self.predict_market_intent(context)
                
                # Step 2: Get decision from voting system (still using multi-agent consensus)
                vote_decision = self.voting_system.decide_trade(context) if self.voting_system else {
                    "action": "hold",
                    "confidence": 0,
                    "reason": "Voting system not available"
                }
                
                # Step 3: Determine optimal liquidity routing
                routing = self.determine_liquidity_routing(context, vote_decision["action"])
                
                # Step 4: Adjust execution based on intent and routing
                adjusted_decision = self.adjust_execution(vote_decision, intent, routing)
                
                # Map adjusted decision to our format
                decision = {
                    "action": adjusted_decision["action"],
                    "confidence": adjusted_decision["confidence"],
                    "reasoning": adjusted_decision["reasoning"],
                    "timestamp": adjusted_decision.get("timestamp", datetime.now().isoformat()),
                    "voting_method": vote_decision.get("voting_method", "unknown"),
                    "votes": vote_decision.get("votes", []),
                    "market_intent": intent["intent_type"],
                    "intent_confidence": intent["confidence"],
                    "liquidity_routing": {
                        "platform": routing["platform"],
                        "reason": routing["reason"]
                    }
                }
                
                # Add regime info if available
                if "regime" in vote_decision:
                    decision["market_regime"] = vote_decision["regime"]
                
                self.logger.info(f"Flow-conscious decision: {decision['action']} with {decision['confidence']}% confidence, routed to {routing['platform']}")
                return decision
                
            except Exception as e:
                self.logger.error(f"Error in flow-conscious decision: {e}")
                # Fall back to multi-agent mode
        
        # Use multi-agent voting system if enabled
        if self.mode == DeciderMode.MULTI_AGENT and self.voting_system:
            try:
                # Prepare context for agents
                context = {
                    "market_data": market_data,
                    "strategy": strategy,
                    "trade_type": trade_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add indicators if available
                if "indicators" in signal:
                    context["indicators"] = signal["indicators"]
                
                # Add news data if available
                if "news" in signal:
                    context["news"] = signal["news"]
                
                # Add account info if available
                if "account_info" in signal:
                    context["account_info"] = signal["account_info"]
                
                # Add trade info if available
                if "trade_info" in signal:
                    context["trade_info"] = signal["trade_info"]
                
                # Get decision from voting system
                vote_decision = self.voting_system.decide_trade(context)
                
                # Map vote decision to our format
                decision = {
                    "action": vote_decision["action"],
                    "confidence": vote_decision["confidence"],
                    "reasoning": vote_decision["reason"],
                    "timestamp": vote_decision.get("timestamp", datetime.now().isoformat()),
                    "voting_method": vote_decision.get("voting_method", "unknown"),
                    "votes": vote_decision.get("votes", [])
                }
                
                # Add regime info if available
                if "regime" in vote_decision:
                    decision["market_regime"] = vote_decision["regime"]
                
                self.logger.info(f"Multi-agent decision: {decision['action']} with {decision['confidence']}% confidence")
                return decision
                
            except Exception as e:
                self.logger.error(f"Error in multi-agent decision: {e}")
                # Fall back to standard or reinforcement mode
        
        # Use reinforcement learning mode
        if self.mode == DeciderMode.REINFORCEMENT:
            # Update market regime if enabled
            if self.regime_awareness and self.rl_agent:
                try:
                    ema_short = market_data.get("ema50", 0)
                    ema_long = market_data.get("ema200", 0)
                    atr = market_data.get("atr", 0)
                    atr_change = market_data.get("atr_change", 0)
                    
                    regime_changed = self.rl_agent.update_market_regime(ema_short, ema_long, atr, atr_change)
                    if regime_changed:
                        self.logger.info(f"Market regime changed to {self.rl_agent.current_regime}")
                except Exception as e:
                    self.logger.error(f"Error updating market regime: {e}")
            
            # Calculate confidence
            confidence = self.calculate_confidence(market_data, strategy)
            
            # Apply reinforcement learning adjustments if enabled
            if self.reinforcement_learning and self.rl_agent:
                try:
                    recommendations = self.rl_agent.get_strategy_recommendations()
                    strategy_rec = recommendations.get(strategy, {})
                    
                    if strategy_rec:
                        action = strategy_rec.get("action", "neutral")
                        weight = strategy_rec.get("weight", 1.0)
                        
                        if action == "increase":
                            confidence = min(100, confidence * weight)
                            self.logger.info(f"RL boosted confidence for {strategy} to {confidence}%")
                        elif action == "decrease":
                            confidence = max(0, confidence / weight)
                            self.logger.info(f"RL reduced confidence for {strategy} to {confidence}%")
                        elif action == "pause":
                            confidence = 0
                            self.logger.info(f"RL paused {strategy} strategy")
                except Exception as e:
                    self.logger.error(f"Error applying RL adjustments: {e}")
            
            # Determine action based on confidence
            if confidence >= 70:
                action = "buy" if trade_type == "entry" else "exit"
            elif confidence <= 30:
                action = "sell" if trade_type == "entry" else "exit"
            else:
                action = "hold"
            
            # Build reasoning
            reasoning = f"Decision based on {strategy} strategy with {confidence}% confidence."
            
            if self.regime_awareness and self.rl_agent:
                reasoning += f" Current market regime: {self.rl_agent.current_regime}."
            
            # Record trade result for reinforcement learning if it's an exit
            if trade_type == "exit" and self.reinforcement_learning and self.rl_agent:
                try:
                    profit = market_data.get("profit", 0)
                    self.rl_agent.record_trade_result(strategy, profit)
                    self.logger.info(f"Recorded {strategy} trade result: {profit}")
                except Exception as e:
                    self.logger.error(f"Error recording trade result: {e}")
            
            # Build final decision
            decision = {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.regime_awareness and self.rl_agent:
                decision["market_regime"] = self.rl_agent.current_regime
        
        # Standard mode (fallback)
        else:
            # Calculate confidence
            confidence = self.calculate_confidence(market_data, strategy)
            
            # Determine action based on confidence
            if confidence >= 70:
                action = "buy" if trade_type == "entry" else "exit"
            elif confidence <= 30:
                action = "sell" if trade_type == "entry" else "exit"
            else:
                action = "hold"
            
            # Build reasoning
            reasoning = f"Decision based on {strategy} strategy with {confidence}% confidence."
            
            # Build final decision
            decision = {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
        
        return decision
    
    def calculate_confidence(self, market_data: Dict[str, Any], strategy: str) -> float:
        """Calculate confidence score for a trading decision."""
        # Basic confidence calculation (placeholder)
        base_confidence = 50  # Neutral starting point
        
        # Adjust based on market condition if provided
        market_condition = market_data.get("market_condition", "")
        if "bullish" in market_condition.lower():
            base_confidence += 20
        elif "bearish" in market_condition.lower():
            base_confidence -= 20
        
        # Adjust based on market regime if available
        if self.regime_awareness and self.rl_agent:
            if self.rl_agent.current_regime == MarketRegime.BULLISH:
                if strategy in ["breakout", "momentum"]:
                    base_confidence += 15
                elif strategy in ["mean_reversion"]:
                    base_confidence -= 10
            elif self.rl_agent.current_regime == MarketRegime.BEARISH:
                if strategy in ["pullback", "mean_reversion"]:
                    base_confidence += 15
                elif strategy in ["breakout", "momentum"]:
                    base_confidence -= 10
            elif self.rl_agent.current_regime == MarketRegime.SIDEWAYS:
                if strategy in ["scalping", "range_trading"]:
                    base_confidence += 15
                else:
                    base_confidence -= 5
        
        # Ensure confidence is within bounds
        return max(0, min(100, base_confidence))
    
    def predict_market_intent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict short-term market intent using microstructure features
        
        Args:
            context (Dict[str, Any]): Trading context with market data
            
        Returns:
            Dict[str, Any]: Predicted market intent with confidence
        """
        # Default intent prediction
        intent = {
            "intent_type": "Unknown",
            "confidence": 0,
            "signals": []
        }
        
        try:
            if not self.intent_predictor or not self.intent_predictor["enabled"]:
                return intent
            
            # Extract market data
            market_data = context.get("market_data", {})
            
            # Check for required microstructure signals
            if not market_data or not all(k in market_data for k in ["orderbook", "recent_trades"]):
                return intent
            
            # Analyze order book for imbalances
            orderbook = market_data["orderbook"]
            recent_trades = market_data["recent_trades"]
            
            # Simple implementation - in a real system this would use ML models
            # to analyze microstructure patterns
            
            # Check for large orders (potential hidden orders)
            large_bids = [order for order in orderbook["bids"] if order["size"] > 10 * orderbook["avg_size"]]
            large_asks = [order for order in orderbook["asks"] if order["size"] > 10 * orderbook["avg_size"]]
            
            # Check for rapid bid/ask flips
            bid_ask_flips = market_data.get("bid_ask_flips", 0)
            
            # Check for VWAP divergence
            vwap = market_data.get("vwap", 0)
            current_price = market_data.get("price", 0)
            vwap_divergence = abs(current_price - vwap) / vwap if vwap > 0 else 0
            
            # Determine intent based on signals
            signals = []
            
            # Institutional absorption
            if len(large_bids) > 3 and vwap_divergence < 0.001:
                signals.append(("Institutional Absorption", 0.8))
            
            # Spoofing / Fake Walls
            if bid_ask_flips > 5 and (len(large_bids) > 0 or len(large_asks) > 0):
                signals.append(("Spoofing / Fake Walls", 0.7))
            
            # Genuine Momentum
            if vwap_divergence > 0.002 and len(recent_trades) > 20:
                signals.append(("Genuine Momentum", 0.75))
            
            # Exhaustion or Trap
            if vwap_divergence > 0.005 and bid_ask_flips < 2:
                signals.append(("Exhaustion or Trap", 0.65))
            
            # Select the highest confidence signal
            if signals:
                signals.sort(key=lambda x: x[1], reverse=True)
                intent_type, confidence = signals[0]
                intent = {
                    "intent_type": intent_type,
                    "confidence": int(confidence * 100),
                    "signals": signals
                }
                
                # Log the intent prediction
                self.intent_predictor["logger"].info(
                    f"Predicted market intent: {intent_type} with {intent['confidence']}% confidence"
                )
                
                # Update intent signals file
                self.update_intent_signals(intent)
            
            return intent
            
        except Exception as e:
            self.logger.error(f"Error predicting market intent: {e}")
            return intent
    
    def determine_liquidity_routing(self, context: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Determine optimal liquidity routing based on market conditions
        
        Args:
            context (Dict[str, Any]): Trading context with market data
            action (str): Trading action (buy, sell, hold, exit)
            
        Returns:
            Dict[str, Any]: Routing decision with platform and reason
        """
        # Default routing to Bulenox
        routing = {
            "platform": "Bulenox",
            "reason": "Default routing"
        }
        
        try:
            if not self.liquidity_router or not self.liquidity_router["enabled"] or action == "hold":
                return routing
            
            # Extract market data
            market_data = context.get("market_data", {})
            
            # Check for required liquidity signals
            if not market_data:
                return routing
            
            # Get platform metrics
            platforms = self.liquidity_router["platforms"]
            platform_metrics = {}
            
            for platform in platforms:
                # In a real system, these would be fetched from APIs or market data feeds
                # Here we're simulating with random values for demonstration
                spread = market_data.get(f"{platform.lower()}_spread", 1.5)
                volume = market_data.get(f"{platform.lower()}_volume", 100)
                latency = market_data.get(f"{platform.lower()}_latency", 80)
                
                platform_metrics[platform] = {
                    "spread": spread,
                    "volume": volume,
                    "latency": latency
                }
            
            # Calculate median spread
            spreads = [metrics["spread"] for metrics in platform_metrics.values()]
            median_spread = sorted(spreads)[len(spreads) // 2]
            
            # Check for routing conditions
            for platform, metrics in platform_metrics.items():
                # Check for spread widening
                if metrics["spread"] > 2 * median_spread:
                    continue
                
                # Check for low volume
                volumes = [m["volume"] for m in platform_metrics.values()]
                volumes.sort()
                percentile_25 = volumes[len(volumes) // 4]
                if metrics["volume"] < percentile_25:
                    continue
                
                # Check for high latency
                if metrics["latency"] > self.liquidity_router["latency_limit_ms"]:
                    continue
                
                # This platform passes all checks
                routing = {
                    "platform": platform,
                    "reason": "Optimal liquidity conditions"
                }
                
                # Log the routing decision
                self.liquidity_router["logger"].info(
                    f"Routing trade to {platform}: spread={metrics['spread']}, volume={metrics['volume']}, latency={metrics['latency']}ms"
                )
                
                # Update routing metrics
                self.update_routing_metrics(platform, metrics)
                
                break
            
            return routing
            
        except Exception as e:
            self.logger.error(f"Error determining liquidity routing: {e}")
            return routing
    
    def adjust_execution(self, decision: Dict[str, Any], intent: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust execution tactics based on market intent and liquidity routing
        
        Args:
            decision (Dict[str, Any]): Original trading decision
            intent (Dict[str, Any]): Predicted market intent
            routing (Dict[str, Any]): Liquidity routing decision
            
        Returns:
            Dict[str, Any]: Adjusted trading decision
        """
        # Start with the original decision
        adjusted_decision = decision.copy()
        
        try:
            # Adjust based on market intent
            intent_type = intent["intent_type"]
            intent_confidence = intent["confidence"]
            
            # Only adjust if intent confidence is high enough
            if intent_confidence >= 70:
                if intent_type == "Spoofing / Fake Walls":
                    # Reduce confidence in spoof zones
                    adjusted_decision["confidence"] = max(30, adjusted_decision["confidence"] - 20)
                    adjusted_decision["reasoning"] = f"Reduced confidence due to detected spoofing. {adjusted_decision['reason']}"
                
                elif intent_type == "Institutional Absorption":
                    # Accelerate fills during absorption
                    adjusted_decision["confidence"] = min(95, adjusted_decision["confidence"] + 10)
                    adjusted_decision["reasoning"] = f"Increased confidence due to institutional absorption. {adjusted_decision['reason']}"
                
                elif intent_type == "Exhaustion or Trap":
                    # Cancel trades in exhaustion signals
                    if adjusted_decision["action"] != "hold":
                        adjusted_decision["action"] = "hold"
                        adjusted_decision["confidence"] = 80
                        adjusted_decision["reasoning"] = f"Changed to hold due to exhaustion signal. Original: {adjusted_decision['reason']}"
            
            # Log the adjustment
            self.logger.info(
                f"Adjusted execution based on {intent_type} intent: {adjusted_decision['action']} with {adjusted_decision['confidence']}% confidence"
            )
            
            return adjusted_decision
            
        except Exception as e:
            self.logger.error(f"Error adjusting execution: {e}")
            return decision
    
    def update_intent_signals(self, intent: Dict[str, Any]) -> None:
        """Update intent signals file with new prediction
        
        Args:
            intent (Dict[str, Any]): Predicted market intent
        """
        try:
            if not self.intent_predictor or not "signals_file" in self.intent_predictor:
                return
            
            signals_file = self.intent_predictor["signals_file"]
            
            # Load current signals data
            if os.path.exists(signals_file):
                with open(signals_file, "r") as f:
                    signals_data = json.load(f)
            else:
                signals_data = {
                    "total_signals": 0,
                    "classified_signals": 0,
                    "average_confidence": 0,
                    "signals_by_type": {
                        "Institutional Absorption": 0,
                        "Spoofing / Fake Walls": 0,
                        "Genuine Momentum": 0,
                        "Exhaustion or Trap": 0
                    }
                }
            
            # Update signals data
            signals_data["total_signals"] += 1
            
            if intent["confidence"] >= self.intent_predictor["min_confidence"]:
                signals_data["classified_signals"] += 1
                signals_data["signals_by_type"][intent["intent_type"]] += 1
            
            # Update average confidence
            old_avg = signals_data["average_confidence"]
            old_count = signals_data["total_signals"] - 1
            new_confidence = intent["confidence"]
            
            if old_count > 0:
                signals_data["average_confidence"] = (old_avg * old_count + new_confidence) / signals_data["total_signals"]
            else:
                signals_data["average_confidence"] = new_confidence
            
            # Save updated signals data
            with open(signals_file, "w") as f:
                json.dump(signals_data, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error updating intent signals: {e}")
    
    def update_routing_metrics(self, platform: str, metrics: Dict[str, Any]) -> None:
        """Update routing metrics file with new routing decision
        
        Args:
            platform (str): Selected platform for routing
            metrics (Dict[str, Any]): Platform metrics
        """
        try:
            if not self.liquidity_router or not "metrics_file" in self.liquidity_router:
                return
            
            metrics_file = self.liquidity_router["metrics_file"]
            
            # Load current metrics data
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    metrics_data = json.load(f)
            else:
                metrics_data = {
                    "total_reroutes": 0,
                    "successful_reroutes": 0,
                    "failed_reroutes": 0,
                    "average_latency_ms": 0,
                    "slippage_reduction": 0,
                    "platforms": {
                        "Exness": {"trades": 0, "avg_spread": 0, "avg_latency": 0},
                        "Bulenox": {"trades": 0, "avg_spread": 0, "avg_latency": 0},
                        "Binance": {"trades": 0, "avg_spread": 0, "avg_latency": 0}
                    }
                }
            
            # Update metrics data
            metrics_data["total_reroutes"] += 1
            metrics_data["successful_reroutes"] += 1
            
            # Update platform-specific metrics
            platform_data = metrics_data["platforms"][platform]
            platform_data["trades"] += 1
            
            # Update average spread
            old_avg_spread = platform_data["avg_spread"]
            old_count = platform_data["trades"] - 1
            new_spread = metrics["spread"]
            
            if old_count > 0:
                platform_data["avg_spread"] = (old_avg_spread * old_count + new_spread) / platform_data["trades"]
            else:
                platform_data["avg_spread"] = new_spread
            
            # Update average latency
            old_avg_latency = platform_data["avg_latency"]
            new_latency = metrics["latency"]
            
            if old_count > 0:
                platform_data["avg_latency"] = (old_avg_latency * old_count + new_latency) / platform_data["trades"]
            else:
                platform_data["avg_latency"] = new_latency
            
            # Update overall average latency
            total_trades = sum(p["trades"] for p in metrics_data["platforms"].values())
            metrics_data["average_latency_ms"] = sum(p["avg_latency"] * p["trades"] for p in metrics_data["platforms"].values()) / total_trades if total_trades > 0 else 0
            
            # Save updated metrics data
            with open(metrics_file, "w") as f:
                json.dump(metrics_data, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error updating routing metrics: {e}")
    
    def load_decider_config(self):
        """Load the decider configuration from file or use defaults."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'sentinel_config.json')
        
        # Default configuration
        default_config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.2,
                "max_tokens": 500
            },
            "confidence_thresholds": {
                "high": 80,
                "medium": 60,
                "low": 40
            },
            "weighting": {
                "technical": 0.6,
                "fundamental": 0.3,
                "sentiment": 0.1
            },
            "history_lookback": {
                "trades": 50,
                "days": 30
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded configuration from {config_path}")
                return config
            else:
                self.logger.warning(f"Configuration file not found at {config_path}, using defaults")
                return default_config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}, using defaults")
            return default_config
    
    def load_phase_prompt(self, phase):
        """Load a markdown prompt file for a specific phase."""
        prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trae_prompts', f'phase-{phase}.md')
        
        try:
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r') as f:
                    content = f.read()
                
                # Parse the markdown content
                self.prompt_data = self.parse_markdown_prompt(content)
                
                # Apply prompt data to configuration
                self.apply_prompt_to_config(self.prompt_data)
                
                # Record the prompt load
                self.record_prompt_load(phase, prompt_path)
                
                return self.prompt_data
            else:
                self.logger.error(f"Prompt file not found at {prompt_path}")
                raise FileNotFoundError(f"Prompt file not found at {prompt_path}")
        except Exception as e:
            self.logger.error(f"Error loading phase prompt: {e}")
            raise
    
    def parse_markdown_prompt(self, content):
        """Parse structured data from markdown content."""
        data = {
            "goals": [],
            "system_instructions": {},
            "risk_policies": [],
            "news_sensitivity": {},
            "success_metrics": []
        }
        
        # Extract goals
        goals_match = re.search(r'## Goals\s+([\s\S]*?)(?=##|$)', content)
        if goals_match:
            goals_text = goals_match.group(1).strip()
            data["goals"] = [g.strip().strip('-').strip() for g in goals_text.split('\n') if g.strip() and g.strip().startswith('-')]
        
        # Extract system instructions
        sys_instr_match = re.search(r'## System Instructions\s+([\s\S]*?)(?=##|$)', content)
        if sys_instr_match:
            sys_instr_text = sys_instr_match.group(1).strip()
            
            # Look for parameters section
            params_match = re.search(r'parameters:\s*([\s\S]*?)(?=\n\n|$)', sys_instr_text)
            if params_match:
                params_text = params_match.group(1).strip()
                for line in params_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert to appropriate type
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r'^\d+\.\d+$', value):
                            value = float(value)
                            
                        data["system_instructions"][key] = value
        
        # Extract success metrics
        metrics_match = re.search(r'## Success Metrics\s+([\s\S]*?)(?=##|$)', content)
        if metrics_match:
            metrics_text = metrics_match.group(1).strip()
            data["success_metrics"] = [m.strip().strip('-').strip() for m in metrics_text.split('\n') if m.strip() and m.strip().startswith('-')]
        
        return data
    
    def apply_prompt_to_config(self, prompt_data):
        """Apply parsed prompt data to the decider's configuration."""
        if "system_instructions" in prompt_data:
            system_instructions = prompt_data["system_instructions"]
            
            # Enable/disable features based on parameters
            if "regime_awareness" in system_instructions:
                self.regime_awareness = system_instructions["regime_awareness"]
                self.logger.info(f"Set regime_awareness to {self.regime_awareness}")
                
            if "reinforcement_learning" in system_instructions:
                self.reinforcement_learning = system_instructions["reinforcement_learning"]
                self.logger.info(f"Set reinforcement_learning to {self.reinforcement_learning}")
                
            # Check for multi-agent mode
            if "mode" in system_instructions:
                mode = system_instructions["mode"]
                if mode == "multi_agent":
                    self.multi_agent_mode = True
                    self.logger.info("Multi-agent mode enabled from phase prompt")
                    
                    # Store parameters for voting system initialization
                    self.prompt_data = prompt_data
    
    def record_prompt_load(self, phase, prompt_path):
        """Record the prompt load in a history file."""
        history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        history_file = os.path.join(history_dir, 'prompts_history.json')
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # Load existing history or create new
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading prompt history: {e}")
        
        # Add new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "prompt_path": prompt_path,
            "goals": self.prompt_data.get("goals", []),
            "system_instructions": self.prompt_data.get("system_instructions", {})
        }
        
        history.append(entry)
        
        # Save updated history
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
            self.logger.info(f"Recorded prompt load in {history_file}")
        except Exception as e:
            self.logger.error(f"Error saving prompt history: {e}")
    
    def initialize_reinforcement_agent(self):
        """Initialize the reinforcement learning agent."""
        try:
            self.rl_agent = ReinforcementAgent()
            self.logger.info("Reinforcement learning agent initialized")
            
            # Apply configuration from prompt if available
            if self.prompt_data and "system_instructions" in self.prompt_data:
                system_instructions = self.prompt_data["system_instructions"]
                
                # Set reward threshold if specified
                if "reward_threshold" in system_instructions:
                    reward_str = system_instructions["reward_threshold"]
                    if isinstance(reward_str, str) and "+" in reward_str and "profit factor" in reward_str:
                        try:
                            reward_value = float(reward_str.split("+")[1].split(" ")[0])
                            self.rl_agent.config["reward_threshold"] = reward_value
                            self.logger.info(f"Updated reward threshold to {reward_value}")
                        except (ValueError, IndexError):
                            self.logger.warning(f"Could not parse reward threshold: {reward_str}")
                
                # Set penalty threshold if specified
                if "penalty_threshold" in system_instructions:
                    penalty_str = system_instructions["penalty_threshold"]
                    if isinstance(penalty_str, str) and "-" in penalty_str and "profit factor" in penalty_str:
                        try:
                            penalty_value = float(penalty_str.split("-")[1].split(" ")[0])
                            self.rl_agent.config["penalty_threshold"] = penalty_value
                            self.logger.info(f"Updated penalty threshold to {penalty_value}")
                        except (ValueError, IndexError):
                            self.logger.warning(f"Could not parse penalty threshold: {penalty_str}")
        except Exception as e:
            self.logger.error(f"Failed to initialize reinforcement agent: {e}")
            self.rl_agent = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sentinel_decider")

# Constants
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")
DECIDER_CONFIG_FILE = os.path.join("config", "decider_config.json")
PROMPTS_DIR = os.path.join("trae_prompts")
PROMPTS_HISTORY_FILE = os.path.join("logs", "prompts_history.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)
os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)


class SentinelDecider:
    """AI-based decision agent for trading strategies"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE, 
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 decider_config_file: str = DECIDER_CONFIG_FILE,
                 phase: int = None):
        """Initialize the sentinel decider

        Args:
            trade_history_file (str): Path to the trade history file
            strategy_stats_file (str): Path to the strategy statistics file
            decider_config_file (str): Path to the decider configuration file
            phase (int, optional): The phase number to load prompt from. Defaults to None.
        """
        self.trade_history_file = trade_history_file
        self.strategy_stats_file = strategy_stats_file
        self.decider_config_file = decider_config_file
        self.evaluator = TradePerformanceEvaluator(trade_history_file, strategy_stats_file)
        self.news_guard = NewsGuard()
        self.decider_config = self.load_decider_config()
        self.current_phase = phase
        self.prompt_data = {}
        
        # Initialize reinforcement learning agent
        self.rl_agent = None
        self.regime_awareness = False
        self.reinforcement_learning = False
        
        # Load phase prompt if specified
        if phase is not None:
            success = self.load_phase_prompt(phase)
            if success:
                logger.info(f"Initialized SentinelDecider with phase {phase}")
                
                # Check if phase prompt enables regime awareness or reinforcement learning
                if "system_instructions" in self.prompt_data:
                    instructions = self.prompt_data["system_instructions"]
                    
                    # Enable regime awareness if specified in prompt
                    if "regime_awareness" in instructions and instructions["regime_awareness"].lower() == "true":
                        self.regime_awareness = True
                        logger.info("Market regime awareness enabled from phase prompt")
                    
                    # Enable reinforcement learning if specified in prompt
                    if "reinforcement_learning" in instructions and instructions["reinforcement_learning"].lower() == "true":
                        self.reinforcement_learning = True
                        logger.info("Reinforcement learning enabled from phase prompt")
                
                # Initialize reinforcement agent if needed
                if self.regime_awareness or self.reinforcement_learning:
                    self.initialize_reinforcement_agent()
            else:
                logger.warning(f"Failed to load phase {phase}, continuing with default configuration")
        else:
            # Log the initialization
            logger.info(f"SentinelDecider initialized with no phase specified")
        
        
    def load_decider_config(self) -> Dict:
        """Load decider configuration from file

        Returns:
            Dict: Decider configuration
        """
        default_config = {
            "llm": {
                "enabled": True,
                "provider": "openai",  # openai, local, or mock
                "model": "gpt-3.5-turbo",
                "api_key": "",  # Set via environment variable OPENAI_API_KEY
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "temperature": 0.2,
                "max_tokens": 500
            },
            "confidence_thresholds": {
                "high": 80.0,
                "medium": 60.0,
                "low": 40.0
            },
            "weighting": {
                "technical": 0.3,
                "psychology": 0.6,
                "news": 0.1
            },
            "history_lookback": {
                "trades": 10,
                "days": 7
            }
        }
        
        try:
            if os.path.exists(self.decider_config_file):
                with open(self.decider_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.decider_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading decider config: {e}")
            return default_config
            
    def load_phase_prompt(self, phase: int) -> bool:
        """Load a phase prompt from markdown file
        
        Args:
            phase (int): The phase number to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        prompt_file = os.path.join(PROMPTS_DIR, f"phase-{phase}.md")
        
        if not os.path.exists(prompt_file):
            logger.error(f"Phase prompt file not found: {prompt_file}")
            return False
            
        try:
            with open(prompt_file, "r") as f:
                content = f.read()
                
            # Parse the markdown content
            self.prompt_data = self.parse_markdown_prompt(content)
            self.current_phase = phase
            
            # Log the loaded prompt
            logger.info(f"Loaded phase prompt {phase} from {prompt_file}")
            
            # Record in prompt history
            self.record_prompt_load(phase, self.prompt_data)
            
            return True
        except Exception as e:
            logger.error(f"Error loading phase prompt: {e}")
            return False
            
    def parse_markdown_prompt(self, content: str) -> Dict:
        """Parse markdown content into structured data
        
        Args:
            content (str): Markdown content to parse
            
        Returns:
            Dict: Structured data from the markdown
        """
        parsed_data = {
            "goals": [],
            "system_instructions": {},
            "risk_policies": {},
            "news_sensitivity": {},
            "success_metrics": {},
            "technical_implementation": {},
            "monitoring": {},
            "completion_criteria": []
        }
        
        # Extract section content using regex
        goals_match = re.search(r"## Goals\s+([\s\S]*?)(?=##|$)", content)
        if goals_match:
            goals_text = goals_match.group(1).strip()
            parsed_data["goals"] = [g.strip().lstrip("- ") for g in goals_text.split("\n") if g.strip() and g.strip().startswith("-")]
        
        # Extract system instructions
        sys_instr_match = re.search(r"### Sentinel Decider Activation\s+```\s*([\s\S]*?)```", content)
        if sys_instr_match:
            instr_text = sys_instr_match.group(1).strip()
            # Parse YAML-like content
            parameters = {}
            current_key = None
            
            for line in instr_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                if ":" in line and not line.endswith(":"):
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Convert to appropriate types
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        value = float(value)
                        
                    parsed_data["system_instructions"][key] = value
                    current_key = key
                elif line.endswith(":") and not ":" in line[:-1]:
                    # This is a parameter group (like 'parameters:')
                    current_key = line[:-1].strip()
                    parsed_data["system_instructions"][current_key] = {}
                elif current_key and current_key in parsed_data["system_instructions"] and isinstance(parsed_data["system_instructions"][current_key], dict) and line.startswith("  ") and ":" in line:
                    # This is a nested parameter
                    sub_key, sub_value = line.strip().split(":", 1)
                    sub_key = sub_key.strip()
                    sub_value = sub_value.strip()
                    
                    # Convert to appropriate types
                    if sub_value.lower() == "true":
                        sub_value = True
                    elif sub_value.lower() == "false":
                        sub_value = False
                    elif sub_value.isdigit():
                        sub_value = int(sub_value)
                    elif sub_value.replace(".", "", 1).isdigit():
                        sub_value = float(sub_value)
                        
                    parsed_data["system_instructions"][current_key][sub_key] = sub_value
        
        # Extract risk policies
        risk_match = re.search(r"### Risk Policies\s+([\s\S]*?)(?=###|$)", content)
        if risk_match:
            risk_text = risk_match.group(1).strip()
            risk_items = [r.strip().lstrip("- ") for r in risk_text.split("\n") if r.strip() and r.strip().startswith("-")]
            for item in risk_items:
                if ":" in item:
                    key, value = item.split(":", 1)
                    parsed_data["risk_policies"][key.strip()] = value.strip()
        
        # Extract news sensitivity thresholds
        news_match = re.search(r"### News Sensitivity Thresholds\s+([\s\S]*?)(?=##|$)", content)
        if news_match:
            news_text = news_match.group(1).strip()
            news_items = [n.strip().lstrip("- ") for n in news_text.split("\n") if n.strip() and n.strip().startswith("-")]
            for item in news_items:
                if ":" in item:
                    key, value = item.split(":", 1)
                    parsed_data["news_sensitivity"][key.strip()] = value.strip()
        
        # Extract success metrics
        metrics_match = re.search(r"## Success Metrics\s+([\s\S]*?)(?=##|$)", content)
        if metrics_match:
            metrics_text = metrics_match.group(1).strip()
            metrics_items = [m.strip().lstrip("- ") for m in metrics_text.split("\n") if m.strip() and m.strip().startswith("-")]
            for item in metrics_items:
                if ":" in item:
                    key, value = item.split(":", 1)
                    parsed_data["success_metrics"][key.strip()] = value.strip()
        
        # Apply parsed data to configuration if needed
        self.apply_prompt_to_config(parsed_data)
        
        return parsed_data
        
    def apply_prompt_to_config(self, prompt_data: Dict) -> None:
        """Apply parsed prompt data to the decider configuration
        
        Args:
            prompt_data (Dict): Parsed prompt data
        """
        # Update confidence thresholds if specified in the prompt
        if "system_instructions" in prompt_data and "confidence_threshold" in prompt_data["system_instructions"]:
            try:
                threshold = float(prompt_data["system_instructions"]["confidence_threshold"])
                self.decider_config["confidence_thresholds"]["medium"] = threshold
                # Adjust high and low thresholds proportionally
                self.decider_config["confidence_thresholds"]["high"] = min(threshold + 20, 100)
                self.decider_config["confidence_thresholds"]["low"] = max(threshold - 20, 0)
                logger.info(f"Updated confidence thresholds based on prompt: {self.decider_config['confidence_thresholds']}")
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not update confidence threshold: {e}")
        
        # Save updated config
        try:
            with open(self.decider_config_file, "w") as f:
                json.dump(self.decider_config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving updated config: {e}")
    
    def record_prompt_load(self, phase: int, prompt_data: Dict) -> None:
        """Record prompt load in history file
        
        Args:
            phase (int): The phase number
            prompt_data (Dict): The parsed prompt data
        """
        history = []
        
        # Load existing history if available
        if os.path.exists(PROMPTS_HISTORY_FILE):
            try:
                with open(PROMPTS_HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading prompts history: {e}")
        
        # Add new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "prompt_file": f"phase-{phase}.md",
            "goals": prompt_data.get("goals", []),
            "system_instructions": prompt_data.get("system_instructions", {})
        }
        
        history.append(entry)
        
        # Save updated history
        try:
            with open(PROMPTS_HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving prompts history: {e}")
            
    def initialize_reinforcement_agent(self) -> None:
        """Initialize the reinforcement learning agent for market regime awareness"""
        try:
            self.rl_agent = ReinforcementAgent()
            logger.info("Reinforcement learning agent initialized")
            
            # Apply any configuration from prompt data
            if self.prompt_data and "system_instructions" in self.prompt_data:
                instructions = self.prompt_data["system_instructions"]
                
                # Update reward threshold if specified
                if "reward_threshold" in instructions:
                    try:
                        # Parse value like "+1.2 profit factor" to extract 1.2
                        reward_str = instructions["reward_threshold"]
                        reward_value = float(reward_str.replace("profit factor", "").strip("+ "))
                        self.rl_agent.config["reward_threshold"] = reward_value
                        logger.info(f"Updated reward threshold to {reward_value}")
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Could not parse reward threshold: {e}")
                
                # Update penalty threshold if specified
                if "penalty_threshold" in instructions:
                    try:
                        # Parse value like "-0.8 profit factor" to extract 0.8
                        penalty_str = instructions["penalty_threshold"]
                        penalty_value = float(penalty_str.replace("profit factor", "").strip("- "))
                        self.rl_agent.config["penalty_threshold"] = penalty_value
                        logger.info(f"Updated penalty threshold to {penalty_value}")
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Could not parse penalty threshold: {e}")
        except Exception as e:
            logger.error(f"Error initializing reinforcement agent: {e}")
            self.rl_agent = None
            self.regime_awareness = False
            self.reinforcement_learning = False
        except Exception as e:
            logger.error(f"Error loading decider config: {e}")
            return default_config
            
    def save_decider_config(self) -> bool:
        """Save decider configuration to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.decider_config_file, "w") as f:
                json.dump(self.decider_config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving decider config: {e}")
            return False
            
    def get_recent_trades(self, strategy_name: str, limit: int = 10) -> List[Dict]:
        """Get recent trades for a strategy

        Args:
            strategy_name (str): Name of the strategy
            limit (int): Maximum number of trades to return

        Returns:
            List[Dict]: List of recent trades
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, "r") as f:
                    trades = json.load(f)
            else:
                return []
                
            # Filter trades for the strategy
            strategy_trades = [trade for trade in trades if trade.get("strategy") == strategy_name]
            
            # Sort by timestamp (newest first)
            strategy_trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit the number of trades
            return strategy_trades[:limit]
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
            
    def get_trade_context(self, strategy_name: str, symbol: str, 
                         market_condition: str) -> Dict:
        """Get trading context for decision making

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            market_condition (str): Current market condition

        Returns:
            Dict: Trading context
        """
        # Get strategy performance
        performance = self.evaluator.get_strategy_performance(strategy_name)
        
        # Get recent trades
        recent_trades = self.get_recent_trades(
            strategy_name, 
            self.decider_config["history_lookback"]["trades"]
        )
        
        # Check if symbol is affected by news
        news_affected, news_event = self.news_guard.is_affected_by_news(symbol)
        
        # Compile context
        context = {
            "strategy": {
                "name": strategy_name,
                "win_rate": performance.get("win_rate", 0.0),
                "profit_factor": performance.get("profit_factor", 0.0),
                "total_trades": performance.get("total_trades", 0),
                "consecutive_wins": performance.get("consecutive_wins", 0),
                "consecutive_losses": performance.get("consecutive_losses", 0)
            },
            "symbol": symbol,
            "market_condition": market_condition,
            "news": {
                "affected": news_affected,
                "event": news_event if news_affected else None
            },
            "recent_trades": [
                {
                    "symbol": trade.get("symbol", ""),
                    "profit_loss": trade.get("profit_loss", 0.0),
                    "win": trade.get("profit_loss", 0.0) > 0,
                    "market_condition": trade.get("market_condition", ""),
                    "news_avoided": trade.get("news_avoided", False)
                }
                for trade in recent_trades
            ]
        }
        
        return context
        
    def generate_llm_prompt(self, context: Dict) -> str:
        """Generate prompt for LLM based on trading context

        Args:
            context (Dict): Trading context

        Returns:
            str: Generated prompt
        """
        # Extract context information
        strategy = context["strategy"]
        symbol = context["symbol"]
        market_condition = context["market_condition"]
        news = context["news"]
        recent_trades = context["recent_trades"]
        
        # Format recent trades
        recent_trades_text = ""
        for i, trade in enumerate(recent_trades):
            result = "WIN" if trade["win"] else "LOSS"
            pnl = trade["profit_loss"]
            symbol = trade["symbol"]
            condition = trade["market_condition"]
            news_avoided = "(News Avoided)" if trade["news_avoided"] else ""
            
            recent_trades_text += f"Trade {i+1}: {result} ${pnl:.2f} on {symbol} in {condition} market {news_avoided}\n"
        
        # Generate prompt
        prompt = f"""
You are Sentinel, an AI trading assistant. Analyze this trading opportunity and provide a confidence score (0-100) and recommendation.

Strategy: {strategy['name']}
Performance: {strategy['win_rate']:.1f}% win rate, {strategy['profit_factor']:.2f} profit factor, {strategy['total_trades']} total trades
Current streak: {strategy['consecutive_wins']} consecutive wins, {strategy['consecutive_losses']} consecutive losses

Symbol: {symbol}
Market condition: {market_condition}
News impact: {'High-impact news event: ' + news['event'] if news['affected'] else 'No significant news'}

Recent trade history:
{recent_trades_text}

Based on this information, provide:
1. A confidence score (0-100) for taking this trade
2. A brief explanation of your reasoning
3. A recommendation (Take Trade, Reduce Size, Skip Trade)
4. Any adjustments to consider for this strategy

Format your response as JSON:
{{"confidence_score": 75, "explanation": "Your reasoning here", "recommendation": "Take Trade", "adjustments": "Any suggested adjustments"}}
"""
        
        return prompt
        
    def call_llm_api(self, prompt: str) -> Dict:
        """Call LLM API with the generated prompt

        Args:
            prompt (str): Generated prompt

        Returns:
            Dict: LLM response
        """
        provider = self.decider_config["llm"]["provider"]
        
        # Mock provider for testing
        if provider == "mock":
            import random
            confidence = random.randint(40, 90)
            recommendations = ["Take Trade", "Reduce Size", "Skip Trade"]
            recommendation = recommendations[random.randint(0, 2)]
            
            return {
                "confidence_score": confidence,
                "explanation": f"Mock LLM response with {confidence}% confidence",
                "recommendation": recommendation,
                "adjustments": "No adjustments needed"
            }
            
        # OpenAI API
        if provider == "openai":
            try:
                # Get API key from environment or config
                api_key = os.environ.get("OPENAI_API_KEY", self.decider_config["llm"]["api_key"])
                
                if not api_key:
                    logger.error("OpenAI API key not found")
                    return {}
                    
                # Prepare request
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                data = {
                    "model": self.decider_config["llm"]["model"],
                    "messages": [
                        {"role": "system", "content": "You are Sentinel, an AI trading assistant that provides concise analysis and recommendations in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.decider_config["llm"]["temperature"],
                    "max_tokens": self.decider_config["llm"]["max_tokens"],
                    "response_format": {"type": "json_object"}
                }
                
                # Make API call
                response = requests.post(
                    self.decider_config["llm"]["api_endpoint"],
                    headers=headers,
                    json=data
                )
                
                # Parse response
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse JSON content
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Error parsing LLM response: {content}")
                        return {}
                else:
                    logger.error(f"Error calling OpenAI API: {response.status_code} {response.text}")
                    return {}
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}")
                return {}
                
        # Local LLM (placeholder for integration with local models)
        if provider == "local":
            logger.warning("Local LLM provider not implemented yet")
            return {}
            
        return {}
        
    def calculate_confidence_score(self, context: Dict) -> Tuple[float, str, str]:
        """Calculate confidence score based on trading context

        Args:
            context (Dict): Trading context

        Returns:
            Tuple[float, str, str]: (confidence_score, explanation, recommendation)
        """
        # Check if LLM is enabled
        if self.decider_config["llm"]["enabled"]:
            # Generate prompt
            prompt = self.generate_llm_prompt(context)
            
            # Call LLM API
            llm_response = self.call_llm_api(prompt)
            
            if llm_response:
                confidence_score = llm_response.get("confidence_score", 0.0)
                explanation = llm_response.get("explanation", "")
                recommendation = llm_response.get("recommendation", "Skip Trade")
                
                # Apply market regime awareness if enabled
                if self.regime_awareness and self.rl_agent:
                    current_regime = self.rl_agent.current_regime
                    
                    # Adjust confidence based on market regime
                    if current_regime == MarketRegime.BULLISH and "bullish" in context["market_condition"].lower():
                        confidence_score = min(100, confidence_score * 1.2)  # Boost confidence in bullish regime
                        explanation = f"[Regime: {current_regime}] " + explanation
                    elif current_regime == MarketRegime.BEARISH and "bearish" in context["market_condition"].lower():
                        confidence_score = min(100, confidence_score * 1.2)  # Boost confidence in bearish regime
                        explanation = f"[Regime: {current_regime}] " + explanation
                    elif current_regime == MarketRegime.SIDEWAYS and "ranging" in context["market_condition"].lower():
                        confidence_score = min(100, confidence_score * 1.1)  # Slight boost in sideways regime
                        explanation = f"[Regime: {current_regime}] " + explanation
                    else:
                        confidence_score = max(0, confidence_score * 0.9)  # Reduce confidence when regime doesn't match
                        explanation = f"[Regime Mismatch: {current_regime}] " + explanation
                
                return confidence_score, explanation, recommendation
        
        # Fallback to rule-based confidence calculation
        return self.calculate_rule_based_confidence(context)
        
    def calculate_rule_based_confidence(self, context: Dict) -> Tuple[float, str, str]:
        """Calculate confidence score based on rules

        Args:
            context (Dict): Trading context

        Returns:
            Tuple[float, str, str]: (confidence_score, explanation, recommendation)
        """
        
    def _check_account_restrictions(self, account: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the account has any restrictions that would prevent trading.
        
        Args:
            account (Dict[str, Any]): Account information
            signal (Dict[str, Any]): Trading signal
            
        Returns:
            Dict[str, Any]: Validation result with valid flag and reason
        """
        try:
            # Default result
            result = {"valid": True, "reason": ""}
            
            # Check if account is in cooldown after hitting daily loss limit
            if "daily_loss_limit" in account and "current_daily_loss" in account:
                if account["current_daily_loss"] >= account["daily_loss_limit"]:
                    result = {"valid": False, "reason": "Daily loss limit reached"}
                    return result
            
            # Check time restrictions if configured
            if "trading_hours" in account:
                current_time = datetime.now().time()
                start_time = datetime.strptime(account["trading_hours"]["start"], "%H:%M").time()
                end_time = datetime.strptime(account["trading_hours"]["end"], "%H:%M").time()
                
                if not (start_time <= current_time <= end_time):
                    result = {"valid": False, "reason": "Outside allowed trading hours"}
                    return result
            
            # Check max open positions if configured
            if "max_open_positions" in account and "open_positions" in account:
                if len(account["open_positions"]) >= account["max_open_positions"]:
                    result = {"valid": False, "reason": "Maximum open positions reached"}
                    return result
            
            # Check if symbol is allowed for this account
            if "allowed_symbols" in account and signal.get("symbol") not in account["allowed_symbols"]:
                result = {"valid": False, "reason": f"Symbol {signal.get('symbol')} not allowed for this account"}
                return result
            
            # Check if strategy is allowed for this account
            if "allowed_strategies" in account and signal.get("strategy") not in account["allowed_strategies"]:
                result = {"valid": False, "reason": f"Strategy {signal.get('strategy')} not allowed for this account"}
                return result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking account restrictions: {e}")
            return {"valid": False, "reason": f"Error checking restrictions: {str(e)}"}
    
    def _calculate_position_size(self, account: Dict[str, Any], signal: Dict[str, Any]) -> float:
        """Calculate position size based on account settings and signal.
        
        Args:
            account (Dict[str, Any]): Account information
            signal (Dict[str, Any]): Trading signal
            
        Returns:
            float: Position size in lots
        """
        try:
            # Default to account's default lot size
            position_size = account.get("default_lot_size", 0.01)
            
            # If risk percentage is specified in account settings, calculate based on that
            if "risk_percentage" in account and "balance" in account and "sl_pips" in signal and signal["sl_pips"] > 0:
                # Calculate position size based on risk percentage
                risk_amount = account["balance"] * (account["risk_percentage"] / 100)
                pip_value = account.get("pip_value", 10)  # Default $10 per pip for 1 lot
                
                # Calculate position size: risk_amount / (sl_pips * pip_value_per_lot)
                calculated_size = risk_amount / (signal["sl_pips"] * pip_value)
                
                # Apply position size limits
                min_lot = account.get("min_lot_size", 0.01)
                max_lot = account.get("max_lot_size", 10.0)
                
                position_size = max(min_lot, min(calculated_size, max_lot))
            
            # Round to 2 decimal places (standard for most brokers)
            position_size = round(position_size, 2)
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return account.get("default_lot_size", 0.01)  # Return default on error
    
    def _record_trade_execution(self, signal: Dict[str, Any], decision: Dict[str, Any]) -> None:
        """Record trade execution in logs.
        
        Args:
            signal (Dict[str, Any]): Trading signal
            decision (Dict[str, Any]): Trade decision with execution results
        """
        try:
            # Create trade record
            trade_record = {
                "signal": signal,
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            }
            
            # Load existing trades
            trades_file = os.path.join(self.data_dir, "trades.json")
            trades = []
            
            if os.path.exists(trades_file):
                try:
                    with open(trades_file, "r") as f:
                        trades = json.load(f)
                except json.JSONDecodeError:
                    trades = []
            
            # Add new trade record
            trades.append(trade_record)
            
            # Save updated trades
            with open(trades_file, "w") as f:
                json.dump(trades, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error recording trade execution: {e}")
    
    def _record_signal_for_learning(self, signal: Dict[str, Any]) -> None:
        """Record signal for passive learning.
        
        Args:
            signal (Dict[str, Any]): Trading signal
        """
        try:
            # Add timestamp to signal
            signal_record = signal.copy()
            signal_record["recorded_at"] = datetime.now().isoformat()
            signal_record["outcome"] = "pending"  # Will be updated later when outcome is known
            
            # Load existing signals
            signals_file = os.path.join(self.data_dir, "signals.json")
            signals = []
            
            if os.path.exists(signals_file):
                try:
                    with open(signals_file, "r") as f:
                        signals = json.load(f)
                except json.JSONDecodeError:
                    signals = []
            
            # Add new signal record
            signals.append(signal_record)
            
            # Save updated signals
            with open(signals_file, "w") as f:
                json.dump(signals, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error recording signal for learning: {e}")
    
    def _record_governance_violation(self, strategy: str, validation_result: Dict[str, Any]) -> None:
        """Record governance violation.
        
        Args:
            strategy (str): Strategy name
            validation_result (Dict[str, Any]): Validation result with reason
        """
        try:
            # Create violation record
            violation_record = {
                "strategy": strategy,
                "reason": validation_result.get("reason", "Unknown reason"),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add details if available
            if "details" in validation_result:
                violation_record["details"] = validation_result["details"]
            
            # Load existing violations
            violations_file = os.path.join(self.logs_dir, "governance_violations.json")
            violations = []
            
            if os.path.exists(violations_file):
                try:
                    with open(violations_file, "r") as f:
                        violations = json.load(f)
                except json.JSONDecodeError:
                    violations = []
            
            # Add new violation record
            violations.append(violation_record)
            
            # Save updated violations
            with open(violations_file, "w") as f:
                json.dump(violations, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error recording governance violation: {e}")
            
    def calculate_rule_based_confidence(self, context: Dict) -> Tuple[float, str, str]:
        """Calculate confidence score based on rules

        Args:
            context (Dict): Trading context

        Returns:
            Tuple[float, str, str]: (confidence_score, explanation, recommendation)
        """
        # Extract context information
        strategy = context["strategy"]
        news = context["news"]
        recent_trades = context["recent_trades"]
        market_condition = context["market_condition"]
        
        # Initialize confidence components
        technical_confidence = 0.0
        psychology_confidence = 0.0
        news_confidence = 0.0
        
        # Technical confidence based on win rate and profit factor
        win_rate = strategy["win_rate"]
        profit_factor = strategy["profit_factor"]
        
        if win_rate >= 60:
            technical_confidence = 80.0
        elif win_rate >= 50:
            technical_confidence = 60.0
        elif win_rate >= 40:
            technical_confidence = 40.0
        else:
            technical_confidence = 20.0
            
        # Adjust based on profit factor
        if profit_factor >= 2.0:
            technical_confidence += 20.0
        elif profit_factor >= 1.5:
            technical_confidence += 10.0
        elif profit_factor < 1.0:
            technical_confidence -= 20.0
            
        # Cap technical confidence
        technical_confidence = max(0.0, min(100.0, technical_confidence))
        
        # Psychology confidence based on consecutive wins/losses
        consecutive_wins = strategy["consecutive_wins"]
        consecutive_losses = strategy["consecutive_losses"]
        
        if consecutive_losses >= 3:
            psychology_confidence = 20.0
        elif consecutive_losses >= 2:
            psychology_confidence = 40.0
        elif consecutive_wins >= 3:
            psychology_confidence = 90.0
        elif consecutive_wins >= 2:
            psychology_confidence = 80.0
        else:
            psychology_confidence = 60.0
            
        # Adjust based on recent trades
        recent_wins = sum(1 for trade in recent_trades if trade["win"])
        recent_losses = len(recent_trades) - recent_wins
        
        if recent_trades:
            recent_win_rate = (recent_wins / len(recent_trades)) * 100
            
            if recent_win_rate >= 70:
                psychology_confidence += 10.0
            elif recent_win_rate <= 30:
                psychology_confidence -= 10.0
                
        # Cap psychology confidence
        psychology_confidence = max(0.0, min(100.0, psychology_confidence))
        
        # News confidence
        if news["affected"]:
            news_confidence = 20.0  # Low confidence if affected by news
        else:
            news_confidence = 80.0  # High confidence if not affected by news
            
        # Market condition adjustment
        if market_condition == "trending":
            technical_confidence += 10.0
        elif market_condition == "choppy":
            technical_confidence -= 10.0
            
        # Cap technical confidence again after adjustments
        technical_confidence = max(0.0, min(100.0, technical_confidence))
        
        # Calculate weighted confidence score
        weights = self.decider_config["weighting"]
        confidence_score = (
            technical_confidence * weights["technical"] +
            psychology_confidence * weights["psychology"] +
            news_confidence * weights["news"]
        )
        
        # Generate explanation
        explanation = f"Technical: {technical_confidence:.1f}% (Win rate: {win_rate:.1f}%, PF: {profit_factor:.2f}), "\
                     f"Psychology: {psychology_confidence:.1f}% (Streak: {consecutive_wins}W/{consecutive_losses}L), "\
                     f"News: {news_confidence:.1f}% ({'Affected' if news['affected'] else 'Clear'})"
        
        # Determine recommendation
        thresholds = self.decider_config["confidence_thresholds"]
        
        if confidence_score >= thresholds["high"]:
            recommendation = "Take Trade"
        elif confidence_score >= thresholds["medium"]:
            recommendation = "Reduce Size"
        else:
            recommendation = "Skip Trade"
            
        return confidence_score, explanation, recommendation
        
    def get_trade_decision(self, strategy_name: str, symbol: str, 
                          market_condition: str) -> Dict:
        """Get trade decision based on context

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            market_condition (str): Current market condition

        Returns:
            Dict: Trade decision
        """
        # Get trading context
        context = self.get_trade_context(strategy_name, symbol, market_condition)
        
        # Calculate confidence score
        confidence_score, explanation, recommendation = self.calculate_confidence_score(context)
        
        # Compile decision
        decision = {
            "strategy": strategy_name,
            "symbol": symbol,
            "market_condition": market_condition,
            "confidence_score": confidence_score,
            "explanation": explanation,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return decision


# Helper functions
def get_trade_decision(strategy_name: str, symbol: str, market_condition: str) -> Dict:
    """Get trade decision based on context (helper function)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Trading symbol
        market_condition (str): Current market condition

    Returns:
        Dict: Trade decision
    """
    decider = SentinelDecider()
    return decider.get_trade_decision(strategy_name, symbol, market_condition)


# For testing
if __name__ == "__main__":
    # Create sentinel decider
    decider = SentinelDecider()
    
    # Test strategies and symbols
    test_cases = [
        ("fibonacci_retracement", "EURUSD", "trending"),
        ("support_resistance", "GBPUSD", "ranging"),
        ("trend_following", "USDJPY", "choppy")
    ]
    
    for strategy, symbol, condition in test_cases:
        # Get trade decision
        decision = decider.get_trade_decision(strategy, symbol, condition)
        
        # Print decision
        print(f"\nDecision for {strategy} on {symbol} in {condition} market:")
        print(f"  Confidence: {decision['confidence_score']:.1f}%")
        print(f"  Explanation: {decision['explanation']}")
        print(f"  Recommendation: {decision['recommendation']}")