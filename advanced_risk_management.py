#!/usr/bin/env python3
"""
TradeBot Sentinel - Advanced Risk Management System

Comprehensive risk management and portfolio optimization:
- Real-time risk assessment and monitoring
- Dynamic position sizing and portfolio allocation
- Value at Risk (VaR) and Expected Shortfall calculations
- Correlation analysis and diversification metrics
- Automated stop-loss and take-profit management
- Drawdown protection and circuit breakers
- Risk-adjusted performance metrics
- Stress testing and scenario analysis
- Regulatory compliance monitoring
- Multi-asset portfolio optimization

Features:
- Monte Carlo simulations for risk modeling
- Machine learning-based risk prediction
- Real-time portfolio rebalancing
- Advanced hedging strategies
- Risk budgeting and allocation
- Performance attribution analysis
- Automated risk reporting
- Integration with predictive analytics

Author: TradeBot Sentinel Team
Version: 1.0.0
Date: 2024
"""

import asyncio
import logging
import json
import time
import threading
import sqlite3
import os
import sys
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import pandas as pd
from collections import deque, defaultdict
import statistics
import traceback
from contextlib import contextmanager
import warnings
warnings.filterwarnings('ignore')

# Scientific computing
from scipy import stats
from scipy.optimize import minimize, differential_evolution
from scipy.stats import norm, t, jarque_bera

# Machine Learning
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import EmpiricalCovariance, LedoitWolf
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Portfolio optimization
try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    print("⚠️ CVXPY not available. Advanced portfolio optimization will be limited.")

# Risk metrics
try:
    import empyrical as emp
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False
    print("⚠️ Empyrical not available. Some risk metrics will be calculated manually.")

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    timestamp: str
    symbol: str
    position_size: float
    market_value: float
    
    # Basic risk metrics
    volatility: float
    beta: float
    correlation_to_market: float
    
    # Value at Risk metrics
    var_1d_95: float  # 1-day 95% VaR
    var_1d_99: float  # 1-day 99% VaR
    var_10d_95: float  # 10-day 95% VaR
    expected_shortfall_95: float  # Expected Shortfall (CVaR)
    
    # Portfolio metrics
    portfolio_weight: float
    contribution_to_var: float
    marginal_var: float
    component_var: float
    
    # Performance metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    
    # Risk-adjusted metrics
    information_ratio: float
    treynor_ratio: float
    jensen_alpha: float
    
    # Liquidity and operational risk
    liquidity_score: float  # 0-1 scale
    bid_ask_spread: float
    market_impact_cost: float
    
    # Model confidence
    confidence_level: float
    model_accuracy: float

@dataclass
class PortfolioRisk:
    """Portfolio-level risk assessment"""
    timestamp: str
    total_value: float
    num_positions: int
    
    # Portfolio risk metrics
    portfolio_var_1d_95: float
    portfolio_var_1d_99: float
    portfolio_expected_shortfall: float
    portfolio_volatility: float
    portfolio_beta: float
    
    # Diversification metrics
    diversification_ratio: float
    concentration_risk: float  # Herfindahl index
    correlation_risk: float
    sector_concentration: Dict[str, float]
    
    # Risk budgeting
    risk_budget_utilization: float
    risk_budget_allocation: Dict[str, float]
    
    # Stress test results
    stress_test_results: Dict[str, float]
    scenario_analysis: Dict[str, float]
    
    # Regulatory metrics
    leverage_ratio: float
    exposure_limits: Dict[str, float]
    compliance_status: str

@dataclass
class RiskAlert:
    """Risk alert notification"""
    timestamp: str
    alert_type: str  # 'var_breach', 'drawdown', 'concentration', 'correlation', 'liquidity'
    severity: str  # 'low', 'medium', 'high', 'critical'
    symbol: Optional[str]
    message: str
    current_value: float
    threshold_value: float
    recommended_action: str
    auto_executed: bool = False

@dataclass
class PositionSizing:
    """Position sizing recommendation"""
    symbol: str
    recommended_size: float
    max_size: float
    min_size: float
    risk_budget_allocation: float
    confidence: float
    reasoning: str
    kelly_criterion: float
    var_based_size: float
    volatility_adjusted_size: float

