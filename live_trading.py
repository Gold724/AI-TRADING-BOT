# live_trading.py

import os
import json
import time
import logging
import threading
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("live_trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LiveTrading")

# Try to import from other modules
try:
    from risk_control import RiskController
except ImportError:
    logger.warning("Could not import RiskController, using minimal version")
    # Define a minimal version if the import fails
    class RiskController:
        def calculate_position_size(self, strategy_name, symbol, risk_percent, entry_price, stop_loss):
            return 0.01  # Default to 0.01 lots
        
        def is_trading_allowed(self, strategy_name):
            return True

try:
    from emergency_protocol import EmergencyProtocol
except ImportError:
    logger.warning("Could not import EmergencyProtocol, using minimal version")
    # Define a minimal version if the import fails
    class EmergencyProtocol:
        def is_trading_allowed(self):
            return True
        
        def get_emergency_status(self):
            return "normal", "No emergency"

class OrderType(Enum):
    """Enum for order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderDirection(Enum):
    """Enum for order directions"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Enum for order statuses"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class Order:
    """Class representing a trading order"""
    
    def __init__(
        self,
        symbol: str,
        order_type: OrderType,
        direction: OrderDirection,
        volume: float,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "",
        strategy: str = "",
        signal_id: str = ""
    ):
        """Initialize an order
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            order_type: Type of order (MARKET, LIMIT, STOP, STOP_LIMIT)
            direction: Direction of order (BUY, SELL)
            volume: Volume in lots
            entry_price: Entry price for limit and stop orders
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Comment for the order
            strategy: Strategy that generated the order
            signal_id: ID of the signal that generated the order
        """
        self.symbol = symbol
        self.order_type = order_type
        self.direction = direction
        self.volume = volume
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.comment = comment
        self.strategy = strategy
        self.signal_id = signal_id
        
        # Order status
        self.status = OrderStatus.PENDING
        self.order_id = None
        self.open_time = None
        self.close_time = None
        self.profit = 0.0
        self.commission = 0.0
        self.swap = 0.0
        self.error = None
        
    def to_dict(self) -> Dict:
        """Convert order to dictionary
        
        Returns:
            Dict: Order as dictionary
        """
        return {
            "symbol": self.symbol,
            "order_type": self.order_type.value,
            "direction": self.direction.value,
            "volume": self.volume,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "comment": self.comment,
            "strategy": self.strategy,
            "signal_id": self.signal_id,
            "status": self.status.value,
            "order_id": self.order_id,
            "open_time": self.open_time.isoformat() if self.open_time else None,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "profit": self.profit,
            "commission": self.commission,
            "swap": self.swap,
            "error": str(self.error) if self.error else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Order':
        """Create order from dictionary
        
        Args:
            data: Dictionary with order data
            
        Returns:
            Order: Order object
        """
        order = cls(
            symbol=data["symbol"],
            order_type=OrderType(data["order_type"]),
            direction=OrderDirection(data["direction"]),
            volume=data["volume"],
            entry_price=data.get("entry_price"),
            stop_loss=data.get("stop_loss"),
            take_profit=data.get("take_profit"),
            comment=data.get("comment", ""),
            strategy=data.get("strategy", ""),
            signal_id=data.get("signal_id", "")
        )
        
        # Set status and other fields
        order.status = OrderStatus(data["status"])
        order.order_id = data.get("order_id")
        
        if data.get("open_time"):
            order.open_time = datetime.fromisoformat(data["open_time"])
            
        if data.get("close_time"):
            order.close_time = datetime.fromisoformat(data["close_time"])
            
        order.profit = data.get("profit", 0.0)
        order.commission = data.get("commission", 0.0)
        order.swap = data.get("swap", 0.0)
        order.error = data.get("error")
        
        return order

class BrokerAdapter(ABC):
    """Abstract base class for broker adapters"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the broker
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the broker
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the broker
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict:
        """Get account information
        
        Returns:
            Dict: Account information
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """Get open positions
        
        Returns:
            List[Dict]: List of open positions
        """
        pass
    
    @abstractmethod
    def get_orders(self) -> List[Dict]:
        """Get pending orders
        
        Returns:
            List[Dict]: List of pending orders
        """
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Tuple[bool, Optional[str], Optional[str]]:
        """Place an order
        
        Args:
            order: Order to place
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: Success, order ID, error message
        """
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """Modify an order
        
        Args:
            order_id: ID of the order to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        pass
    
    @abstractmethod
    def close_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """Close an order
        
        Args:
            order_id: ID of the order to close
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        pass
    
    @abstractmethod
    def close_all_orders(self) -> Tuple[int, Optional[str]]:
        """Close all open orders
        
        Returns:
            Tuple[int, Optional[str]]: Number of orders closed, error message
        """
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a symbol
        
        Args:
            symbol: Symbol to get market data for
            
        Returns:
            Dict: Market data
        """
        pass

class ExnessBrokerAdapter(BrokerAdapter):
    """Broker adapter for Exness"""
    
    def __init__(self, config: Dict):
        """Initialize the Exness broker adapter
        
        Args:
            config: Configuration for the broker adapter
        """
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.server = config.get("server", "")
        self.account_id = config.get("account_id", "")
        self.connected = False
        self.last_error = None
        self.session = requests.Session()
        
        # Set up headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        })
        
        # Base URL
        self.base_url = f"https://api.exness.com/v1"
        
    def connect(self) -> bool:
        """Connect to Exness
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test connection by getting account info
            response = self.session.get(f"{self.base_url}/accounts/{self.account_id}")
            
            if response.status_code == 200:
                self.connected = True
                logger.info("Connected to Exness")
                return True
            else:
                self.last_error = f"Connection failed: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return False
        except Exception as e:
            self.last_error = f"Connection failed: {str(e)}"
            logger.error(self.last_error)
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Exness
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        self.connected = False
        self.session.close()
        logger.info("Disconnected from Exness")
        return True
    
    def is_connected(self) -> bool:
        """Check if connected to Exness
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def get_account_info(self) -> Dict:
        """Get account information
        
        Returns:
            Dict: Account information
        """
        try:
            response = self.session.get(f"{self.base_url}/accounts/{self.account_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Format account info
                account_info = {
                    "account_id": self.account_id,
                    "balance": data.get("balance", 0.0),
                    "equity": data.get("equity", 0.0),
                    "margin": data.get("margin", 0.0),
                    "free_margin": data.get("free_margin", 0.0),
                    "margin_level": data.get("margin_level", 0.0),
                    "currency": data.get("currency", "USD"),
                    "leverage": data.get("leverage", 1),
                    "server": self.server
                }
                
                return account_info
            else:
                self.last_error = f"Failed to get account info: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return {}
        except Exception as e:
            self.last_error = f"Failed to get account info: {str(e)}"
            logger.error(self.last_error)
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get open positions
        
        Returns:
            List[Dict]: List of open positions
        """
        try:
            response = self.session.get(f"{self.base_url}/accounts/{self.account_id}/positions")
            
            if response.status_code == 200:
                data = response.json()
                positions = []
                
                for pos in data:
                    position = {
                        "order_id": pos.get("id"),
                        "symbol": pos.get("symbol"),
                        "direction": "BUY" if pos.get("type") == "buy" else "SELL",
                        "volume": pos.get("volume", 0.0),
                        "open_price": pos.get("open_price", 0.0),
                        "current_price": pos.get("current_price", 0.0),
                        "stop_loss": pos.get("sl", 0.0),
                        "take_profit": pos.get("tp", 0.0),
                        "profit": pos.get("profit", 0.0),
                        "swap": pos.get("swap", 0.0),
                        "open_time": datetime.fromtimestamp(pos.get("open_time", 0)).isoformat(),
                        "comment": pos.get("comment", "")
                    }
                    
                    positions.append(position)
                
                return positions
            else:
                self.last_error = f"Failed to get positions: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return []
        except Exception as e:
            self.last_error = f"Failed to get positions: {str(e)}"
            logger.error(self.last_error)
            return []
    
    def get_orders(self) -> List[Dict]:
        """Get pending orders
        
        Returns:
            List[Dict]: List of pending orders
        """
        try:
            response = self.session.get(f"{self.base_url}/accounts/{self.account_id}/orders")
            
            if response.status_code == 200:
                data = response.json()
                orders = []
                
                for ord in data:
                    order = {
                        "order_id": ord.get("id"),
                        "symbol": ord.get("symbol"),
                        "direction": "BUY" if ord.get("type") == "buy" else "SELL",
                        "volume": ord.get("volume", 0.0),
                        "order_type": ord.get("order_type", "LIMIT").upper(),
                        "price": ord.get("price", 0.0),
                        "stop_loss": ord.get("sl", 0.0),
                        "take_profit": ord.get("tp", 0.0),
                        "open_time": datetime.fromtimestamp(ord.get("open_time", 0)).isoformat(),
                        "expiration": datetime.fromtimestamp(ord.get("expiration", 0)).isoformat() if ord.get("expiration") else None,
                        "comment": ord.get("comment", "")
                    }
                    
                    orders.append(order)
                
                return orders
            else:
                self.last_error = f"Failed to get orders: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return []
        except Exception as e:
            self.last_error = f"Failed to get orders: {str(e)}"
            logger.error(self.last_error)
            return []
    
    def place_order(self, order: Order) -> Tuple[bool, Optional[str], Optional[str]]:
        """Place an order with Exness
        
        Args:
            order: Order to place
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: Success, order ID, error message
        """
        try:
            # Prepare order data
            order_data = {
                "symbol": order.symbol,
                "type": order.direction.value.lower(),
                "volume": order.volume,
                "comment": order.comment
            }
            
            # Set order type specific parameters
            if order.order_type == OrderType.MARKET:
                endpoint = f"{self.base_url}/accounts/{self.account_id}/trade"
            else:
                endpoint = f"{self.base_url}/accounts/{self.account_id}/orders"
                order_data["order_type"] = order.order_type.value.lower()
                order_data["price"] = order.entry_price
            
            # Set stop loss and take profit
            if order.stop_loss:
                order_data["sl"] = order.stop_loss
                
            if order.take_profit:
                order_data["tp"] = order.take_profit
            
            # Send request
            response = self.session.post(endpoint, json=order_data)
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get("order_id")
                
                if order_id:
                    logger.info(f"Order placed successfully: {order_id}")
                    return True, order_id, None
                else:
                    error = "Order placed but no order ID returned"
                    logger.warning(error)
                    return False, None, error
            else:
                error = f"Failed to place order: {response.status_code} {response.text}"
                logger.error(error)
                return False, None, error
        except Exception as e:
            error = f"Failed to place order: {str(e)}"
            logger.error(error)
            return False, None, error
    
    def modify_order(self, order_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """Modify an order with Exness
        
        Args:
            order_id: ID of the order to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        try:
            # Prepare modification data
            modify_data = {}
            
            if stop_loss is not None:
                modify_data["sl"] = stop_loss
                
            if take_profit is not None:
                modify_data["tp"] = take_profit
                
            if not modify_data:
                return True, None  # Nothing to modify
            
            # Send request
            response = self.session.put(f"{self.base_url}/accounts/{self.account_id}/positions/{order_id}", json=modify_data)
            
            if response.status_code == 200:
                logger.info(f"Order {order_id} modified successfully")
                return True, None
            else:
                error = f"Failed to modify order: {response.status_code} {response.text}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Failed to modify order: {str(e)}"
            logger.error(error)
            return False, error
    
    def close_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """Close an order with Exness
        
        Args:
            order_id: ID of the order to close
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        try:
            # Send request
            response = self.session.delete(f"{self.base_url}/accounts/{self.account_id}/positions/{order_id}")
            
            if response.status_code == 200:
                logger.info(f"Order {order_id} closed successfully")
                return True, None
            else:
                error = f"Failed to close order: {response.status_code} {response.text}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Failed to close order: {str(e)}"
            logger.error(error)
            return False, error
    
    def close_all_orders(self) -> Tuple[int, Optional[str]]:
        """Close all open orders with Exness
        
        Returns:
            Tuple[int, Optional[str]]: Number of orders closed, error message
        """
        try:
            # Get open positions
            positions = self.get_positions()
            
            if not positions:
                return 0, None  # No positions to close
                
            # Close each position
            closed_count = 0
            errors = []
            
            for position in positions:
                order_id = position.get("order_id")
                
                if order_id:
                    success, error = self.close_order(order_id)
                    
                    if success:
                        closed_count += 1
                    else:
                        errors.append(f"Order {order_id}: {error}")
            
            if errors:
                error_message = "\n".join(errors)
                logger.warning(f"Closed {closed_count} orders with errors: {error_message}")
                return closed_count, error_message
            else:
                logger.info(f"Closed {closed_count} orders successfully")
                return closed_count, None
        except Exception as e:
            error = f"Failed to close all orders: {str(e)}"
            logger.error(error)
            return 0, error
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a symbol from Exness
        
        Args:
            symbol: Symbol to get market data for
            
        Returns:
            Dict: Market data
        """
        try:
            response = self.session.get(f"{self.base_url}/symbols/{symbol}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Format market data
                market_data = {
                    "symbol": symbol,
                    "bid": data.get("bid", 0.0),
                    "ask": data.get("ask", 0.0),
                    "spread": data.get("spread", 0.0),
                    "time": datetime.now().isoformat(),
                    "high": data.get("high", 0.0),
                    "low": data.get("low", 0.0),
                    "volume": data.get("volume", 0.0),
                    "digits": data.get("digits", 5),
                    "contract_size": data.get("contract_size", 100000.0),
                    "point": data.get("point", 0.00001)
                }
                
                return market_data
            else:
                self.last_error = f"Failed to get market data: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return {}
        except Exception as e:
            self.last_error = f"Failed to get market data: {str(e)}"
            logger.error(self.last_error)
            return {}

class BulenoxBrokerAdapter(BrokerAdapter):
    """Broker adapter for Bulenox"""
    
    def __init__(self, config: Dict):
        """Initialize the Bulenox broker adapter
        
        Args:
            config: Configuration for the broker adapter
        """
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.server = config.get("server", "")
        self.account_id = config.get("account_id", "")
        self.connected = False
        self.last_error = None
        self.session = requests.Session()
        
        # Set up headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-API-SECRET": self.api_secret
        })
        
        # Base URL
        self.base_url = f"https://api.bulenox.com/v1"
        
    def connect(self) -> bool:
        """Connect to Bulenox
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test connection by getting account info
            response = self.session.get(f"{self.base_url}/account")
            
            if response.status_code == 200:
                self.connected = True
                logger.info("Connected to Bulenox")
                return True
            else:
                self.last_error = f"Connection failed: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return False
        except Exception as e:
            self.last_error = f"Connection failed: {str(e)}"
            logger.error(self.last_error)
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Bulenox
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        self.connected = False
        self.session.close()
        logger.info("Disconnected from Bulenox")
        return True
    
    def is_connected(self) -> bool:
        """Check if connected to Bulenox
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def get_account_info(self) -> Dict:
        """Get account information
        
        Returns:
            Dict: Account information
        """
        try:
            response = self.session.get(f"{self.base_url}/account")
            
            if response.status_code == 200:
                data = response.json()
                
                # Format account info
                account_info = {
                    "account_id": self.account_id,
                    "balance": data.get("balance", 0.0),
                    "equity": data.get("equity", 0.0),
                    "margin": data.get("margin", 0.0),
                    "free_margin": data.get("free_margin", 0.0),
                    "margin_level": data.get("margin_level", 0.0),
                    "currency": data.get("currency", "USD"),
                    "leverage": data.get("leverage", 1),
                    "server": self.server
                }
                
                return account_info
            else:
                self.last_error = f"Failed to get account info: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return {}
        except Exception as e:
            self.last_error = f"Failed to get account info: {str(e)}"
            logger.error(self.last_error)
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get open positions
        
        Returns:
            List[Dict]: List of open positions
        """
        try:
            response = self.session.get(f"{self.base_url}/positions")
            
            if response.status_code == 200:
                data = response.json()
                positions = []
                
                for pos in data:
                    position = {
                        "order_id": pos.get("id"),
                        "symbol": pos.get("symbol"),
                        "direction": "BUY" if pos.get("direction") == "buy" else "SELL",
                        "volume": pos.get("volume", 0.0),
                        "open_price": pos.get("open_price", 0.0),
                        "current_price": pos.get("current_price", 0.0),
                        "stop_loss": pos.get("stop_loss", 0.0),
                        "take_profit": pos.get("take_profit", 0.0),
                        "profit": pos.get("profit", 0.0),
                        "swap": pos.get("swap", 0.0),
                        "open_time": pos.get("open_time"),
                        "comment": pos.get("comment", "")
                    }
                    
                    positions.append(position)
                
                return positions
            else:
                self.last_error = f"Failed to get positions: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return []
        except Exception as e:
            self.last_error = f"Failed to get positions: {str(e)}"
            logger.error(self.last_error)
            return []
    
    def get_orders(self) -> List[Dict]:
        """Get pending orders
        
        Returns:
            List[Dict]: List of pending orders
        """
        try:
            response = self.session.get(f"{self.base_url}/orders")
            
            if response.status_code == 200:
                data = response.json()
                orders = []
                
                for ord in data:
                    order = {
                        "order_id": ord.get("id"),
                        "symbol": ord.get("symbol"),
                        "direction": "BUY" if ord.get("direction") == "buy" else "SELL",
                        "volume": ord.get("volume", 0.0),
                        "order_type": ord.get("type", "LIMIT").upper(),
                        "price": ord.get("price", 0.0),
                        "stop_loss": ord.get("stop_loss", 0.0),
                        "take_profit": ord.get("take_profit", 0.0),
                        "open_time": ord.get("open_time"),
                        "expiration": ord.get("expiration"),
                        "comment": ord.get("comment", "")
                    }
                    
                    orders.append(order)
                
                return orders
            else:
                self.last_error = f"Failed to get orders: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return []
        except Exception as e:
            self.last_error = f"Failed to get orders: {str(e)}"
            logger.error(self.last_error)
            return []
    
    def place_order(self, order: Order) -> Tuple[bool, Optional[str], Optional[str]]:
        """Place an order with Bulenox
        
        Args:
            order: Order to place
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: Success, order ID, error message
        """
        try:
            # Prepare order data
            order_data = {
                "symbol": order.symbol,
                "direction": order.direction.value.lower(),
                "volume": order.volume,
                "comment": order.comment
            }
            
            # Set order type specific parameters
            if order.order_type == OrderType.MARKET:
                endpoint = f"{self.base_url}/trade"
            else:
                endpoint = f"{self.base_url}/orders"
                order_data["type"] = order.order_type.value.lower()
                order_data["price"] = order.entry_price
            
            # Set stop loss and take profit
            if order.stop_loss:
                order_data["stop_loss"] = order.stop_loss
                
            if order.take_profit:
                order_data["take_profit"] = order.take_profit
            
            # Send request
            response = self.session.post(endpoint, json=order_data)
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get("order_id")
                
                if order_id:
                    logger.info(f"Order placed successfully: {order_id}")
                    return True, order_id, None
                else:
                    error = "Order placed but no order ID returned"
                    logger.warning(error)
                    return False, None, error
            else:
                error = f"Failed to place order: {response.status_code} {response.text}"
                logger.error(error)
                return False, None, error
        except Exception as e:
            error = f"Failed to place order: {str(e)}"
            logger.error(error)
            return False, None, error
    
    def modify_order(self, order_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """Modify an order with Bulenox
        
        Args:
            order_id: ID of the order to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        try:
            # Prepare modification data
            modify_data = {}
            
            if stop_loss is not None:
                modify_data["stop_loss"] = stop_loss
                
            if take_profit is not None:
                modify_data["take_profit"] = take_profit
                
            if not modify_data:
                return True, None  # Nothing to modify
            
            # Send request
            response = self.session.put(f"{self.base_url}/positions/{order_id}", json=modify_data)
            
            if response.status_code == 200:
                logger.info(f"Order {order_id} modified successfully")
                return True, None
            else:
                error = f"Failed to modify order: {response.status_code} {response.text}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Failed to modify order: {str(e)}"
            logger.error(error)
            return False, error
    
    def close_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """Close an order with Bulenox
        
        Args:
            order_id: ID of the order to close
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        try:
            # Send request
            response = self.session.delete(f"{self.base_url}/positions/{order_id}")
            
            if response.status_code == 200:
                logger.info(f"Order {order_id} closed successfully")
                return True, None
            else:
                error = f"Failed to close order: {response.status_code} {response.text}"
                logger.error(error)
                return False, error
        except Exception as e:
            error = f"Failed to close order: {str(e)}"
            logger.error(error)
            return False, error
    
    def close_all_orders(self) -> Tuple[int, Optional[str]]:
        """Close all open orders with Bulenox
        
        Returns:
            Tuple[int, Optional[str]]: Number of orders closed, error message
        """
        try:
            # Send request to close all positions
            response = self.session.delete(f"{self.base_url}/positions")
            
            if response.status_code == 200:
                data = response.json()
                closed_count = data.get("closed_count", 0)
                logger.info(f"Closed {closed_count} orders successfully")
                return closed_count, None
            else:
                error = f"Failed to close all orders: {response.status_code} {response.text}"
                logger.error(error)
                return 0, error
        except Exception as e:
            error = f"Failed to close all orders: {str(e)}"
            logger.error(error)
            return 0, error
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a symbol from Bulenox
        
        Args:
            symbol: Symbol to get market data for
            
        Returns:
            Dict: Market data
        """
        try:
            response = self.session.get(f"{self.base_url}/symbols/{symbol}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Format market data
                market_data = {
                    "symbol": symbol,
                    "bid": data.get("bid", 0.0),
                    "ask": data.get("ask", 0.0),
                    "spread": data.get("ask", 0.0) - data.get("bid", 0.0),
                    "time": datetime.now().isoformat(),
                    "high": data.get("high", 0.0),
                    "low": data.get("low", 0.0),
                    "volume": data.get("volume", 0.0),
                    "digits": data.get("digits", 5),
                    "contract_size": data.get("contract_size", 100000.0),
                    "point": data.get("point", 0.00001)
                }
                
                return market_data
            else:
                self.last_error = f"Failed to get market data: {response.status_code} {response.text}"
                logger.error(self.last_error)
                return {}
        except Exception as e:
            self.last_error = f"Failed to get market data: {str(e)}"
            logger.error(self.last_error)
            return {}

class MockBrokerAdapter(BrokerAdapter):
    """Mock broker adapter for testing"""
    
    def __init__(self, config: Dict):
        """Initialize the mock broker adapter
        
        Args:
            config: Configuration for the broker adapter
        """
        self.config = config
        self.connected = False
        self.last_error = None
        self.account_info = {
            "account_id": "mock_account",
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "free_margin": 10000.0,
            "margin_level": 0.0,
            "currency": "USD",
            "leverage": 100,
            "server": "mock_server"
        }
        self.positions = []
        self.orders = []
        self.order_id_counter = 1000
        self.market_data = {
            "EURUSD": {"bid": 1.1000, "ask": 1.1002, "spread": 0.0002, "digits": 5, "contract_size": 100000.0, "point": 0.00001},
            "GBPUSD": {"bid": 1.2500, "ask": 1.2503, "spread": 0.0003, "digits": 5, "contract_size": 100000.0, "point": 0.00001},
            "USDJPY": {"bid": 110.00, "ask": 110.03, "spread": 0.03, "digits": 3, "contract_size": 100000.0, "point": 0.001},
            "AUDUSD": {"bid": 0.7000, "ask": 0.7002, "spread": 0.0002, "digits": 5, "contract_size": 100000.0, "point": 0.00001},
            "USDCAD": {"bid": 1.3000, "ask": 1.3003, "spread": 0.0003, "digits": 5, "contract_size": 100000.0, "point": 0.00001},
        }
        
    def connect(self) -> bool:
        """Connect to the mock broker
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.connected = True
        logger.info("Connected to mock broker")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from the mock broker
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        self.connected = False
        logger.info("Disconnected from mock broker")
        return True
    
    def is_connected(self) -> bool:
        """Check if connected to the mock broker
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def get_account_info(self) -> Dict:
        """Get account information
        
        Returns:
            Dict: Account information
        """
        if not self.connected:
            self.last_error = "Not connected"
            return {}
            
        # Update equity based on open positions
        profit_sum = sum(pos.get("profit", 0.0) for pos in self.positions)
        self.account_info["equity"] = self.account_info["balance"] + profit_sum
        self.account_info["free_margin"] = self.account_info["equity"] - self.account_info["margin"]
        
        if self.account_info["margin"] > 0:
            self.account_info["margin_level"] = (self.account_info["equity"] / self.account_info["margin"]) * 100
        else:
            self.account_info["margin_level"] = 0
            
        return self.account_info.copy()
    
    def get_positions(self) -> List[Dict]:
        """Get open positions
        
        Returns:
            List[Dict]: List of open positions
        """
        if not self.connected:
            self.last_error = "Not connected"
            return []
            
        # Update position prices and profits
        for pos in self.positions:
            symbol = pos["symbol"]
            direction = pos["direction"]
            volume = pos["volume"]
            open_price = pos["open_price"]
            
            if symbol in self.market_data:
                if direction == "BUY":
                    current_price = self.market_data[symbol]["bid"]
                    pos["profit"] = (current_price - open_price) * volume * self.market_data[symbol]["contract_size"]
                else:  # SELL
                    current_price = self.market_data[symbol]["ask"]
                    pos["profit"] = (open_price - current_price) * volume * self.market_data[symbol]["contract_size"]
                    
                pos["current_price"] = current_price
            
        return self.positions.copy()
    
    def get_orders(self) -> List[Dict]:
        """Get pending orders
        
        Returns:
            List[Dict]: List of pending orders
        """
        if not self.connected:
            self.last_error = "Not connected"
            return []
            
        return self.orders.copy()
    
    def place_order(self, order: Order) -> Tuple[bool, Optional[str], Optional[str]]:
        """Place an order with the mock broker
        
        Args:
            order: Order to place
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: Success, order ID, error message
        """
        if not self.connected:
            self.last_error = "Not connected"
            return False, None, "Not connected"
            
        # Check if symbol exists
        if order.symbol not in self.market_data:
            error = f"Symbol {order.symbol} not found"
            self.last_error = error
            return False, None, error
            
        # Generate order ID
        order_id = str(self.order_id_counter)
        self.order_id_counter += 1
        
        # Handle market orders
        if order.order_type == OrderType.MARKET:
            # Create position
            position = {
                "order_id": order_id,
                "symbol": order.symbol,
                "direction": order.direction.value,
                "volume": order.volume,
                "open_price": self.market_data[order.symbol]["ask"] if order.direction == OrderDirection.BUY else self.market_data[order.symbol]["bid"],
                "current_price": self.market_data[order.symbol]["bid"] if order.direction == OrderDirection.BUY else self.market_data[order.symbol]["ask"],
                "stop_loss": order.stop_loss,
                "take_profit": order.take_profit,
                "profit": 0.0,
                "swap": 0.0,
                "open_time": datetime.now().isoformat(),
                "comment": order.comment
            }
            
            # Add position
            self.positions.append(position)
            
            # Update account margin
            margin_per_lot = 1000.0  # Simplified margin calculation
            self.account_info["margin"] += order.volume * margin_per_lot
            
            logger.info(f"Market order placed: {order_id}")
            return True, order_id, None
        else:
            # Create pending order
            pending_order = {
                "order_id": order_id,
                "symbol": order.symbol,
                "direction": order.direction.value,
                "volume": order.volume,
                "order_type": order.order_type.value,
                "price": order.entry_price,
                "stop_loss": order.stop_loss,
                "take_profit": order.take_profit,
                "open_time": datetime.now().isoformat(),
                "expiration": None,
                "comment": order.comment
            }
            
            # Add order
            self.orders.append(pending_order)
            
            logger.info(f"Pending order placed: {order_id}")
            return True, order_id, None
    
    def modify_order(self, order_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """Modify an order with the mock broker
        
        Args:
            order_id: ID of the order to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        if not self.connected:
            self.last_error = "Not connected"
            return False, "Not connected"
            
        # Find position
        for pos in self.positions:
            if pos["order_id"] == order_id:
                if stop_loss is not None:
                    pos["stop_loss"] = stop_loss
                    
                if take_profit is not None:
                    pos["take_profit"] = take_profit
                    
                logger.info(f"Position {order_id} modified")
                return True, None
                
        # Find pending order
        for ord in self.orders:
            if ord["order_id"] == order_id:
                if stop_loss is not None:
                    ord["stop_loss"] = stop_loss
                    
                if take_profit is not None:
                    ord["take_profit"] = take_profit
                    
                logger.info(f"Order {order_id} modified")
                return True, None
                
        error = f"Order {order_id} not found"
        self.last_error = error
        return False, error
    
    def close_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """Close an order with the mock broker
        
        Args:
            order_id: ID of the order to close
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        if not self.connected:
            self.last_error = "Not connected"
            return False, "Not connected"
            
        # Find position
        for i, pos in enumerate(self.positions):
            if pos["order_id"] == order_id:
                # Update account balance
                self.account_info["balance"] += pos["profit"]
                
                # Update account margin
                margin_per_lot = 1000.0  # Simplified margin calculation
                self.account_info["margin"] -= pos["volume"] * margin_per_lot
                
                # Remove position
                self.positions.pop(i)
                
                logger.info(f"Position {order_id} closed")
                return True, None
                
        # Find pending order
        for i, ord in enumerate(self.orders):
            if ord["order_id"] == order_id:
                # Remove order
                self.orders.pop(i)
                
                logger.info(f"Order {order_id} canceled")
                return True, None
                
        error = f"Order {order_id} not found"
        self.last_error = error
        return False, error
    
    def close_all_orders(self) -> Tuple[int, Optional[str]]:
        """Close all open orders with the mock broker
        
        Returns:
            Tuple[int, Optional[str]]: Number of orders closed, error message
        """
        if not self.connected:
            self.last_error = "Not connected"
            return 0, "Not connected"
            
        # Close positions
        closed_count = len(self.positions)
        
        # Update account balance
        for pos in self.positions:
            self.account_info["balance"] += pos["profit"]
            
        # Reset margin
        self.account_info["margin"] = 0.0
        
        # Clear positions and orders
        self.positions = []
        self.orders = []
        
        logger.info(f"Closed {closed_count} orders")
        return closed_count, None
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a symbol from the mock broker
        
        Args:
            symbol: Symbol to get market data for
            
        Returns:
            Dict: Market data
        """
        if not self.connected:
            self.last_error = "Not connected"
            return {}
            
        if symbol not in self.market_data:
            self.last_error = f"Symbol {symbol} not found"
            return {}
            
        # Create a copy of the market data
        data = self.market_data[symbol].copy()
        
        # Add additional fields
        data["symbol"] = symbol
        data["time"] = datetime.now().isoformat()
        data["high"] = data["ask"] + 0.0010
        data["low"] = data["bid"] - 0.0010
        data["volume"] = 1000.0
        
        return data

class LiveTrading:
    """Class for live trading"""
    
    def __init__(self, config_path: str = "config/live_trading_config.json"):
        """Initialize the LiveTrading class
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.broker_adapter = self._initialize_broker_adapter()
        
        # Initialize components
        self.data_dir = os.path.join("data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.risk_controller = RiskController()
        self.emergency_protocol = EmergencyProtocol()
        
        # Order history
        self.order_history_path = os.path.join(self.data_dir, "order_history.json")
        self.order_history = self._load_order_history()
        
        # Active orders
        self.active_orders = {}
        
        # Start update thread
        self.update_interval = self.config.get("update_interval", 5)  # seconds
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
            "broker": {
                "name": "mock",
                "config": {
                    "api_key": "",
                    "api_secret": "",
                    "server": "",
                    "account_id": ""
                }
            },
            "risk": {
                "max_risk_per_trade": 1.0,  # Percentage of account balance
                "max_open_trades": 5,
                "max_daily_drawdown": 5.0,  # Percentage of account balance
                "default_stop_loss_pips": 50,
                "default_take_profit_pips": 100
            },
            "symbols": [
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "AUDUSD",
                "USDCAD"
            ],
            "update_interval": 5,
            "auto_update": True,
            "max_order_history": 1000,
            "notifications": {
                "enabled": False,
                "slack_webhook": "",
                "telegram_bot_token": "",
                "telegram_chat_id": ""
            }
        }
    
    def _initialize_broker_adapter(self) -> BrokerAdapter:
        """Initialize the broker adapter
        
        Returns:
            BrokerAdapter: Broker adapter
        """
        broker_name = self.config.get("broker", {}).get("name", "mock")
        broker_config = self.config.get("broker", {}).get("config", {})
        
        if broker_name == "exness":
            return ExnessBrokerAdapter(broker_config)
        elif broker_name == "bulenox":
            return BulenoxBrokerAdapter(broker_config)
        else:
            # Default to mock broker
            logger.info("Using mock broker adapter")
            return MockBrokerAdapter(broker_config)
    
    def _load_order_history(self) -> List[Dict]:
        """Load order history from file
        
        Returns:
            List[Dict]: Order history
        """
        try:
            if os.path.exists(self.order_history_path):
                with open(self.order_history_path, "r") as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading order history: {e}")
            return []
    
    def _save_order_history(self):
        """Save order history to file"""
        try:
            # Limit history size
            max_history = self.config.get("max_order_history", 1000)
            if len(self.order_history) > max_history:
                self.order_history = self.order_history[-max_history:]
                
            with open(self.order_history_path, "w") as f:
                json.dump(self.order_history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving order history: {e}")
    
    def start_update_thread(self):
        """Start the update thread"""
        if self.running:
            logger.warning("Update thread already running")
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info("Started order update thread")
    
    def stop_update_thread(self):
        """Stop the update thread"""
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
            
        logger.info("Stopped order update thread")
    
    def _update_loop(self):
        """Update loop for orders"""
        while self.running:
            try:
                self.update_orders()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Short delay before retrying
    
    def update_orders(self):
        """Update orders from broker"""
        if not self.broker_adapter.is_connected():
            try:
                self.broker_adapter.connect()
            except Exception as e:
                logger.error(f"Error connecting to broker: {e}")
                return
                
        try:
            # Get positions from broker
            positions = self.broker_adapter.get_positions()
            
            # Update active orders
            current_order_ids = set()
            
            for pos in positions:
                order_id = pos.get("order_id")
                
                if order_id:
                    current_order_ids.add(order_id)
                    
                    if order_id in self.active_orders:
                        # Update existing order
                        order = self.active_orders[order_id]
                        
                        # Update profit
                        order.profit = pos.get("profit", 0.0)
                        
                        # Check for stop loss or take profit hit
                        if order.stop_loss and order.direction == OrderDirection.BUY and pos.get("current_price", 0.0) <= order.stop_loss:
                            logger.info(f"Stop loss hit for order {order_id}")
                            self.close_order(order_id)
                        elif order.stop_loss and order.direction == OrderDirection.SELL and pos.get("current_price", 0.0) >= order.stop_loss:
                            logger.info(f"Stop loss hit for order {order_id}")
                            self.close_order(order_id)
                        elif order.take_profit and order.direction == OrderDirection.BUY and pos.get("current_price", 0.0) >= order.take_profit:
                            logger.info(f"Take profit hit for order {order_id}")
                            self.close_order(order_id)
                        elif order.take_profit and order.direction == OrderDirection.SELL and pos.get("current_price", 0.0) <= order.take_profit:
                            logger.info(f"Take profit hit for order {order_id}")
                            self.close_order(order_id)
                    else:
                        # New order (from another source)
                        order = Order(
                            symbol=pos.get("symbol", ""),
                            order_type=OrderType.MARKET,
                            direction=OrderDirection.BUY if pos.get("direction") == "BUY" else OrderDirection.SELL,
                            volume=pos.get("volume", 0.0),
                            entry_price=pos.get("open_price", 0.0),
                            stop_loss=pos.get("stop_loss", None),
                            take_profit=pos.get("take_profit", None),
                            comment=pos.get("comment", "")
                        )
                        
                        order.order_id = order_id
                        order.status = OrderStatus.OPEN
                        order.open_time = datetime.fromisoformat(pos.get("open_time")) if isinstance(pos.get("open_time"), str) else datetime.now()
                        order.profit = pos.get("profit", 0.0)
                        
                        self.active_orders[order_id] = order
                        logger.info(f"Found new order: {order_id}")
            
            # Check for closed orders
            closed_order_ids = set(self.active_orders.keys()) - current_order_ids
            
            for order_id in closed_order_ids:
                order = self.active_orders.pop(order_id)
                order.status = OrderStatus.CLOSED
                order.close_time = datetime.now()
                
                # Add to history
                self.order_history.append(order.to_dict())
                logger.info(f"Order {order_id} closed")
                
            # Save order history
            if closed_order_ids:
                self._save_order_history()
                
            # Check emergency protocol
            if not self.emergency_protocol.is_trading_allowed():
                status, message = self.emergency_protocol.get_emergency_status()
                logger.warning(f"Emergency protocol active: {status} - {message}")
                
                if status in ["critical", "emergency"]:
                    # Close all orders
                    self.close_all_orders()
        except Exception as e:
            logger.error(f"Error updating orders: {e}")
    
    def connect(self) -> bool:
        """Connect to the broker
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            return self.broker_adapter.connect()
        except Exception as e:
            logger.error(f"Error connecting to broker: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from the broker
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            return self.broker_adapter.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from broker: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to the broker
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            return self.broker_adapter.is_connected()
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return False
    
    def get_account_info(self) -> Dict:
        """Get account information
        
        Returns:
            Dict: Account information
        """
        try:
            return self.broker_adapter.get_account_info()
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get open positions
        
        Returns:
            List[Dict]: List of open positions
        """
        try:
            return self.broker_adapter.get_positions()
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self) -> List[Dict]:
        """Get pending orders
        
        Returns:
            List[Dict]: List of pending orders
        """
        try:
            return self.broker_adapter.get_orders()
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def place_order(self, order: Order) -> Tuple[bool, Optional[str], Optional[str]]:
        """Place an order
        
        Args:
            order: Order to place
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: Success, order ID, error message
        """
        try:
            # Check emergency protocol
            if not self.emergency_protocol.is_trading_allowed():
                status, message = self.emergency_protocol.get_emergency_status()
                error = f"Trading not allowed: {status} - {message}"
                logger.warning(error)
                return False, None, error
                
            # Check risk controller
            if not self.risk_controller.is_trading_allowed(order.strategy):
                error = f"Trading not allowed for strategy {order.strategy}"
                logger.warning(error)
                return False, None, error
                
            # Calculate position size if not specified
            if order.volume <= 0 and order.stop_loss and order.entry_price:
                risk_percent = self.config.get("risk", {}).get("max_risk_per_trade", 1.0)
                order.volume = self.risk_controller.calculate_position_size(
                    strategy_name=order.strategy,
                    symbol=order.symbol,
                    risk_percent=risk_percent,
                    entry_price=order.entry_price,
                    stop_loss=order.stop_loss
                )
                
            # Check if volume is valid
            if order.volume <= 0:
                error = "Invalid volume"
                logger.warning(error)
                return False, None, error
                
            # Check max open trades
            max_open_trades = self.config.get("risk", {}).get("max_open_trades", 5)
            if len(self.active_orders) >= max_open_trades:
                error = f"Max open trades reached: {max_open_trades}"
                logger.warning(error)
                return False, None, error
                
            # Place order
            success, order_id, error = self.broker_adapter.place_order(order)
            
            if success and order_id:
                # Add to active orders
                order.order_id = order_id
                order.status = OrderStatus.OPEN if order.order_type == OrderType.MARKET else OrderStatus.PENDING
                order.open_time = datetime.now()
                
                self.active_orders[order_id] = order
                logger.info(f"Order placed: {order_id}")
                
                return True, order_id, None
            else:
                logger.error(f"Error placing order: {error}")
                return False, None, error
        except Exception as e:
            error = f"Error placing order: {str(e)}"
            logger.error(error)
            return False, None, error
    
    def modify_order(self, order_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """Modify an order
        
        Args:
            order_id: ID of the order to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        try:
            # Check if order exists
            if order_id not in self.active_orders:
                error = f"Order {order_id} not found"
                logger.warning(error)
                return False, error
                
            # Modify order
            success, error = self.broker_adapter.modify_order(order_id, stop_loss, take_profit)
            
            if success:
                # Update active order
                order = self.active_orders[order_id]
                
                if stop_loss is not None:
                    order.stop_loss = stop_loss
                    
                if take_profit is not None:
                    order.take_profit = take_profit
                    
                logger.info(f"Order {order_id} modified")
                return True, None
            else:
                logger.error(f"Error modifying order: {error}")
                return False, error
        except Exception as e:
            error = f"Error modifying order: {str(e)}"
            logger.error(error)
            return False, error
    
    def close_order(self, order_id: str) -> Tuple[bool, Optional[str]]:
        """Close an order
        
        Args:
            order_id: ID of the order to close
            
        Returns:
            Tuple[bool, Optional[str]]: Success, error message
        """
        try:
            # Check if order exists
            if order_id not in self.active_orders:
                error = f"Order {order_id} not found"
                logger.warning(error)
                return False, error
                
            # Close order
            success, error = self.broker_adapter.close_order(order_id)
            
            if success:
                # Update active order
                order = self.active_orders.pop(order_id)
                order.status = OrderStatus.CLOSED
                order.close_time = datetime.now()
                
                # Add to history
                self.order_history.append(order.to_dict())
                self._save_order_history()
                
                logger.info(f"Order {order_id} closed")
                return True, None
            else:
                logger.error(f"Error closing order: {error}")
                return False, error
        except Exception as e:
            error = f"Error closing order: {str(e)}"
            logger.error(error)
            return False, error
    
    def close_all_orders(self) -> Tuple[int, Optional[str]]:
        """Close all open orders
        
        Returns:
            Tuple[int, Optional[str]]: Number of orders closed, error message
        """
        try:
            # Close all orders
            closed_count, error = self.broker_adapter.close_all_orders()
            
            if closed_count > 0:
                # Update active orders
                for order_id, order in list(self.active_orders.items()):
                    order.status = OrderStatus.CLOSED
                    order.close_time = datetime.now()
                    
                    # Add to history
                    self.order_history.append(order.to_dict())
                    
                # Clear active orders
                self.active_orders = {}
                
                # Save order history
                self._save_order_history()
                
                logger.info(f"Closed {closed_count} orders")
            
            if error:
                logger.error(f"Error closing all orders: {error}")
                
            return closed_count, error
        except Exception as e:
            error = f"Error closing all orders: {str(e)}"
            logger.error(error)
            return 0, error
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a symbol
        
        Args:
            symbol: Symbol to get market data for
            
        Returns:
            Dict: Market data
        """
        try:
            return self.broker_adapter.get_market_data(symbol)
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}
    
    def get_order_history(self, limit: int = 100) -> List[Dict]:
        """Get order history
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            List[Dict]: Order history
        """
        # Return most recent orders first
        return sorted(
            self.order_history,
            key=lambda o: o.get("close_time", ""),
            reverse=True
        )[:limit]
    
    def get_active_orders(self) -> List[Dict]:
        """Get active orders
        
        Returns:
            List[Dict]: Active orders
        """
        return [order.to_dict() for order in self.active_orders.values()]
    
    def get_daily_pnl(self) -> float:
        """Get daily profit and loss
        
        Returns:
            float: Daily profit and loss
        """
        today = datetime.now().date()
        
        # Calculate profit from closed orders today
        closed_profit = sum(
            order.get("profit", 0.0)
            for order in self.order_history
            if order.get("close_time") and datetime.fromisoformat(order.get("close_time")).date() == today
        )
        
        # Calculate profit from open orders
        open_profit = sum(order.profit for order in self.active_orders.values())
        
        return closed_profit + open_profit
    
    def get_trading_stats(self) -> Dict:
        """Get trading statistics
        
        Returns:
            Dict: Trading statistics
        """
        stats = {
            "total_trades": len(self.order_history),
            "active_trades": len(self.active_orders),
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_profit": 0.0,
            "total_loss": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "max_win": 0.0,
            "max_loss": 0.0,
            "daily_pnl": self.get_daily_pnl()
        }
        
        # Calculate statistics from order history
        wins = []
        losses = []
        
        for order in self.order_history:
            profit = order.get("profit", 0.0)
            
            if profit > 0:
                wins.append(profit)
                stats["win_count"] += 1
                stats["total_profit"] += profit
                stats["max_win"] = max(stats["max_win"], profit)
            elif profit < 0:
                losses.append(profit)
                stats["loss_count"] += 1
                stats["total_loss"] += abs(profit)
                stats["max_loss"] = max(stats["max_loss"], abs(profit))
        
        # Calculate win rate
        if stats["win_count"] + stats["loss_count"] > 0:
            stats["win_rate"] = stats["win_count"] / (stats["win_count"] + stats["loss_count"]) * 100
            
        # Calculate profit factor
        if stats["total_loss"] > 0:
            stats["profit_factor"] = stats["total_profit"] / stats["total_loss"]
            
        # Calculate average win and loss
        if wins:
            stats["average_win"] = sum(wins) / len(wins)
            
        if losses:
            stats["average_loss"] = sum(abs(l) for l in losses) / len(losses)
            
        return stats

# Example usage
if __name__ == "__main__":
    # Create live trading instance
    live_trading = LiveTrading()
    
    # Connect to broker
    if live_trading.connect():
        try:
            # Get account info
            account_info = live_trading.get_account_info()
            print("Account Info:")
            print(json.dumps(account_info, indent=2))
            
            # Place a test order
            test_order = Order(
                symbol="EURUSD",
                order_type=OrderType.MARKET,
                direction=OrderDirection.BUY,
                volume=0.01,
                stop_loss=1.0900,
                take_profit=1.1100,
                comment="Test order",
                strategy="Test"
            )
            
            success, order_id, error = live_trading.place_order(test_order)
            
            if success:
                print(f"Order placed: {order_id}")
                
                # Wait for a while
                time.sleep(5)
                
                # Get positions
                positions = live_trading.get_positions()
                print("\nPositions:")
                print(json.dumps(positions, indent=2))
                
                # Close the order
                success, error = live_trading.close_order(order_id)
                
                if success:
                    print(f"Order closed: {order_id}")
                else:
                    print(f"Error closing order: {error}")
            else:
                print(f"Error placing order: {error}")
                
            # Get trading stats
            stats = live_trading.get_trading_stats()
            print("\nTrading Stats:")
            print(json.dumps(stats, indent=2))
        finally:
            # Disconnect from broker
            live_trading.disconnect()
            
            # Stop update thread
            live_trading.stop_update_thread()
    else:
        print("Failed to connect to broker")