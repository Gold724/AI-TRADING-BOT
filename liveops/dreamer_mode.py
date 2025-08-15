#!/usr/bin/env python3

import os
import json
import logging
import random
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger("trae.liveops.dreamer")

class DreamerMode:
    """Dreamer Mode for simulating trades with fake responses.
    
    This class provides functionality for simulating trades without actually executing them.
    It can be used for backtests, paper trades, or running overnight simulations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Dreamer Mode.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.simulation_data_dir = os.path.join("data", "simulations")
        os.makedirs(self.simulation_data_dir, exist_ok=True)
        
        # Initialize simulation state
        self.simulation_id = f"sim_{int(time.time())}"
        self.simulation_start_time = datetime.now()
        self.simulated_trades = []
        self.simulated_balances = {}
        self.simulated_positions = {}
        
        # Load market data if available
        self.market_data = self._load_market_data()
        
        logger.info(f"Dreamer Mode initialized with simulation ID: {self.simulation_id}")
    
    def _load_market_data(self) -> Dict[str, Any]:
        """Load market data for more realistic simulations.
        
        Returns:
            Dict[str, Any]: Market data dictionary
        """
        market_data = {}
        market_data_path = os.path.join("data", "market_data.json")
        
        if os.path.exists(market_data_path):
            try:
                with open(market_data_path, "r") as f:
                    market_data = json.load(f)
                logger.info(f"Loaded market data from {market_data_path}")
            except Exception as e:
                logger.warning(f"Failed to load market data: {e}")
        else:
            logger.info("No market data found, using random price movements")
            # Create basic market data with current prices
            symbols = self.config.get("governance", {}).get("allowed_symbols", [])
            market_data = {"prices": {}}
            
            # Generate random prices for allowed symbols
            for symbol in symbols:
                if "USD" in symbol:
                    if symbol.startswith("USD"):
                        # USDXXX pairs typically range from 0.5 to 1.5
                        market_data["prices"][symbol] = round(random.uniform(0.5, 1.5), 5)
                    else:
                        # XXXUSD pairs typically range from 0.8 to 2.0
                        market_data["prices"][symbol] = round(random.uniform(0.8, 2.0), 5)
                elif "JPY" in symbol:
                    # JPY pairs typically have larger values (80-150)
                    market_data["prices"][symbol] = round(random.uniform(80, 150), 3)
                elif symbol == "XAUUSD":
                    # Gold typically ranges from 1500 to 2000
                    market_data["prices"][symbol] = round(random.uniform(1500, 2000), 2)
                else:
                    # Default range for other pairs
                    market_data["prices"][symbol] = round(random.uniform(1.0, 1.5), 5)
        
        return market_data
    
    def simulate_trade(self, 
                       account_id: str, 
                       broker: str, 
                       symbol: str, 
                       action: str, 
                       lot_size: float, 
                       take_profit: Optional[float] = None, 
                       stop_loss: Optional[float] = None) -> Dict[str, Any]:
        """Simulate a trade execution.
        
        Args:
            account_id (str): Account ID
            broker (str): Broker name
            symbol (str): Trading symbol
            action (str): Trade action (BUY/SELL)
            lot_size (float): Lot size
            take_profit (Optional[float]): Take profit level in pips
            stop_loss (Optional[float]): Stop loss level in pips
            
        Returns:
            Dict[str, Any]: Simulated trade execution result
        """
        # Initialize account if not exists
        if account_id not in self.simulated_balances:
            self.simulated_balances[account_id] = 10000.0  # Default balance
            self.simulated_positions[account_id] = []
        
        # Get current price for the symbol
        current_price = self._get_current_price(symbol)
        
        # Calculate trade details
        trade_id = f"T{int(time.time())}{random.randint(1000, 9999)}"
        execution_time = datetime.now()
        
        # Calculate pip value and position size
        pip_value = self._calculate_pip_value(symbol, lot_size)
        position_size = lot_size * 100000  # Standard lot is 100,000 units
        
        # Calculate take profit and stop loss levels
        tp_price = None
        sl_price = None
        
        if take_profit is not None:
            tp_pips = take_profit
            if action == "BUY":
                tp_price = current_price + (tp_pips * self._get_pip_size(symbol))
            else:  # SELL
                tp_price = current_price - (tp_pips * self._get_pip_size(symbol))
        
        if stop_loss is not None:
            sl_pips = stop_loss
            if action == "BUY":
                sl_price = current_price - (sl_pips * self._get_pip_size(symbol))
            else:  # SELL
                sl_price = current_price + (sl_pips * self._get_pip_size(symbol))
        
        # Create simulated trade
        trade = {
            "trade_id": trade_id,
            "account_id": account_id,
            "broker": broker,
            "symbol": symbol,
            "action": action,
            "lot_size": lot_size,
            "position_size": position_size,
            "open_price": current_price,
            "take_profit": tp_price,
            "stop_loss": sl_price,
            "open_time": execution_time.isoformat(),
            "status": "OPEN",
            "pip_value": pip_value,
            "simulated": True
        }
        
        # Add to simulated trades and positions
        self.simulated_trades.append(trade)
        self.simulated_positions[account_id].append(trade)
        
        # Save simulation state
        self._save_simulation_state()
        
        # Create execution result
        result = {
            "success": True,
            "trade_id": trade_id,
            "account_id": account_id,
            "broker": broker,
            "symbol": symbol,
            "action": action,
            "lot_size": lot_size,
            "open_price": current_price,
            "execution_time": execution_time.isoformat(),
            "message": "Trade executed successfully (SIMULATION)",
            "simulated": True
        }
        
        logger.info(f"Simulated {action} trade for {symbol} at {current_price} (ID: {trade_id})")
        return result
    
    def _get_current_price(self, symbol: str) -> float:
        """Get the current price for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            float: Current price
        """
        # Check if we have market data for this symbol
        if "prices" in self.market_data and symbol in self.market_data["prices"]:
            base_price = self.market_data["prices"][symbol]
            
            # Add some random movement (0.1% - 0.5%)
            movement_percent = random.uniform(0.001, 0.005)
            movement_direction = random.choice([-1, 1])
            movement = base_price * movement_percent * movement_direction
            
            # Update the price in market data
            new_price = base_price + movement
            self.market_data["prices"][symbol] = new_price
            
            return new_price
        else:
            # Generate a random price if no market data available
            if "JPY" in symbol:
                return round(random.uniform(80, 150), 3)
            elif symbol == "XAUUSD":
                return round(random.uniform(1500, 2000), 2)
            else:
                return round(random.uniform(1.0, 1.5), 5)
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get the pip size for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            float: Pip size
        """
        if "JPY" in symbol:
            return 0.01  # 2 decimal places for JPY pairs
        else:
            return 0.0001  # 4 decimal places for other pairs
    
    def _calculate_pip_value(self, symbol: str, lot_size: float) -> float:
        """Calculate the pip value for a symbol and lot size.
        
        Args:
            symbol (str): Trading symbol
            lot_size (float): Lot size
            
        Returns:
            float: Pip value in account currency
        """
        # Standard calculation (simplified)
        if "USD" in symbol:
            if symbol.endswith("USD"):
                # For pairs ending with USD, pip value is 10 USD per standard lot
                return 10.0 * lot_size
            else:
                # For pairs starting with USD, pip value depends on the exchange rate
                price = self._get_current_price(symbol)
                return 10.0 * lot_size / price
        elif "JPY" in symbol:
            # For JPY pairs, pip value is approximately 10 USD per standard lot
            return 10.0 * lot_size
        else:
            # Default pip value for other pairs
            return 10.0 * lot_size
    
    def update_simulation(self) -> None:
        """Update the simulation state.
        
        This method simulates market movements and updates open positions.
        """
        current_time = datetime.now()
        
        # Update all open positions
        for account_id, positions in self.simulated_positions.items():
            for i, position in enumerate(positions):
                if position["status"] == "OPEN":
                    # Get updated price
                    current_price = self._get_current_price(position["symbol"])
                    
                    # Calculate profit/loss
                    pip_size = self._get_pip_size(position["symbol"])
                    if position["action"] == "BUY":
                        pips_gained = (current_price - position["open_price"]) / pip_size
                    else:  # SELL
                        pips_gained = (position["open_price"] - current_price) / pip_size
                    
                    profit = pips_gained * position["pip_value"]
                    
                    # Update position with current price and profit
                    position["current_price"] = current_price
                    position["profit"] = profit
                    position["pips"] = pips_gained
                    position["last_updated"] = current_time.isoformat()
                    
                    # Check if take profit or stop loss hit
                    if position["take_profit"] is not None:
                        if (position["action"] == "BUY" and current_price >= position["take_profit"]) or \
                           (position["action"] == "SELL" and current_price <= position["take_profit"]):
                            # Take profit hit
                            position["status"] = "CLOSED"
                            position["close_price"] = position["take_profit"]
                            position["close_time"] = current_time.isoformat()
                            position["close_reason"] = "TAKE_PROFIT"
                            
                            # Recalculate final profit
                            if position["action"] == "BUY":
                                pips_gained = (position["take_profit"] - position["open_price"]) / pip_size
                            else:  # SELL
                                pips_gained = (position["open_price"] - position["take_profit"]) / pip_size
                            
                            position["profit"] = pips_gained * position["pip_value"]
                            position["pips"] = pips_gained
                            
                            # Update account balance
                            self.simulated_balances[account_id] += position["profit"]
                            
                            logger.info(f"Take profit hit for {position['symbol']} trade {position['trade_id']} with profit {position['profit']:.2f}")
                    
                    if position["status"] == "OPEN" and position["stop_loss"] is not None:
                        if (position["action"] == "BUY" and current_price <= position["stop_loss"]) or \
                           (position["action"] == "SELL" and current_price >= position["stop_loss"]):
                            # Stop loss hit
                            position["status"] = "CLOSED"
                            position["close_price"] = position["stop_loss"]
                            position["close_time"] = current_time.isoformat()
                            position["close_reason"] = "STOP_LOSS"
                            
                            # Recalculate final profit (loss)
                            if position["action"] == "BUY":
                                pips_gained = (position["stop_loss"] - position["open_price"]) / pip_size
                            else:  # SELL
                                pips_gained = (position["open_price"] - position["stop_loss"]) / pip_size
                            
                            position["profit"] = pips_gained * position["pip_value"]
                            position["pips"] = pips_gained
                            
                            # Update account balance
                            self.simulated_balances[account_id] += position["profit"]
                            
                            logger.info(f"Stop loss hit for {position['symbol']} trade {position['trade_id']} with loss {position['profit']:.2f}")
        
        # Save updated simulation state
        self._save_simulation_state()
    
    def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get a summary of an account's performance in the simulation.
        
        Args:
            account_id (str): Account ID
            
        Returns:
            Dict[str, Any]: Account summary
        """
        if account_id not in self.simulated_balances:
            return {
                "account_id": account_id,
                "balance": 0.0,
                "equity": 0.0,
                "open_positions": 0,
                "closed_positions": 0,
                "profit": 0.0,
                "simulated": True
            }
        
        # Calculate account metrics
        balance = self.simulated_balances[account_id]
        open_positions = [p for p in self.simulated_positions[account_id] if p["status"] == "OPEN"]
        closed_positions = [p for p in self.simulated_positions[account_id] if p["status"] == "CLOSED"]
        
        # Calculate floating profit/loss
        floating_pnl = sum(p.get("profit", 0.0) for p in open_positions)
        
        # Calculate equity
        equity = balance + floating_pnl
        
        # Calculate total profit from closed positions
        closed_profit = sum(p.get("profit", 0.0) for p in closed_positions)
        
        return {
            "account_id": account_id,
            "balance": balance,
            "equity": equity,
            "open_positions": len(open_positions),
            "closed_positions": len(closed_positions),
            "floating_pnl": floating_pnl,
            "closed_profit": closed_profit,
            "total_profit": floating_pnl + closed_profit,
            "simulated": True
        }
    
    def get_open_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get open positions for an account.
        
        Args:
            account_id (str): Account ID
            
        Returns:
            List[Dict[str, Any]]: List of open positions
        """
        if account_id not in self.simulated_positions:
            return []
        
        return [p for p in self.simulated_positions[account_id] if p["status"] == "OPEN"]
    
    def get_trade_history(self, account_id: str) -> List[Dict[str, Any]]:
        """Get trade history for an account.
        
        Args:
            account_id (str): Account ID
            
        Returns:
            List[Dict[str, Any]]: List of trades
        """
        if account_id not in self.simulated_positions:
            return []
        
        return self.simulated_positions[account_id]
    
    def close_position(self, account_id: str, trade_id: str) -> Dict[str, Any]:
        """Close a position manually.
        
        Args:
            account_id (str): Account ID
            trade_id (str): Trade ID
            
        Returns:
            Dict[str, Any]: Close position result
        """
        if account_id not in self.simulated_positions:
            return {
                "success": False,
                "message": f"Account {account_id} not found",
                "simulated": True
            }
        
        # Find the position
        position = None
        for p in self.simulated_positions[account_id]:
            if p["trade_id"] == trade_id and p["status"] == "OPEN":
                position = p
                break
        
        if position is None:
            return {
                "success": False,
                "message": f"Open position with ID {trade_id} not found",
                "simulated": True
            }
        
        # Get current price
        current_price = self._get_current_price(position["symbol"])
        current_time = datetime.now()
        
        # Calculate profit/loss
        pip_size = self._get_pip_size(position["symbol"])
        if position["action"] == "BUY":
            pips_gained = (current_price - position["open_price"]) / pip_size
        else:  # SELL
            pips_gained = (position["open_price"] - current_price) / pip_size
        
        profit = pips_gained * position["pip_value"]
        
        # Update position
        position["status"] = "CLOSED"
        position["close_price"] = current_price
        position["close_time"] = current_time.isoformat()
        position["close_reason"] = "MANUAL"
        position["profit"] = profit
        position["pips"] = pips_gained
        
        # Update account balance
        self.simulated_balances[account_id] += profit
        
        # Save simulation state
        self._save_simulation_state()
        
        logger.info(f"Manually closed position {trade_id} with profit {profit:.2f}")
        
        return {
            "success": True,
            "trade_id": trade_id,
            "account_id": account_id,
            "symbol": position["symbol"],
            "action": position["action"],
            "open_price": position["open_price"],
            "close_price": current_price,
            "profit": profit,
            "pips": pips_gained,
            "message": "Position closed successfully (SIMULATION)",
            "simulated": True
        }
    
    def _save_simulation_state(self) -> None:
        """Save the current simulation state to disk."""
        try:
            simulation_data = {
                "simulation_id": self.simulation_id,
                "start_time": self.simulation_start_time.isoformat(),
                "last_updated": datetime.now().isoformat(),
                "balances": self.simulated_balances,
                "trades": self.simulated_trades,
                "positions": self.simulated_positions,
                "market_data": self.market_data
            }
            
            # Save to file
            file_path = os.path.join(self.simulation_data_dir, f"{self.simulation_id}.json")
            with open(file_path, "w") as f:
                json.dump(simulation_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving simulation state: {e}")
    
    def load_simulation(self, simulation_id: str) -> bool:
        """Load a previous simulation.
        
        Args:
            simulation_id (str): Simulation ID to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = os.path.join(self.simulation_data_dir, f"{simulation_id}.json")
            
            if not os.path.exists(file_path):
                logger.error(f"Simulation file {file_path} not found")
                return False
            
            with open(file_path, "r") as f:
                simulation_data = json.load(f)
            
            # Load simulation state
            self.simulation_id = simulation_data["simulation_id"]
            self.simulation_start_time = datetime.fromisoformat(simulation_data["start_time"])
            self.simulated_balances = simulation_data["balances"]
            self.simulated_trades = simulation_data["trades"]
            self.simulated_positions = simulation_data["positions"]
            self.market_data = simulation_data["market_data"]
            
            logger.info(f"Loaded simulation {simulation_id}")
            return True
        except Exception as e:
            logger.error(f"Error loading simulation: {e}")
            return False
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current simulation.
        
        Returns:
            Dict[str, Any]: Simulation summary
        """
        current_time = datetime.now()
        duration = current_time - self.simulation_start_time
        
        # Calculate overall metrics
        total_trades = len(self.simulated_trades)
        open_trades = sum(1 for account in self.simulated_positions.values() 
                         for p in account if p["status"] == "OPEN")
        closed_trades = sum(1 for account in self.simulated_positions.values() 
                           for p in account if p["status"] == "CLOSED")
        
        # Calculate profit metrics
        total_profit = sum(self.simulated_balances.get(account_id, 0) - 10000.0 
                          for account_id in self.simulated_balances)
        
        # Calculate win/loss metrics
        winning_trades = sum(1 for account in self.simulated_positions.values() 
                            for p in account if p["status"] == "CLOSED" and p.get("profit", 0) > 0)
        losing_trades = sum(1 for account in self.simulated_positions.values() 
                           for p in account if p["status"] == "CLOSED" and p.get("profit", 0) <= 0)
        
        win_rate = winning_trades / closed_trades if closed_trades > 0 else 0
        
        return {
            "simulation_id": self.simulation_id,
            "start_time": self.simulation_start_time.isoformat(),
            "current_time": current_time.isoformat(),
            "duration": str(duration),
            "total_trades": total_trades,
            "open_trades": open_trades,
            "closed_trades": closed_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "accounts": len(self.simulated_balances),
            "simulated": True
        }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example configuration
    config = {
        "governance": {
            "allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        }
    }
    
    # Initialize dreamer mode
    dreamer = DreamerMode(config)
    
    # Simulate some trades
    dreamer.simulate_trade("demo_account", "exness", "EURUSD", "BUY", 0.1, 20, 10)
    dreamer.simulate_trade("demo_account", "exness", "GBPUSD", "SELL", 0.2, 15, 12)
    
    # Update simulation a few times
    for _ in range(5):
        dreamer.update_simulation()
        time.sleep(1)
    
    # Get account summary
    summary = dreamer.get_account_summary("demo_account")
    print(json.dumps(summary, indent=2))
    
    # Get simulation summary
    sim_summary = dreamer.get_simulation_summary()
    print(json.dumps(sim_summary, indent=2))