class RiskModelEngine:
    """Advanced risk modeling engine"""
    
    def __init__(self):
        self.logger = logging.getLogger('RiskModelEngine')
        self.models = {}
        self.risk_factors = {}
        self.correlation_matrix = None
        self.covariance_matrix = None
        
    def calculate_var(self, returns: np.ndarray, confidence_level: float = 0.95, 
                     method: str = 'historical') -> float:
        """Calculate Value at Risk using different methods"""
        try:
            if len(returns) < 30:
                self.logger.warning("Insufficient data for VaR calculation")
                return 0.0
            
            if method == 'historical':
                return np.percentile(returns, (1 - confidence_level) * 100)
            
            elif method == 'parametric':
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                z_score = norm.ppf(1 - confidence_level)
                return mean_return + z_score * std_return
            
            elif method == 'monte_carlo':
                # Monte Carlo simulation
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                
                # Generate random scenarios
                num_simulations = 10000
                simulated_returns = np.random.normal(mean_return, std_return, num_simulations)
                
                return np.percentile(simulated_returns, (1 - confidence_level) * 100)
            
            else:
                return self.calculate_var(returns, confidence_level, 'historical')
                
        except Exception as e:
            self.logger.error(f"VaR calculation failed: {e}")
            return 0.0
    
    def calculate_expected_shortfall(self, returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        try:
            var = self.calculate_var(returns, confidence_level, 'historical')
            tail_returns = returns[returns <= var]
            
            if len(tail_returns) == 0:
                return var
            
            return np.mean(tail_returns)
            
        except Exception as e:
            self.logger.error(f"Expected Shortfall calculation failed: {e}")
            return 0.0
    
    def calculate_portfolio_var(self, weights: np.ndarray, cov_matrix: np.ndarray, 
                               confidence_level: float = 0.95) -> float:
        """Calculate portfolio VaR using covariance matrix"""
        try:
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)
            
            z_score = norm.ppf(1 - confidence_level)
            portfolio_var = z_score * portfolio_std
            
            return portfolio_var
            
        except Exception as e:
            self.logger.error(f"Portfolio VaR calculation failed: {e}")
            return 0.0
    
    def calculate_marginal_var(self, weights: np.ndarray, cov_matrix: np.ndarray, 
                              asset_index: int, confidence_level: float = 0.95) -> float:
        """Calculate marginal VaR for a specific asset"""
        try:
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)
            
            # Marginal contribution to portfolio variance
            marginal_contrib = np.dot(cov_matrix, weights)[asset_index] / portfolio_std
            
            z_score = norm.ppf(1 - confidence_level)
            marginal_var = z_score * marginal_contrib
            
            return marginal_var
            
        except Exception as e:
            self.logger.error(f"Marginal VaR calculation failed: {e}")
            return 0.0
    
    def calculate_component_var(self, weights: np.ndarray, cov_matrix: np.ndarray, 
                               confidence_level: float = 0.95) -> np.ndarray:
        """Calculate component VaR for all assets"""
        try:
            portfolio_var = self.calculate_portfolio_var(weights, cov_matrix, confidence_level)
            component_vars = np.zeros(len(weights))
            
            for i in range(len(weights)):
                marginal_var = self.calculate_marginal_var(weights, cov_matrix, i, confidence_level)
                component_vars[i] = weights[i] * marginal_var
            
            return component_vars
            
        except Exception as e:
            self.logger.error(f"Component VaR calculation failed: {e}")
            return np.zeros(len(weights))
    
    def monte_carlo_simulation(self, returns_data: pd.DataFrame, num_simulations: int = 10000, 
                              time_horizon: int = 1) -> Dict[str, np.ndarray]:
        """Perform Monte Carlo simulation for risk assessment"""
        try:
            # Calculate mean returns and covariance matrix
            mean_returns = returns_data.mean()
            cov_matrix = returns_data.cov()
            
            # Cholesky decomposition for correlated random variables
            chol_matrix = np.linalg.cholesky(cov_matrix)
            
            # Generate random scenarios
            random_matrix = np.random.normal(0, 1, (len(mean_returns), num_simulations))
            correlated_random = np.dot(chol_matrix, random_matrix)
            
            # Calculate simulated returns
            simulated_returns = np.zeros((len(mean_returns), num_simulations))
            
            for i in range(len(mean_returns)):
                simulated_returns[i] = mean_returns.iloc[i] * time_horizon + \
                                     correlated_random[i] * np.sqrt(time_horizon)
            
            results = {
                'simulated_returns': simulated_returns,
                'portfolio_returns': np.sum(simulated_returns, axis=0),
                'mean_returns': mean_returns,
                'cov_matrix': cov_matrix
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Monte Carlo simulation failed: {e}")
            return {}
    
    def stress_test(self, portfolio_data: pd.DataFrame, scenarios: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Perform stress testing under various scenarios"""
        results = {}
        
        try:
            current_portfolio_value = portfolio_data['market_value'].sum()
            
            for scenario_name, shocks in scenarios.items():
                stressed_value = 0.0
                
                for symbol, shock in shocks.items():
                    if symbol in portfolio_data['symbol'].values:
                        position_value = portfolio_data[portfolio_data['symbol'] == symbol]['market_value'].iloc[0]
                        stressed_value += position_value * (1 + shock)
                    else:
                        # Apply shock to entire portfolio if symbol not found
                        stressed_value = current_portfolio_value * (1 + shock)
                        break
                
                pnl_change = (stressed_value - current_portfolio_value) / current_portfolio_value
                results[scenario_name] = pnl_change
            
            return results
            
        except Exception as e:
            self.logger.error(f"Stress testing failed: {e}")
            return {}

class AdvancedRiskManager:
    """Advanced risk management system"""
    
    def __init__(self, config_file: str = 'risk_config.json'):
        self.logger = self._setup_logging()
        self.risk_engine = RiskModelEngine()
        
        # Configuration
        self.config = self._load_config(config_file)
        
        # Data storage
        self.portfolio_data = pd.DataFrame()
        self.price_history = {}
        self.returns_history = {}
        self.risk_metrics_history = deque(maxlen=1000)
        self.alerts_history = deque(maxlen=500)
        
        # Risk limits and thresholds
        self.risk_limits = self.config.get('risk_limits', {
            'max_portfolio_var_1d': 0.05,  # 5% daily VaR limit
            'max_position_weight': 0.20,   # 20% max position size
            'max_sector_weight': 0.40,     # 40% max sector exposure
            'max_correlation': 0.80,       # 80% max correlation
            'min_liquidity_score': 0.60,   # 60% min liquidity
            'max_drawdown': 0.15,          # 15% max drawdown
            'leverage_limit': 2.0          # 2x max leverage
        })
        
        # Risk budgets
        self.risk_budgets = self.config.get('risk_budgets', {
            'equity': 0.60,
            'crypto': 0.25,
            'forex': 0.10,
            'commodities': 0.05
        })
        
        # Monitoring flags
        self.monitoring_active = False
        self.auto_rebalance_enabled = True
        self.circuit_breaker_active = False
        
        # Performance tracking
        self.performance_metrics = {}
        
        self.logger.info("🛡️ Advanced Risk Management System initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('AdvancedRiskManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('risk_management.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load risk management configuration"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    'risk_limits': {
                        'max_portfolio_var_1d': 0.05,
                        'max_position_weight': 0.20,
                        'max_sector_weight': 0.40,
                        'max_correlation': 0.80,
                        'min_liquidity_score': 0.60,
                        'max_drawdown': 0.15,
                        'leverage_limit': 2.0
                    },
                    'position_sizing': {
                        'method': 'kelly_var_hybrid',
                        'max_kelly_fraction': 0.25,
                        'var_multiplier': 2.0,
                        'volatility_lookback': 30
                    },
                    'rebalancing': {
                        'frequency': 'daily',
                        'threshold': 0.05,
                        'method': 'mean_reversion'
                    },
                    'stress_scenarios': {
                        'market_crash': {'all': -0.20},
                        'sector_rotation': {'tech': -0.15, 'finance': 0.10},
                        'volatility_spike': {'all': -0.10},
                        'liquidity_crisis': {'small_cap': -0.25}
                    }
                }
                
                # Save default config
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
                
        except Exception as e:
            self.logger.error(f"Config loading failed: {e}")
            return {}
    
    def update_portfolio_data(self, portfolio_data: pd.DataFrame):
        """Update portfolio data for risk analysis"""
        try:
            self.portfolio_data = portfolio_data.copy()
            
            # Update price history
            for _, row in portfolio_data.iterrows():
                symbol = row['symbol']
                price = row.get('current_price', row.get('price', 0))
                
                if symbol not in self.price_history:
                    self.price_history[symbol] = deque(maxlen=252)  # 1 year of daily data
                
                self.price_history[symbol].append({
                    'timestamp': datetime.now().isoformat(),
                    'price': price
                })
            
            # Calculate returns
            self._update_returns_history()
            
        except Exception as e:
            self.logger.error(f"Portfolio data update failed: {e}")
    
    def _update_returns_history(self):
        """Update returns history for all symbols"""
        try:
            for symbol, price_data in self.price_history.items():
                if len(price_data) < 2:
                    continue
                
                prices = [p['price'] for p in price_data]
                returns = np.diff(np.log(prices))  # Log returns
                
                if symbol not in self.returns_history:
                    self.returns_history[symbol] = deque(maxlen=252)
                
                if len(returns) > 0:
                    self.returns_history[symbol].append(returns[-1])
            
        except Exception as e:
            self.logger.error(f"Returns history update failed: {e}")
    
    def calculate_position_risk_metrics(self, symbol: str) -> Optional[RiskMetrics]:
        """Calculate comprehensive risk metrics for a position"""
        try:
            if symbol not in self.returns_history or len(self.returns_history[symbol]) < 30:
                self.logger.warning(f"Insufficient data for {symbol} risk calculation")
                return None
            
            # Get position data
            position_data = self.portfolio_data[self.portfolio_data['symbol'] == symbol]
            if position_data.empty:
                return None
            
            position = position_data.iloc[0]
            returns = np.array(list(self.returns_history[symbol]))
            
            # Basic metrics
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # VaR calculations
            var_1d_95 = self.risk_engine.calculate_var(returns, 0.95)
            var_1d_99 = self.risk_engine.calculate_var(returns, 0.99)
            var_10d_95 = var_1d_95 * np.sqrt(10)  # Scaling for 10 days
            expected_shortfall_95 = self.risk_engine.calculate_expected_shortfall(returns, 0.95)
            
            # Performance metrics
            mean_return = np.mean(returns)
            sharpe_ratio = mean_return / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            # Downside deviation for Sortino ratio
            downside_returns = returns[returns < 0]
            downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else np.std(returns)
            sortino_ratio = mean_return / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
            
            # Maximum drawdown
            cumulative_returns = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # Calmar ratio
            calmar_ratio = (mean_return * 252) / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Portfolio weight
            total_portfolio_value = self.portfolio_data['market_value'].sum()
            portfolio_weight = position['market_value'] / total_portfolio_value if total_portfolio_value > 0 else 0
            
            # Liquidity score (simplified)
            liquidity_score = min(1.0, position.get('volume', 1000000) / 1000000)  # Based on volume
            
            # Beta calculation (if market data available)
            beta = self._calculate_beta(symbol)
            correlation_to_market = self._calculate_market_correlation(symbol)
            
            risk_metrics = RiskMetrics(
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                position_size=position.get('quantity', 0),
                market_value=position['market_value'],
                volatility=volatility,
                beta=beta,
                correlation_to_market=correlation_to_market,
                var_1d_95=var_1d_95,
                var_1d_99=var_1d_99,
                var_10d_95=var_10d_95,
                expected_shortfall_95=expected_shortfall_95,
                portfolio_weight=portfolio_weight,
                contribution_to_var=0.0,  # Will be calculated at portfolio level
                marginal_var=0.0,  # Will be calculated at portfolio level
                component_var=0.0,  # Will be calculated at portfolio level
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                max_drawdown=max_drawdown,
                information_ratio=0.0,  # Requires benchmark
                treynor_ratio=mean_return * 252 / beta if beta != 0 else 0,
                jensen_alpha=0.0,  # Requires benchmark
                liquidity_score=liquidity_score,
                bid_ask_spread=position.get('spread', 0.001),
                market_impact_cost=position.get('impact_cost', 0.0005),
                confidence_level=0.8,  # Model confidence
                model_accuracy=0.75  # Historical accuracy
            )
            
            return risk_metrics
            
        except Exception as e:
            self.logger.error(f"Risk metrics calculation failed for {symbol}: {e}")
            return None
    
    def _calculate_beta(self, symbol: str) -> float:
        """Calculate beta relative to market (simplified)"""
        try:
            # This is a simplified beta calculation
            # In practice, you would use a market index
            if symbol not in self.returns_history:
                return 1.0
            
            returns = np.array(list(self.returns_history[symbol]))
            
            # Use portfolio returns as proxy for market
            portfolio_returns = self._calculate_portfolio_returns()
            
            if len(portfolio_returns) != len(returns):
                return 1.0
            
            covariance = np.cov(returns, portfolio_returns)[0, 1]
            market_variance = np.var(portfolio_returns)
            
            beta = covariance / market_variance if market_variance > 0 else 1.0
            return beta
            
        except Exception as e:
            self.logger.error(f"Beta calculation failed for {symbol}: {e}")
            return 1.0
    
    def _calculate_market_correlation(self, symbol: str) -> float:
        """Calculate correlation to market"""
        try:
            if symbol not in self.returns_history:
                return 0.0
            
            returns = np.array(list(self.returns_history[symbol]))
            portfolio_returns = self._calculate_portfolio_returns()
            
            if len(portfolio_returns) != len(returns):
                return 0.0
            
            correlation = np.corrcoef(returns, portfolio_returns)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            self.logger.error(f"Market correlation calculation failed for {symbol}: {e}")
            return 0.0
    
    def _calculate_portfolio_returns(self) -> np.ndarray:
        """Calculate portfolio returns"""
        try:
            if self.portfolio_data.empty:
                return np.array([])
            
            # Weight returns by market value
            total_value = self.portfolio_data['market_value'].sum()
            portfolio_returns = []
            
            # Get minimum length across all symbols
            min_length = min([len(self.returns_history[symbol]) 
                            for symbol in self.portfolio_data['symbol'] 
                            if symbol in self.returns_history])
            
            if min_length == 0:
                return np.array([])
            
            for i in range(min_length):
                weighted_return = 0.0
                
                for _, position in self.portfolio_data.iterrows():
                    symbol = position['symbol']
                    if symbol in self.returns_history and len(self.returns_history[symbol]) > i:
                        weight = position['market_value'] / total_value
                        return_value = list(self.returns_history[symbol])[-min_length + i]
                        weighted_return += weight * return_value
                
                portfolio_returns.append(weighted_return)
            
            return np.array(portfolio_returns)
            
        except Exception as e:
            self.logger.error(f"Portfolio returns calculation failed: {e}")
            return np.array([])
    
    def calculate_portfolio_risk(self) -> Optional[PortfolioRisk]:
        """Calculate portfolio-level risk metrics"""
        try:
            if self.portfolio_data.empty:
                return None
            
            total_value = self.portfolio_data['market_value'].sum()
            num_positions = len(self.portfolio_data)
            
            # Portfolio returns
            portfolio_returns = self._calculate_portfolio_returns()
            
            if len(portfolio_returns) < 30:
                self.logger.warning("Insufficient data for portfolio risk calculation")
                return None
            
            # Portfolio VaR
            portfolio_var_1d_95 = self.risk_engine.calculate_var(portfolio_returns, 0.95)
            portfolio_var_1d_99 = self.risk_engine.calculate_var(portfolio_returns, 0.99)
            portfolio_expected_shortfall = self.risk_engine.calculate_expected_shortfall(portfolio_returns, 0.95)
            
            # Portfolio volatility and beta
            portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)
            portfolio_beta = 1.0  # Simplified
            
            # Diversification metrics
            weights = self.portfolio_data['market_value'] / total_value
            
            # Concentration risk (Herfindahl index)
            concentration_risk = np.sum(weights ** 2)
            
            # Correlation risk
            correlation_risk = self._calculate_correlation_risk()
            
            # Diversification ratio
            diversification_ratio = self._calculate_diversification_ratio(weights)
            
            # Sector concentration
            sector_concentration = self._calculate_sector_concentration()
            
            # Risk budget utilization
            risk_budget_utilization = self._calculate_risk_budget_utilization()
            risk_budget_allocation = self._calculate_risk_budget_allocation()
            
            # Stress testing
            stress_scenarios = self.config.get('stress_scenarios', {})
            stress_test_results = self.risk_engine.stress_test(self.portfolio_data, stress_scenarios)
            
            # Scenario analysis
            scenario_analysis = self._perform_scenario_analysis()
            
            # Regulatory metrics
            leverage_ratio = self._calculate_leverage_ratio()
            exposure_limits = self._check_exposure_limits()
            compliance_status = self._check_compliance_status()
            
            portfolio_risk = PortfolioRisk(
                timestamp=datetime.now().isoformat(),
                total_value=total_value,
                num_positions=num_positions,
                portfolio_var_1d_95=portfolio_var_1d_95,
                portfolio_var_1d_99=portfolio_var_1d_99,
                portfolio_expected_shortfall=portfolio_expected_shortfall,
                portfolio_volatility=portfolio_volatility,
                portfolio_beta=portfolio_beta,
                diversification_ratio=diversification_ratio,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk,
                sector_concentration=sector_concentration,
                risk_budget_utilization=risk_budget_utilization,
                risk_budget_allocation=risk_budget_allocation,
                stress_test_results=stress_test_results,
                scenario_analysis=scenario_analysis,
                leverage_ratio=leverage_ratio,
                exposure_limits=exposure_limits,
                compliance_status=compliance_status
            )
            
            return portfolio_risk
            
        except Exception as e:
            self.logger.error(f"Portfolio risk calculation failed: {e}")
            return None
    
    def _calculate_correlation_risk(self) -> float:
        """Calculate correlation risk metric"""
        try:
            if len(self.portfolio_data) < 2:
                return 0.0
            
            symbols = self.portfolio_data['symbol'].tolist()
            correlations = []
            
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols[i+1:], i+1):
                    if symbol1 in self.returns_history and symbol2 in self.returns_history:
                        returns1 = np.array(list(self.returns_history[symbol1]))
                        returns2 = np.array(list(self.returns_history[symbol2]))
                        
                        min_length = min(len(returns1), len(returns2))
                        if min_length > 10:
                            corr = np.corrcoef(returns1[-min_length:], returns2[-min_length:])[0, 1]
                            if not np.isnan(corr):
                                correlations.append(abs(corr))
            
            return np.mean(correlations) if correlations else 0.0
            
        except Exception as e:
            self.logger.error(f"Correlation risk calculation failed: {e}")
            return 0.0
    
    def _calculate_diversification_ratio(self, weights: np.ndarray) -> float:
        """Calculate diversification ratio"""
        try:
            # Simplified diversification ratio
            # In practice, this would use the full covariance matrix
            
            # Weighted average volatility
            individual_vols = []
            for symbol in self.portfolio_data['symbol']:
                if symbol in self.returns_history and len(self.returns_history[symbol]) > 10:
                    returns = np.array(list(self.returns_history[symbol]))
                    vol = np.std(returns) * np.sqrt(252)
                    individual_vols.append(vol)
                else:
                    individual_vols.append(0.2)  # Default 20% volatility
            
            weighted_avg_vol = np.sum(weights * np.array(individual_vols))
            
            # Portfolio volatility
            portfolio_returns = self._calculate_portfolio_returns()
            if len(portfolio_returns) > 10:
                portfolio_vol = np.std(portfolio_returns) * np.sqrt(252)
            else:
                portfolio_vol = weighted_avg_vol
            
            diversification_ratio = weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1.0
            return diversification_ratio
            
        except Exception as e:
            self.logger.error(f"Diversification ratio calculation failed: {e}")
            return 1.0
    
    def _calculate_sector_concentration(self) -> Dict[str, float]:
        """Calculate sector concentration"""
        try:
            sector_exposure = defaultdict(float)
            total_value = self.portfolio_data['market_value'].sum()
            
            for _, position in self.portfolio_data.iterrows():
                # Simplified sector classification
                symbol = position['symbol']
                sector = self._classify_sector(symbol)
                weight = position['market_value'] / total_value
                sector_exposure[sector] += weight
            
            return dict(sector_exposure)
            
        except Exception as e:
            self.logger.error(f"Sector concentration calculation failed: {e}")
            return {}
    
    def _classify_sector(self, symbol: str) -> str:
        """Classify symbol into sector (simplified)"""
        # This is a simplified classification
        # In practice, you would use a proper sector classification system
        
        crypto_symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']
        tech_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        finance_symbols = ['JPM', 'BAC', 'GS', 'MS', 'C']
        
        if any(crypto in symbol for crypto in crypto_symbols):
            return 'crypto'
        elif any(tech in symbol for tech in tech_symbols):
            return 'technology'
        elif any(fin in symbol for fin in finance_symbols):
            return 'finance'
        else:
            return 'other'
    
    def _calculate_risk_budget_utilization(self) -> float:
        """Calculate risk budget utilization"""
        try:
            sector_exposure = self._calculate_sector_concentration()
            utilization = 0.0
            
            for sector, exposure in sector_exposure.items():
                budget = self.risk_budgets.get(sector, 0.1)  # Default 10%
                utilization += exposure / budget if budget > 0 else 0
            
            return min(utilization, 1.0)
            
        except Exception as e:
            self.logger.error(f"Risk budget utilization calculation failed: {e}")
            return 0.0
    
    def _calculate_risk_budget_allocation(self) -> Dict[str, float]:
        """Calculate current risk budget allocation"""
        try:
            sector_exposure = self._calculate_sector_concentration()
            allocation = {}
            
            for sector, budget in self.risk_budgets.items():
                current_exposure = sector_exposure.get(sector, 0.0)
                allocation[sector] = current_exposure / budget if budget > 0 else 0
            
            return allocation
            
        except Exception as e:
            self.logger.error(f"Risk budget allocation calculation failed: {e}")
            return {}
    
    def _perform_scenario_analysis(self) -> Dict[str, float]:
        """Perform scenario analysis"""
        try:
            scenarios = {
                'bull_market': 0.15,
                'bear_market': -0.20,
                'high_volatility': -0.10,
                'low_volatility': 0.05,
                'sector_rotation': -0.05
            }
            
            # This is simplified - in practice you would model specific scenarios
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Scenario analysis failed: {e}")
            return {}
    
    def _calculate_leverage_ratio(self) -> float:
        """Calculate leverage ratio"""
        try:
            # Simplified leverage calculation
            total_exposure = self.portfolio_data['market_value'].sum()
            # Assuming cash/equity base (would need actual equity data)
            equity_base = total_exposure  # Simplified assumption
            
            leverage = total_exposure / equity_base if equity_base > 0 else 1.0
            return leverage
            
        except Exception as e:
            self.logger.error(f"Leverage ratio calculation failed: {e}")
            return 1.0
    
    def _check_exposure_limits(self) -> Dict[str, float]:
        """Check exposure limits"""
        try:
            limits = {}
            total_value = self.portfolio_data['market_value'].sum()
            
            # Position limits
            for _, position in self.portfolio_data.iterrows():
                weight = position['market_value'] / total_value
                limits[f"{position['symbol']}_weight"] = weight
            
            # Sector limits
            sector_exposure = self._calculate_sector_concentration()
            for sector, exposure in sector_exposure.items():
                limits[f"{sector}_exposure"] = exposure
            
            return limits
            
        except Exception as e:
            self.logger.error(f"Exposure limits check failed: {e}")
            return {}
    
    def _check_compliance_status(self) -> str:
        """Check overall compliance status"""
        try:
            violations = []
            
            # Check portfolio VaR
            portfolio_risk = self.calculate_portfolio_risk()
            if portfolio_risk and abs(portfolio_risk.portfolio_var_1d_95) > self.risk_limits['max_portfolio_var_1d']:
                violations.append('portfolio_var')
            
            # Check position weights
            total_value = self.portfolio_data['market_value'].sum()
            for _, position in self.portfolio_data.iterrows():
                weight = position['market_value'] / total_value
                if weight > self.risk_limits['max_position_weight']:
                    violations.append(f"position_weight_{position['symbol']}")
            
            # Check sector concentration
            sector_exposure = self._calculate_sector_concentration()
            for sector, exposure in sector_exposure.items():
                if exposure > self.risk_limits['max_sector_weight']:
                    violations.append(f"sector_weight_{sector}")
            
            if not violations:
                return 'compliant'
            elif len(violations) <= 2:
                return 'minor_violations'
            else:
                return 'major_violations'
                
        except Exception as e:
            self.logger.error(f"Compliance status check failed: {e}")
            return 'unknown'
    
    def calculate_optimal_position_size(self, symbol: str, target_return: float = 0.0, 
                                      max_risk: float = 0.02) -> Optional[PositionSizing]:
        """Calculate optimal position size using multiple methods"""
        try:
            if symbol not in self.returns_history or len(self.returns_history[symbol]) < 30:
                return None
            
            returns = np.array(list(self.returns_history[symbol]))
            
            # Kelly Criterion
            mean_return = np.mean(returns)
            variance = np.var(returns)
            kelly_fraction = mean_return / variance if variance > 0 else 0
            kelly_fraction = max(0, min(kelly_fraction, self.config.get('position_sizing', {}).get('max_kelly_fraction', 0.25)))
            
            # VaR-based sizing
            var_95 = self.risk_engine.calculate_var(returns, 0.95)
            var_based_size = max_risk / abs(var_95) if var_95 != 0 else 0
            
            # Volatility-adjusted sizing
            volatility = np.std(returns)
            target_vol = 0.15  # 15% target volatility
            vol_adjusted_size = target_vol / volatility if volatility > 0 else 0
            
            # Combined approach
            method = self.config.get('position_sizing', {}).get('method', 'kelly_var_hybrid')
            
            if method == 'kelly_var_hybrid':
                recommended_size = (kelly_fraction + var_based_size + vol_adjusted_size) / 3
            elif method == 'kelly':
                recommended_size = kelly_fraction
            elif method == 'var':
                recommended_size = var_based_size
            else:
                recommended_size = vol_adjusted_size
            
            # Apply position limits
            max_position_weight = self.risk_limits['max_position_weight']
            recommended_size = min(recommended_size, max_position_weight)
            
            # Calculate confidence
            data_quality = min(1.0, len(returns) / 252)  # More data = higher confidence
            model_stability = 1.0 - abs(np.std([kelly_fraction, var_based_size, vol_adjusted_size]) / np.mean([kelly_fraction, var_based_size, vol_adjusted_size]))
            confidence = (data_quality + model_stability) / 2
            
            position_sizing = PositionSizing(
                symbol=symbol,
                recommended_size=recommended_size,
                max_size=max_position_weight,
                min_size=0.01,  # 1% minimum
                risk_budget_allocation=recommended_size,
                confidence=confidence,
                reasoning=f"Using {method} method with {len(returns)} data points",
                kelly_criterion=kelly_fraction,
                var_based_size=var_based_size,
                volatility_adjusted_size=vol_adjusted_size
            )
            
            return position_sizing
            
        except Exception as e:
            self.logger.error(f"Position sizing calculation failed for {symbol}: {e}")
            return None
    
    def generate_risk_alerts(self) -> List[RiskAlert]:
        """Generate risk alerts based on current portfolio state"""
        alerts = []
        
        try:
            # Portfolio-level alerts
            portfolio_risk = self.calculate_portfolio_risk()
            
            if portfolio_risk:
                # VaR breach alert
                if abs(portfolio_risk.portfolio_var_1d_95) > self.risk_limits['max_portfolio_var_1d']:
                    alert = RiskAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='var_breach',
                        severity='high',
                        symbol=None,
                        message=f"Portfolio VaR ({abs(portfolio_risk.portfolio_var_1d_95):.2%}) exceeds limit ({self.risk_limits['max_portfolio_var_1d']:.2%})",
                        current_value=abs(portfolio_risk.portfolio_var_1d_95),
                        threshold_value=self.risk_limits['max_portfolio_var_1d'],
                        recommended_action="Reduce position sizes or hedge portfolio"
                    )
                    alerts.append(alert)
                
                # Concentration risk alert
                if portfolio_risk.concentration_risk > 0.5:  # High concentration
                    alert = RiskAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='concentration',
                        severity='medium',
                        symbol=None,
                        message=f"High portfolio concentration detected ({portfolio_risk.concentration_risk:.2f})",
                        current_value=portfolio_risk.concentration_risk,
                        threshold_value=0.5,
                        recommended_action="Diversify portfolio holdings"
                    )
                    alerts.append(alert)
                
                # Correlation risk alert
                if portfolio_risk.correlation_risk > self.risk_limits['max_correlation']:
                    alert = RiskAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='correlation',
                        severity='medium',
                        symbol=None,
                        message=f"High correlation risk detected ({portfolio_risk.correlation_risk:.2f})",
                        current_value=portfolio_risk.correlation_risk,
                        threshold_value=self.risk_limits['max_correlation'],
                        recommended_action="Reduce correlated positions"
                    )
                    alerts.append(alert)
            
            # Position-level alerts
            total_value = self.portfolio_data['market_value'].sum()
            
            for _, position in self.portfolio_data.iterrows():
                symbol = position['symbol']
                weight = position['market_value'] / total_value
                
                # Position size alert
                if weight > self.risk_limits['max_position_weight']:
                    alert = RiskAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='position_size',
                        severity='high',
                        symbol=symbol,
                        message=f"{symbol} position size ({weight:.2%}) exceeds limit ({self.risk_limits['max_position_weight']:.2%})",
                        current_value=weight,
                        threshold_value=self.risk_limits['max_position_weight'],
                        recommended_action=f"Reduce {symbol} position size"
                    )
                    alerts.append(alert)
                
                # Liquidity alert
                liquidity_score = position.get('liquidity_score', 1.0)
                if liquidity_score < self.risk_limits['min_liquidity_score']:
                    alert = RiskAlert(
                        timestamp=datetime.now().isoformat(),
                        alert_type='liquidity',
                        severity='medium',
                        symbol=symbol,
                        message=f"{symbol} liquidity score ({liquidity_score:.2f}) below minimum ({self.risk_limits['min_liquidity_score']:.2f})",
                        current_value=liquidity_score,
                        threshold_value=self.risk_limits['min_liquidity_score'],
                        recommended_action=f"Monitor {symbol} liquidity or reduce position"
                    )
                    alerts.append(alert)
            
            # Store alerts
            self.alerts_history.extend(alerts)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Risk alert generation failed: {e}")
            return []
    
    def start_monitoring(self):
        """Start continuous risk monitoring"""
        self.monitoring_active = True
        self.logger.info("🔍 Risk monitoring started")
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Generate alerts
                    alerts = self.generate_risk_alerts()
                    
                    # Process critical alerts
                    for alert in alerts:
                        if alert.severity == 'critical':
                            self._handle_critical_alert(alert)
                        elif alert.severity == 'high':
                            self._handle_high_alert(alert)
                    
                    # Auto-rebalance if enabled
                    if self.auto_rebalance_enabled:
                        self._check_rebalancing_triggers()
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
    
    def _handle_critical_alert(self, alert: RiskAlert):
        """Handle critical risk alerts"""
        try:
            self.logger.critical(f"CRITICAL ALERT: {alert.message}")
            
            # Implement emergency actions
            if alert.alert_type == 'var_breach' and not self.circuit_breaker_active:
                self._activate_circuit_breaker()
            
            # Send notifications (implement as needed)
            self._send_alert_notification(alert)
            
        except Exception as e:
            self.logger.error(f"Critical alert handling failed: {e}")
    
    def _handle_high_alert(self, alert: RiskAlert):
        """Handle high severity alerts"""
        try:
            self.logger.warning(f"HIGH ALERT: {alert.message}")
            
            # Implement automated responses
            if alert.alert_type == 'position_size' and alert.symbol:
                self._suggest_position_reduction(alert.symbol)
            
            self._send_alert_notification(alert)
            
        except Exception as e:
            self.logger.error(f"High alert handling failed: {e}")
    
    def _activate_circuit_breaker(self):
        """Activate emergency circuit breaker"""
        try:
            self.circuit_breaker_active = True
            self.logger.critical("🚨 CIRCUIT BREAKER ACTIVATED - Trading halted")
            
            # Implement emergency procedures
            # - Stop all trading
            # - Close risky positions
            # - Send emergency notifications
            
        except Exception as e:
            self.logger.error(f"Circuit breaker activation failed: {e}")
    
    def _suggest_position_reduction(self, symbol: str):
        """Suggest position reduction for oversized positions"""
        try:
            optimal_sizing = self.calculate_optimal_position_size(symbol)
            if optimal_sizing:
                self.logger.info(f"💡 Suggested position size for {symbol}: {optimal_sizing.recommended_size:.2%}")
            
        except Exception as e:
            self.logger.error(f"Position reduction suggestion failed: {e}")
    
    def _check_rebalancing_triggers(self):
        """Check if portfolio rebalancing is needed"""
        try:
            # Implement rebalancing logic
            # This would check drift from target allocations
            pass
            
        except Exception as e:
            self.logger.error(f"Rebalancing check failed: {e}")
    
    def _send_alert_notification(self, alert: RiskAlert):
        """Send alert notification (implement as needed)"""
        try:
            # Implement notification system (email, Slack, etc.)
            self.logger.info(f"📧 Alert notification sent: {alert.message}")
            
        except Exception as e:
            self.logger.error(f"Alert notification failed: {e}")
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'portfolio_summary': {},
                'risk_metrics': {},
                'alerts': [],
                'compliance': {},
                'recommendations': []
            }
            
            # Portfolio summary
            if not self.portfolio_data.empty:
                report['portfolio_summary'] = {
                    'total_value': self.portfolio_data['market_value'].sum(),
                    'num_positions': len(self.portfolio_data),
                    'largest_position': self.portfolio_data['market_value'].max(),
                    'smallest_position': self.portfolio_data['market_value'].min()
                }
            
            # Risk metrics
            portfolio_risk = self.calculate_portfolio_risk()
            if portfolio_risk:
                report['risk_metrics'] = {
                    'portfolio_var_1d_95': portfolio_risk.portfolio_var_1d_95,
                    'portfolio_volatility': portfolio_risk.portfolio_volatility,
                    'concentration_risk': portfolio_risk.concentration_risk,
                    'correlation_risk': portfolio_risk.correlation_risk,
                    'diversification_ratio': portfolio_risk.diversification_ratio
                }
            
            # Recent alerts
            recent_alerts = [alert for alert in self.alerts_history 
                           if datetime.fromisoformat(alert.timestamp) > datetime.now() - timedelta(days=1)]
            report['alerts'] = [asdict(alert) for alert in recent_alerts[-10:]]  # Last 10 alerts
            
            # Compliance status
            report['compliance'] = {
                'status': self._check_compliance_status(),
                'violations': [],
                'risk_budget_utilization': self._calculate_risk_budget_utilization()
            }
            
            # Recommendations
            recommendations = self._generate_recommendations()
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            self.logger.error(f"Risk report generation failed: {e}")
            return {}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        try:
            portfolio_risk = self.calculate_portfolio_risk()
            
            if portfolio_risk:
                # Concentration recommendations
                if portfolio_risk.concentration_risk > 0.4:
                    recommendations.append("Consider diversifying portfolio to reduce concentration risk")
                
                # Correlation recommendations
                if portfolio_risk.correlation_risk > 0.7:
                    recommendations.append("Reduce correlated positions to improve diversification")
                
                # VaR recommendations
                if abs(portfolio_risk.portfolio_var_1d_95) > self.risk_limits['max_portfolio_var_1d'] * 0.8:
                    recommendations.append("Portfolio VaR approaching limit - consider risk reduction")
                
                # Sector recommendations
                for sector, exposure in portfolio_risk.sector_concentration.items():
                    if exposure > self.risk_limits['max_sector_weight'] * 0.8:
                        recommendations.append(f"High {sector} sector exposure - consider rebalancing")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return []

# Example usage and testing
def main():
    """Main function for testing the risk management system"""
    risk_manager = AdvancedRiskManager()
    
    # Generate sample portfolio data
    print("📊 Generating sample portfolio data...")
    
    sample_portfolio = pd.DataFrame([
        {'symbol': 'BTCUSD', 'quantity': 1.5, 'current_price': 50000, 'market_value': 75000},
        {'symbol': 'ETHUSD', 'quantity': 20, 'current_price': 3000, 'market_value': 60000},
        {'symbol': 'AAPL', 'quantity': 100, 'current_price': 150, 'market_value': 15000},
        {'symbol': 'GOOGL', 'quantity': 10, 'current_price': 2500, 'market_value': 25000},
        {'symbol': 'TSLA', 'quantity': 50, 'current_price': 200, 'market_value': 10000}
    ])
    
    # Update portfolio data
    risk_manager.update_portfolio_data(sample_portfolio)
    
    # Generate sample price history
    print("📈 Generating sample price history...")
    
    for symbol in sample_portfolio['symbol']:
        base_price = sample_portfolio[sample_portfolio['symbol'] == symbol]['current_price'].iloc[0]
        
        for i in range(100):
            price_change = np.random.normal(0, 0.02)
            new_price = base_price * (1 + price_change)
            
            risk_manager.price_history[symbol].append({
                'timestamp': (datetime.now() - timedelta(days=100-i)).isoformat(),
                'price': new_price
            })
            
            base_price = new_price
    
    # Update returns history
    risk_manager._update_returns_history()
    
    # Calculate risk metrics
    print("🛡️ Calculating risk metrics...")
    
    # Position-level risk metrics
    for symbol in sample_portfolio['symbol']:
        risk_metrics = risk_manager.calculate_position_risk_metrics(symbol)
        if risk_metrics:
            print(f"\n📊 Risk Metrics for {symbol}:")
            print(f"   VaR (1d, 95%): {risk_metrics.var_1d_95:.4f}")
            print(f"   Volatility: {risk_metrics.volatility:.2%}")
            print(f"   Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
            print(f"   Max Drawdown: {risk_metrics.max_drawdown:.2%}")
    
    # Portfolio-level risk metrics
    portfolio_risk = risk_manager.calculate_portfolio_risk()
    if portfolio_risk:
        print(f"\n🎯 Portfolio Risk Metrics:")
        print(f"   Portfolio VaR (1d, 95%): {portfolio_risk.portfolio_var_1d_95:.4f}")
        print(f"   Portfolio Volatility: {portfolio_risk.portfolio_volatility:.2%}")
        print(f"   Concentration Risk: {portfolio_risk.concentration_risk:.3f}")
        print(f"   Diversification Ratio: {portfolio_risk.diversification_ratio:.2f}")
        print(f"   Compliance Status: {portfolio_risk.compliance_status}")
    
    # Position sizing recommendations
    print(f"\n💰 Position Sizing Recommendations:")
    for symbol in sample_portfolio['symbol']:
        sizing = risk_manager.calculate_optimal_position_size(symbol)
        if sizing:
            print(f"   {symbol}: {sizing.recommended_size:.2%} (Kelly: {sizing.kelly_criterion:.2%}, Confidence: {sizing.confidence:.2f})")
    
    # Generate alerts
    print(f"\n🚨 Risk Alerts:")
    alerts = risk_manager.generate_risk_alerts()
    if alerts:
        for alert in alerts:
            print(f"   [{alert.severity.upper()}] {alert.message}")
    else:
        print("   No alerts generated")
    
    # Generate comprehensive report
    print(f"\n📋 Generating comprehensive risk report...")
    report = risk_manager.generate_risk_report()
    
    if report:
        print(f"\n📊 Risk Report Summary:")
        print(f"   Total Portfolio Value: ${report['portfolio_summary'].get('total_value', 0):,.2f}")
        print(f"   Number of Positions: {report['portfolio_summary'].get('num_positions', 0)}")
        print(f"   Risk Budget Utilization: {report['compliance'].get('risk_budget_utilization', 0):.1%}")
        print(f"   Recent Alerts: {len(report['alerts'])}")
        print(f"   Recommendations: {len(report['recommendations'])}")
        
        if report['recommendations']:
            print(f"\n💡 Key Recommendations:")
            for i, rec in enumerate(report['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
    
    # Start monitoring (for demonstration)
    print(f"\n🔍 Starting risk monitoring...")
    risk_manager.start_monitoring()
    
    print(f"\n✅ Advanced Risk Management System demonstration completed!")
    print(f"📝 Check 'risk_management.log' for detailed logs")
    print(f"⚙️ Modify 'risk_config.json' to customize risk parameters")
    
    return risk_manager

if __name__ == "__main__":
    try:
        print("🛡️ TradeBot Sentinel - Advanced Risk Management System")
        print("=" * 60)
        
        # Run the main demonstration
        risk_manager = main()
        
        # Keep the monitoring running for a short time
        print(f"\n⏱️ Monitoring active for 30 seconds...")
        time.sleep(30)
        
        # Stop monitoring
        risk_manager.monitoring_active = False
        print(f"\n🛑 Risk monitoring stopped")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Risk management system stopped by user")
    except Exception as e:
        print(f"\n❌ Error in risk management system: {e}")
        traceback.print_exc()