# risk_auditor.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import os

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('risk_auditor')

class RiskAuditor(BaseAgent):
    """Agent specialized in risk management and trade vetting"""
    
    def __init__(self, agent_id: str = "risk_auditor", config: Dict[str, Any] = None):
        """Initialize the risk auditor agent
        
        Args:
            agent_id (str, optional): Agent identifier. Defaults to "risk_auditor".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id, "guard", config)
        
        # Default risk thresholds
        self.risk_thresholds = {
            "max_position_size": 0.05,  # 5% of account
            "max_daily_drawdown": 0.03,  # 3% max daily drawdown
            "max_open_trades": 5,  # Maximum concurrent open trades
            "min_risk_reward": 1.5,  # Minimum risk-reward ratio
            "max_correlated_exposure": 0.1  # 10% max exposure to correlated assets
        }
        
        # Override with config if provided
        if config and 'risk_thresholds' in config:
            self.risk_thresholds.update(config['risk_thresholds'])
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate trade risk and potentially veto risky trades
        
        Args:
            context (Dict[str, Any]): Trading context with market data and account info
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Default response - neutral with no veto
        proposal = {
            "action": "hold",
            "confidence": 50,
            "reason": "No risk concerns identified",
            "veto": False,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if we have the required data
        if not context:
            return proposal
        
        # Extract relevant data
        account_info = context.get('account_info', {})
        trade_info = context.get('trade_info', {})
        market_data = context.get('market_data', {})
        open_trades = context.get('open_trades', [])
        daily_pnl = context.get('daily_pnl', 0)
        
        # Risk checks
        risk_violations = []
        
        # 1. Check position size
        account_balance = account_info.get('balance', 0)
        position_size = trade_info.get('position_size', 0)
        
        if account_balance > 0 and position_size > 0:
            position_ratio = position_size / account_balance
            if position_ratio > self.risk_thresholds['max_position_size']:
                risk_violations.append(f"Position size ({position_ratio:.1%}) exceeds maximum ({self.risk_thresholds['max_position_size']:.1%})")
        
        # 2. Check daily drawdown
        if account_balance > 0 and daily_pnl < 0:
            daily_drawdown = abs(daily_pnl) / account_balance
            if daily_drawdown > self.risk_thresholds['max_daily_drawdown']:
                risk_violations.append(f"Daily drawdown ({daily_drawdown:.1%}) exceeds maximum ({self.risk_thresholds['max_daily_drawdown']:.1%})")
        
        # 3. Check number of open trades
        if len(open_trades) >= self.risk_thresholds['max_open_trades']:
            risk_violations.append(f"Too many open trades ({len(open_trades)}/{self.risk_thresholds['max_open_trades']})")
        
        # 4. Check risk-reward ratio
        entry_price = trade_info.get('entry_price', 0)
        stop_loss = trade_info.get('stop_loss', 0)
        take_profit = trade_info.get('take_profit', 0)
        
        if entry_price > 0 and stop_loss > 0 and take_profit > 0:
            # Calculate risk-reward ratio
            if trade_info.get('direction', '').lower() == 'buy':
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:  # sell
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            if risk > 0 and reward > 0:
                risk_reward_ratio = reward / risk
                if risk_reward_ratio < self.risk_thresholds['min_risk_reward']:
                    risk_violations.append(f"Risk-reward ratio ({risk_reward_ratio:.2f}) below minimum ({self.risk_thresholds['min_risk_reward']:.2f})")
        
        # 5. Check for correlated exposure
        symbol = trade_info.get('symbol', '')
        correlated_exposure = self.calculate_correlated_exposure(symbol, open_trades)
        
        if correlated_exposure > self.risk_thresholds['max_correlated_exposure']:
            risk_violations.append(f"Correlated exposure ({correlated_exposure:.1%}) exceeds maximum ({self.risk_thresholds['max_correlated_exposure']:.1%})")
        
        # Determine if veto is needed
        if risk_violations:
            proposal["veto"] = True
            proposal["action"] = "hold"  # Override to hold
            proposal["confidence"] = 100  # High confidence in the veto
            proposal["reason"] = "Risk violations: " + "; ".join(risk_violations)
        
        return proposal
    
    def calculate_correlated_exposure(self, symbol: str, open_trades: List[Dict[str, Any]]) -> float:
        """Calculate exposure to correlated assets
        
        Args:
            symbol (str): Symbol being traded
            open_trades (List[Dict[str, Any]]): Currently open trades
            
        Returns:
            float: Correlated exposure as a ratio of total exposure
        """
        # Simple implementation - just check for same currency pairs
        if not symbol or len(symbol) < 6:
            return 0
        
        # Extract currencies from forex pair (e.g., EURUSD -> EUR, USD)
        base_currency = symbol[:3]
        quote_currency = symbol[3:6]
        
        # Count trades with the same currencies
        correlated_trades = 0
        total_trades = len(open_trades)
        
        for trade in open_trades:
            trade_symbol = trade.get('symbol', '')
            if not trade_symbol or len(trade_symbol) < 6:
                continue
            
            trade_base = trade_symbol[:3]
            trade_quote = trade_symbol[3:6]
            
            # Check if currencies overlap
            if trade_base == base_currency or trade_base == quote_currency or \
               trade_quote == base_currency or trade_quote == quote_currency:
                correlated_trades += 1
        
        # Calculate exposure ratio
        return correlated_trades / max(1, total_trades)