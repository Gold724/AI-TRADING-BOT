from AlgorithmImports import *
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
import math

@dataclass
class RiskMetrics:
    """Container for risk assessment metrics"""
    var_1day: float  # 1-day Value at Risk
    var_5day: float  # 5-day Value at Risk
    expected_shortfall: float  # Expected Shortfall (CVaR)
    volatility: float  # Annualized volatility
    sharpe_ratio: float  # Risk-adjusted return
    max_drawdown: float  # Maximum drawdown
    risk_score: float  # Overall risk score (0-1)
    position_heat: float  # Position concentration risk
    correlation_risk: float  # Market correlation risk

@dataclass
class DynamicStopLoss:
    """Container for dynamic stop-loss parameters"""
    atr_multiplier: float
    volatility_adjustment: float
    time_decay_factor: float
    profit_protection_level: float
    maximum_loss_pct: float
    trailing_activation_pct: float

@dataclass
class PositionRisk:
    """Container for individual position risk metrics"""
    symbol: Symbol
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    position_value: float
    var_contribution: float
    stop_loss_price: float
    risk_reward_ratio: float
    time_in_position: timedelta
    heat_score: float  # Position concentration score

class AdvancedRiskManager:
    """Advanced risk management system with VaR and dynamic stops"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.returns_history = []
        self.position_history = []
        self.risk_metrics_history = []
        
        # Risk parameters
        self.confidence_level = 0.95  # 95% confidence for VaR
        self.var_lookback_days = 252  # 1 year of data
        self.max_portfolio_var = 0.02  # 2% daily VaR limit
        self.max_position_heat = 0.15  # 15% max position concentration
        self.emergency_stop_loss = 0.05  # 5% emergency stop
        
        # Dynamic stop-loss parameters
        self.base_atr_multiplier = 2.0
        self.min_atr_multiplier = 1.5
        self.max_atr_multiplier = 3.5
        self.volatility_lookback = 20
        
        # Risk state tracking
        self.current_var = 0
        self.current_risk_score = 0
        self.last_risk_update = None
        self.risk_alerts = []
        
        self.algorithm.Debug("🛡️ Advanced Risk Manager initialized")
    
    def update_risk_metrics(self, current_time: datetime, portfolio_value: float):
        """Update comprehensive risk metrics"""
        try:
            # Calculate portfolio returns
            if len(self.returns_history) > 0:
                last_value = self.returns_history[-1]['portfolio_value']
                daily_return = (portfolio_value - last_value) / last_value
            else:
                daily_return = 0
            
            # Store return data
            return_data = {
                'timestamp': current_time,
                'portfolio_value': portfolio_value,
                'daily_return': daily_return
            }
            self.returns_history.append(return_data)
            
            # Keep only required history
            if len(self.returns_history) > self.var_lookback_days:
                self.returns_history = self.returns_history[-self.var_lookback_days:]
            
            # Calculate VaR if we have sufficient data
            if len(self.returns_history) >= 30:  # Minimum 30 days
                risk_metrics = self.calculate_var_metrics()
                self.current_var = risk_metrics.var_1day
                self.current_risk_score = risk_metrics.risk_score
                
                # Store risk metrics
                self.risk_metrics_history.append({
                    'timestamp': current_time,
                    'metrics': risk_metrics
                })
                
                # Keep last 100 risk metric records
                if len(self.risk_metrics_history) > 100:
                    self.risk_metrics_history = self.risk_metrics_history[-100:]
                
                self.last_risk_update = current_time
                
                # Check for risk alerts
                self.check_risk_alerts(risk_metrics)
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Risk metrics update failed: {e}")
    
    def calculate_var_metrics(self) -> RiskMetrics:
        """Calculate comprehensive VaR and risk metrics"""
        try:
            # Extract returns
            returns = [r['daily_return'] for r in self.returns_history if r['daily_return'] != 0]
            
            if len(returns) < 10:
                return self.get_default_risk_metrics()
            
            returns_array = np.array(returns)
            
            # Calculate VaR using multiple methods
            var_1day_historical = self.calculate_historical_var(returns_array, self.confidence_level)
            var_1day_parametric = self.calculate_parametric_var(returns_array, self.confidence_level)
            var_1day_monte_carlo = self.calculate_monte_carlo_var(returns_array, self.confidence_level)
            
            # Use average of methods for robustness
            var_1day = np.mean([var_1day_historical, var_1day_parametric, var_1day_monte_carlo])
            var_5day = var_1day * np.sqrt(5)  # Scale to 5-day
            
            # Calculate Expected Shortfall (CVaR)
            expected_shortfall = self.calculate_expected_shortfall(returns_array, self.confidence_level)
            
            # Calculate other risk metrics
            volatility = np.std(returns_array) * np.sqrt(252)  # Annualized
            mean_return = np.mean(returns_array) * 252  # Annualized
            sharpe_ratio = mean_return / volatility if volatility > 0 else 0
            
            # Calculate maximum drawdown
            cumulative_returns = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            
            # Calculate position heat (concentration risk)
            position_heat = self.calculate_position_heat()
            
            # Calculate correlation risk
            correlation_risk = self.calculate_correlation_risk()
            
            # Calculate overall risk score (0-1, higher is riskier)
            risk_score = self.calculate_risk_score(
                var_1day, volatility, max_drawdown, position_heat, correlation_risk
            )
            
            return RiskMetrics(
                var_1day=abs(var_1day),
                var_5day=abs(var_5day),
                expected_shortfall=abs(expected_shortfall),
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=abs(max_drawdown),
                risk_score=risk_score,
                position_heat=position_heat,
                correlation_risk=correlation_risk
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ VaR calculation failed: {e}")
            return self.get_default_risk_metrics()
    
    def calculate_historical_var(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate VaR using historical simulation"""
        percentile = (1 - confidence) * 100
        return np.percentile(returns, percentile)
    
    def calculate_parametric_var(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate VaR using parametric method (normal distribution)"""
        mean = np.mean(returns)
        std = np.std(returns)
        z_score = stats.norm.ppf(1 - confidence)
        return mean + z_score * std
    
    def calculate_monte_carlo_var(self, returns: np.ndarray, confidence: float, simulations: int = 10000) -> float:
        """Calculate VaR using Monte Carlo simulation"""
        try:
            mean = np.mean(returns)
            std = np.std(returns)
            
            # Generate random scenarios
            simulated_returns = np.random.normal(mean, std, simulations)
            
            # Calculate VaR
            percentile = (1 - confidence) * 100
            return np.percentile(simulated_returns, percentile)
            
        except Exception:
            # Fallback to parametric method
            return self.calculate_parametric_var(returns, confidence)
    
    def calculate_expected_shortfall(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        var_threshold = self.calculate_historical_var(returns, confidence)
        tail_losses = returns[returns <= var_threshold]
        return np.mean(tail_losses) if len(tail_losses) > 0 else var_threshold
    
    def calculate_position_heat(self) -> float:
        """Calculate position concentration risk"""
        try:
            total_value = abs(self.algorithm.Portfolio.TotalPortfolioValue)
            if total_value == 0:
                return 0
            
            max_position_value = 0
            for symbol in self.algorithm.Portfolio.Keys:
                position_value = abs(self.algorithm.Portfolio[symbol].HoldingsValue)
                max_position_value = max(max_position_value, position_value)
            
            return max_position_value / total_value
            
        except Exception:
            return 0
    
    def calculate_correlation_risk(self) -> float:
        """Calculate market correlation risk (simplified)"""
        # Placeholder for correlation analysis
        # In production, this would analyze correlations with market indices
        return 0.5  # Default moderate correlation risk
    
    def calculate_risk_score(self, var: float, volatility: float, max_dd: float, 
                           position_heat: float, correlation_risk: float) -> float:
        """Calculate overall risk score (0-1)"""
        try:
            # Normalize components to 0-1 scale
            var_score = min(1.0, abs(var) / 0.05)  # 5% daily loss as max
            vol_score = min(1.0, volatility / 0.5)  # 50% annual vol as max
            dd_score = min(1.0, abs(max_dd) / 0.3)  # 30% drawdown as max
            heat_score = min(1.0, position_heat / 0.2)  # 20% concentration as max
            corr_score = correlation_risk  # Already 0-1
            
            # Weighted average
            weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # VaR, Vol, DD, Heat, Corr
            scores = [var_score, vol_score, dd_score, heat_score, corr_score]
            
            return sum(w * s for w, s in zip(weights, scores))
            
        except Exception:
            return 0.5  # Default moderate risk
    
    def get_default_risk_metrics(self) -> RiskMetrics:
        """Return default risk metrics when calculation fails"""
        return RiskMetrics(
            var_1day=0.01,
            var_5day=0.02,
            expected_shortfall=0.015,
            volatility=0.2,
            sharpe_ratio=0,
            max_drawdown=0,
            risk_score=0.5,
            position_heat=0,
            correlation_risk=0.5
        )
    
    def calculate_dynamic_stop_loss(self, symbol: Symbol, entry_price: float, 
                                  direction: int, atr_value: float) -> DynamicStopLoss:
        """Calculate dynamic stop-loss parameters"""
        try:
            # Base ATR multiplier
            base_multiplier = self.base_atr_multiplier
            
            # Adjust for current volatility regime
            if len(self.returns_history) >= self.volatility_lookback:
                recent_returns = [r['daily_return'] for r in self.returns_history[-self.volatility_lookback:]]
                current_vol = np.std(recent_returns) * np.sqrt(252)
                
                # Historical average volatility
                all_returns = [r['daily_return'] for r in self.returns_history]
                avg_vol = np.std(all_returns) * np.sqrt(252)
                
                # Adjust multiplier based on volatility regime
                vol_ratio = current_vol / max(0.01, avg_vol)
                if vol_ratio > 1.5:  # High volatility
                    base_multiplier *= 1.3
                elif vol_ratio < 0.7:  # Low volatility
                    base_multiplier *= 0.8
            
            # Adjust for risk score
            if hasattr(self, 'current_risk_score'):
                risk_adjustment = 1 + (self.current_risk_score - 0.5) * 0.4
                base_multiplier *= risk_adjustment
            
            # Ensure within bounds
            atr_multiplier = max(self.min_atr_multiplier, 
                               min(self.max_atr_multiplier, base_multiplier))
            
            # Calculate other parameters
            volatility_adjustment = min(2.0, max(0.5, atr_multiplier / self.base_atr_multiplier))
            time_decay_factor = 0.95  # Tighten stops over time
            profit_protection_level = 0.5  # Protect 50% of profits
            maximum_loss_pct = min(0.03, self.current_var * 2)  # Max 3% or 2x VaR
            trailing_activation_pct = atr_value * atr_multiplier * 1.5  # Activate trailing
            
            return DynamicStopLoss(
                atr_multiplier=atr_multiplier,
                volatility_adjustment=volatility_adjustment,
                time_decay_factor=time_decay_factor,
                profit_protection_level=profit_protection_level,
                maximum_loss_pct=maximum_loss_pct,
                trailing_activation_pct=trailing_activation_pct
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Dynamic stop-loss calculation failed: {e}")
            return DynamicStopLoss(
                atr_multiplier=self.base_atr_multiplier,
                volatility_adjustment=1.0,
                time_decay_factor=0.95,
                profit_protection_level=0.5,
                maximum_loss_pct=0.02,
                trailing_activation_pct=0.01
            )
    
    def check_position_risk(self, symbol: Symbol) -> PositionRisk:
        """Analyze risk for individual position"""
        try:
            position = self.algorithm.Portfolio[symbol]
            if position.Quantity == 0:
                return None
            
            current_price = self.algorithm.Securities[symbol].Price
            entry_price = position.AveragePrice
            unrealized_pnl = position.UnrealizedProfit
            position_value = abs(position.HoldingsValue)
            
            # Calculate VaR contribution (simplified)
            portfolio_value = abs(self.algorithm.Portfolio.TotalPortfolioValue)
            position_weight = position_value / max(1, portfolio_value)
            var_contribution = self.current_var * position_weight
            
            # Calculate heat score
            heat_score = position_weight
            
            # Estimate time in position
            time_in_position = timedelta(hours=1)  # Placeholder
            
            # Calculate risk-reward ratio
            if hasattr(position, 'stop_loss_price') and position.stop_loss_price:
                potential_loss = abs(current_price - position.stop_loss_price)
                potential_gain = abs(current_price - entry_price) * 2  # Assume 2:1 target
                risk_reward_ratio = potential_gain / max(0.01, potential_loss)
            else:
                risk_reward_ratio = 1.0
            
            return PositionRisk(
                symbol=symbol,
                quantity=position.Quantity,
                entry_price=entry_price,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                position_value=position_value,
                var_contribution=var_contribution,
                stop_loss_price=getattr(position, 'stop_loss_price', 0),
                risk_reward_ratio=risk_reward_ratio,
                time_in_position=time_in_position,
                heat_score=heat_score
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Position risk analysis failed: {e}")
            return None
    
    def check_risk_alerts(self, risk_metrics: RiskMetrics):
        """Check for risk threshold breaches and generate alerts"""
        alerts = []
        
        # VaR breach
        if risk_metrics.var_1day > self.max_portfolio_var:
            alerts.append({
                'type': 'VAR_BREACH',
                'severity': 'HIGH',
                'message': f'Daily VaR ({risk_metrics.var_1day:.2%}) exceeds limit ({self.max_portfolio_var:.2%})',
                'timestamp': self.algorithm.Time
            })
        
        # Position concentration
        if risk_metrics.position_heat > self.max_position_heat:
            alerts.append({
                'type': 'CONCENTRATION_RISK',
                'severity': 'MEDIUM',
                'message': f'Position concentration ({risk_metrics.position_heat:.2%}) exceeds limit ({self.max_position_heat:.2%})',
                'timestamp': self.algorithm.Time
            })
        
        # High overall risk score
        if risk_metrics.risk_score > 0.8:
            alerts.append({
                'type': 'HIGH_RISK_SCORE',
                'severity': 'MEDIUM',
                'message': f'Overall risk score ({risk_metrics.risk_score:.2f}) is elevated',
                'timestamp': self.algorithm.Time
            })
        
        # Large drawdown
        if risk_metrics.max_drawdown > 0.15:  # 15% drawdown
            alerts.append({
                'type': 'LARGE_DRAWDOWN',
                'severity': 'HIGH',
                'message': f'Maximum drawdown ({risk_metrics.max_drawdown:.2%}) is significant',
                'timestamp': self.algorithm.Time
            })
        
        # Store and log alerts
        for alert in alerts:
            self.risk_alerts.append(alert)
            severity_emoji = '🚨' if alert['severity'] == 'HIGH' else '⚠️'
            self.algorithm.Debug(f"{severity_emoji} RISK ALERT: {alert['message']}")
        
        # Keep only recent alerts
        cutoff_time = self.algorithm.Time - timedelta(days=7)
        self.risk_alerts = [a for a in self.risk_alerts if a['timestamp'] > cutoff_time]
    
    def should_reduce_position_size(self) -> Tuple[bool, float]:
        """Determine if position size should be reduced due to risk"""
        try:
            if self.current_risk_score > 0.7:
                # High risk - reduce position size
                reduction_factor = max(0.3, 1 - (self.current_risk_score - 0.7) * 2)
                return True, reduction_factor
            
            if self.current_var > self.max_portfolio_var * 0.8:
                # Approaching VaR limit - reduce size
                reduction_factor = max(0.5, 1 - (self.current_var / self.max_portfolio_var - 0.8) * 2.5)
                return True, reduction_factor
            
            return False, 1.0
            
        except Exception:
            return False, 1.0
    
    def get_risk_adjusted_position_size(self, base_size: int, signal_strength: float) -> int:
        """Calculate risk-adjusted position size"""
        try:
            # Check if size should be reduced
            should_reduce, reduction_factor = self.should_reduce_position_size()
            
            if should_reduce:
                adjusted_size = int(base_size * reduction_factor)
                self.algorithm.Debug(f"🛡️ Risk-adjusted position size: {base_size} → {adjusted_size} (factor: {reduction_factor:.2f})")
                return max(1, adjusted_size)
            
            return base_size
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Risk-adjusted sizing failed: {e}")
            return base_size
    
    def get_current_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary for logging/monitoring"""
        try:
            if len(self.risk_metrics_history) == 0:
                return {'status': 'insufficient_data'}
            
            latest_metrics = self.risk_metrics_history[-1]['metrics']
            
            return {
                'status': 'active',
                'var_1day': latest_metrics.var_1day,
                'var_5day': latest_metrics.var_5day,
                'risk_score': latest_metrics.risk_score,
                'position_heat': latest_metrics.position_heat,
                'volatility': latest_metrics.volatility,
                'sharpe_ratio': latest_metrics.sharpe_ratio,
                'max_drawdown': latest_metrics.max_drawdown,
                'active_alerts': len([a for a in self.risk_alerts if a['timestamp'] > self.algorithm.Time - timedelta(hours=24)]),
                'last_update': self.last_risk_update.isoformat() if self.last_risk_update else None
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}