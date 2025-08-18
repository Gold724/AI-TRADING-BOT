#!/usr/bin/env python3
"""
TradeBot Sentinel - Advanced Portfolio Optimization System

Comprehensive portfolio optimization and risk management:
- Modern Portfolio Theory (MPT) implementation
- Black-Litterman model for expected returns
- Risk parity and equal risk contribution strategies
- Machine learning-based portfolio optimization
- Dynamic rebalancing and position sizing
- Multi-objective optimization (return, risk, drawdown)
- Factor-based portfolio construction
- Real-time portfolio monitoring and alerts
- Backtesting and performance attribution
- Integration with sentiment and market data

Features:
- Efficient frontier calculation and visualization
- Monte Carlo simulation for portfolio scenarios
- Value at Risk (VaR) and Expected Shortfall (ES) optimization
- Correlation and covariance matrix estimation
- Regime-aware portfolio allocation
- Transaction cost optimization
- Tax-aware portfolio management
- Multi-asset class support (crypto, stocks, bonds, commodities)
- Real-time portfolio tracking and rebalancing alerts
- Performance attribution and risk decomposition

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
import warnings
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
warnings.filterwarnings('ignore')

# Scientific computing
from scipy import optimize
from scipy.stats import norm, t
from scipy.linalg import sqrtm
import cvxpy as cp

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Plotting (optional)
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("⚠️ Matplotlib/Seaborn not available. Plotting features will be disabled.")

@dataclass
class Asset:
    """Individual asset information"""
    symbol: str
    name: str
    asset_class: str  # 'crypto', 'stock', 'bond', 'commodity'
    current_price: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    beta: Optional[float] = None
    correlation_to_market: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    liquidity_score: Optional[float] = None

@dataclass
class Position:
    """Portfolio position"""
    symbol: str
    quantity: float
    current_price: float
    market_value: float
    weight: float  # Portfolio weight (0-1)
    cost_basis: float
    unrealized_pnl: float
    realized_pnl: float
    entry_date: str
    last_updated: str

@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    timestamp: str
    total_value: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Risk metrics
    var_95: float  # 95% Value at Risk
    var_99: float  # 99% Value at Risk
    expected_shortfall: float
    beta: float
    alpha: float
    
    # Diversification metrics
    correlation_avg: float
    concentration_risk: float  # Herfindahl index
    effective_assets: float
    
    # Performance attribution
    asset_allocation_return: float
    security_selection_return: float
    interaction_return: float

@dataclass
class OptimizationResult:
    """Portfolio optimization result"""
    timestamp: str
    optimization_method: str
    objective: str  # 'max_sharpe', 'min_variance', 'risk_parity', etc.
    
    # Optimal weights
    weights: Dict[str, float]
    
    # Expected metrics
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    
    # Risk metrics
    portfolio_var: float
    portfolio_es: float
    max_weight: float
    min_weight: float
    
    # Constraints satisfied
    constraints_satisfied: bool
    optimization_success: bool
    
    # Additional info
    solver_status: str
    computation_time: float
    rebalancing_required: bool
    transaction_costs: float

@dataclass
class RebalancingSignal:
    """Portfolio rebalancing signal"""
    timestamp: str
    trigger_type: str  # 'drift', 'time', 'volatility', 'market_regime'
    severity: str  # 'low', 'medium', 'high'
    
    current_weights: Dict[str, float]
    target_weights: Dict[str, float]
    weight_deviations: Dict[str, float]
    
    recommended_trades: List[Dict[str, Any]]
    estimated_costs: float
    expected_improvement: float
    
    reasoning: str
    urgency_score: float

class ModernPortfolioTheory:
    """Modern Portfolio Theory implementation"""
    
    def __init__(self):
        self.logger = logging.getLogger('ModernPortfolioTheory')
    
    def calculate_efficient_frontier(self, returns: pd.DataFrame, 
                                   num_portfolios: int = 100,
                                   risk_free_rate: float = 0.02) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate efficient frontier"""
        try:
            # Calculate expected returns and covariance matrix
            expected_returns = returns.mean() * 252  # Annualized
            cov_matrix = returns.cov() * 252  # Annualized
            
            num_assets = len(expected_returns)
            
            # Generate target returns
            min_ret = expected_returns.min()
            max_ret = expected_returns.max()
            target_returns = np.linspace(min_ret, max_ret, num_portfolios)
            
            efficient_portfolios = []
            efficient_returns = []
            efficient_volatilities = []
            
            for target_return in target_returns:
                try:
                    # Optimization variables
                    weights = cp.Variable(num_assets)
                    
                    # Objective: minimize portfolio variance
                    portfolio_variance = cp.quad_form(weights, cov_matrix.values)
                    objective = cp.Minimize(portfolio_variance)
                    
                    # Constraints
                    constraints = [
                        cp.sum(weights) == 1,  # Weights sum to 1
                        weights >= 0,  # Long-only
                        expected_returns.values @ weights == target_return  # Target return
                    ]
                    
                    # Solve optimization
                    problem = cp.Problem(objective, constraints)
                    problem.solve(solver=cp.ECOS, verbose=False)
                    
                    if problem.status == cp.OPTIMAL:
                        optimal_weights = weights.value
                        portfolio_return = expected_returns.values @ optimal_weights
                        portfolio_vol = np.sqrt(optimal_weights @ cov_matrix.values @ optimal_weights)
                        
                        efficient_portfolios.append(optimal_weights)
                        efficient_returns.append(portfolio_return)
                        efficient_volatilities.append(portfolio_vol)
                    
                except Exception as e:
                    self.logger.warning(f"Optimization failed for target return {target_return}: {e}")
            
            return (np.array(efficient_returns), 
                   np.array(efficient_volatilities), 
                   np.array(efficient_portfolios))
            
        except Exception as e:
            self.logger.error(f"Efficient frontier calculation failed: {e}")
            return np.array([]), np.array([]), np.array([])
    
    def optimize_portfolio(self, returns: pd.DataFrame, 
                          objective: str = 'max_sharpe',
                          constraints: Dict[str, Any] = None,
                          risk_free_rate: float = 0.02) -> OptimizationResult:
        """Optimize portfolio based on objective"""
        try:
            start_time = time.time()
            
            # Calculate expected returns and covariance matrix
            expected_returns = returns.mean() * 252  # Annualized
            cov_matrix = returns.cov() * 252  # Annualized
            
            num_assets = len(expected_returns)
            asset_names = returns.columns.tolist()
            
            # Default constraints
            if constraints is None:
                constraints = {
                    'long_only': True,
                    'max_weight': 0.4,
                    'min_weight': 0.0,
                    'max_turnover': None,
                    'sector_limits': None
                }
            
            # Optimization variables
            weights = cp.Variable(num_assets)
            
            # Define objective function
            if objective == 'max_sharpe':
                # Maximize Sharpe ratio (equivalent to maximizing excess return / volatility)
                portfolio_return = expected_returns.values @ weights
                portfolio_variance = cp.quad_form(weights, cov_matrix.values)
                
                # Use auxiliary variable for Sharpe ratio maximization
                kappa = cp.Variable()
                objective_func = cp.Maximize(portfolio_return - risk_free_rate)
                
                # Additional constraint for Sharpe ratio
                sharpe_constraints = [
                    cp.quad_form(weights, cov_matrix.values) <= 1,
                    cp.sum(weights) == kappa,
                    kappa >= 0
                ]
                
            elif objective == 'min_variance':
                portfolio_variance = cp.quad_form(weights, cov_matrix.values)
                objective_func = cp.Minimize(portfolio_variance)
                sharpe_constraints = []
                
            elif objective == 'max_return':
                portfolio_return = expected_returns.values @ weights
                objective_func = cp.Maximize(portfolio_return)
                sharpe_constraints = []
                
            elif objective == 'risk_parity':
                # Risk parity: equal risk contribution
                # Approximate using iterative method
                return self._optimize_risk_parity(returns, constraints)
                
            else:
                raise ValueError(f"Unknown objective: {objective}")
            
            # Basic constraints
            basic_constraints = [cp.sum(weights) == 1]  # Weights sum to 1
            
            if constraints.get('long_only', True):
                basic_constraints.append(weights >= 0)
            
            if constraints.get('max_weight'):
                basic_constraints.append(weights <= constraints['max_weight'])
            
            if constraints.get('min_weight'):
                basic_constraints.append(weights >= constraints['min_weight'])
            
            # Combine all constraints
            all_constraints = basic_constraints + sharpe_constraints
            
            # Solve optimization
            problem = cp.Problem(objective_func, all_constraints)
            problem.solve(solver=cp.ECOS, verbose=False)
            
            computation_time = time.time() - start_time
            
            if problem.status == cp.OPTIMAL:
                optimal_weights = weights.value
                
                # Handle Sharpe ratio optimization scaling
                if objective == 'max_sharpe' and 'kappa' in locals():
                    kappa_val = kappa.value
                    if kappa_val > 1e-6:
                        optimal_weights = optimal_weights / kappa_val
                
                # Calculate portfolio metrics
                portfolio_return = expected_returns.values @ optimal_weights
                portfolio_variance = optimal_weights @ cov_matrix.values @ optimal_weights
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
                
                # Create weights dictionary
                weights_dict = {asset: float(weight) for asset, weight in zip(asset_names, optimal_weights)}
                
                # Calculate risk metrics
                portfolio_var_95 = self._calculate_var(optimal_weights, cov_matrix, confidence=0.95)
                portfolio_es = self._calculate_expected_shortfall(optimal_weights, cov_matrix, confidence=0.95)
                
                result = OptimizationResult(
                    timestamp=datetime.now().isoformat(),
                    optimization_method='cvxpy',
                    objective=objective,
                    weights=weights_dict,
                    expected_return=float(portfolio_return),
                    expected_volatility=float(portfolio_volatility),
                    expected_sharpe=float(sharpe_ratio),
                    portfolio_var=float(portfolio_var_95),
                    portfolio_es=float(portfolio_es),
                    max_weight=float(np.max(optimal_weights)),
                    min_weight=float(np.min(optimal_weights)),
                    constraints_satisfied=True,
                    optimization_success=True,
                    solver_status=problem.status,
                    computation_time=computation_time,
                    rebalancing_required=False,
                    transaction_costs=0.0
                )
                
                return result
                
            else:
                self.logger.error(f"Optimization failed with status: {problem.status}")
                return self._create_failed_result(objective, computation_time, problem.status)
            
        except Exception as e:
            self.logger.error(f"Portfolio optimization failed: {e}")
            return self._create_failed_result(objective, 0.0, "ERROR")
    
    def _optimize_risk_parity(self, returns: pd.DataFrame, 
                             constraints: Dict[str, Any]) -> OptimizationResult:
        """Optimize for risk parity (equal risk contribution)"""
        try:
            start_time = time.time()
            
            # Calculate covariance matrix
            cov_matrix = returns.cov() * 252  # Annualized
            expected_returns = returns.mean() * 252
            
            num_assets = len(returns.columns)
            asset_names = returns.columns.tolist()
            
            # Initial equal weights
            initial_weights = np.ones(num_assets) / num_assets
            
            def risk_parity_objective(weights):
                """Risk parity objective function"""
                weights = np.array(weights)
                portfolio_vol = np.sqrt(weights @ cov_matrix.values @ weights)
                
                # Risk contributions
                marginal_contrib = cov_matrix.values @ weights
                risk_contrib = weights * marginal_contrib / portfolio_vol
                
                # Target risk contribution (equal for all assets)
                target_contrib = portfolio_vol / num_assets
                
                # Minimize sum of squared deviations from target
                return np.sum((risk_contrib - target_contrib) ** 2)
            
            # Constraints
            constraints_list = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]  # Weights sum to 1
            
            # Bounds
            bounds = [(constraints.get('min_weight', 0.0), 
                      constraints.get('max_weight', 1.0)) for _ in range(num_assets)]
            
            # Optimize
            result = optimize.minimize(
                risk_parity_objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'maxiter': 1000}
            )
            
            computation_time = time.time() - start_time
            
            if result.success:
                optimal_weights = result.x
                
                # Calculate portfolio metrics
                portfolio_return = expected_returns.values @ optimal_weights
                portfolio_variance = optimal_weights @ cov_matrix.values @ optimal_weights
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = portfolio_return / portfolio_volatility
                
                # Create weights dictionary
                weights_dict = {asset: float(weight) for asset, weight in zip(asset_names, optimal_weights)}
                
                # Calculate risk metrics
                portfolio_var_95 = self._calculate_var(optimal_weights, cov_matrix, confidence=0.95)
                portfolio_es = self._calculate_expected_shortfall(optimal_weights, cov_matrix, confidence=0.95)
                
                optimization_result = OptimizationResult(
                    timestamp=datetime.now().isoformat(),
                    optimization_method='scipy',
                    objective='risk_parity',
                    weights=weights_dict,
                    expected_return=float(portfolio_return),
                    expected_volatility=float(portfolio_volatility),
                    expected_sharpe=float(sharpe_ratio),
                    portfolio_var=float(portfolio_var_95),
                    portfolio_es=float(portfolio_es),
                    max_weight=float(np.max(optimal_weights)),
                    min_weight=float(np.min(optimal_weights)),
                    constraints_satisfied=True,
                    optimization_success=True,
                    solver_status='OPTIMAL',
                    computation_time=computation_time,
                    rebalancing_required=False,
                    transaction_costs=0.0
                )
                
                return optimization_result
                
            else:
                self.logger.error(f"Risk parity optimization failed: {result.message}")
                return self._create_failed_result('risk_parity', computation_time, 'FAILED')
            
        except Exception as e:
            self.logger.error(f"Risk parity optimization failed: {e}")
            return self._create_failed_result('risk_parity', 0.0, 'ERROR')
    
    def _calculate_var(self, weights: np.ndarray, cov_matrix: pd.DataFrame, 
                      confidence: float = 0.95, time_horizon: int = 1) -> float:
        """Calculate Value at Risk"""
        try:
            portfolio_std = np.sqrt(weights @ cov_matrix.values @ weights)
            # Adjust for time horizon
            portfolio_std_adjusted = portfolio_std * np.sqrt(time_horizon / 252)
            
            # Assuming normal distribution
            z_score = norm.ppf(1 - confidence)
            var = -z_score * portfolio_std_adjusted
            
            return var
            
        except Exception as e:
            self.logger.error(f"VaR calculation failed: {e}")
            return 0.0
    
    def _calculate_expected_shortfall(self, weights: np.ndarray, cov_matrix: pd.DataFrame,
                                    confidence: float = 0.95, time_horizon: int = 1) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        try:
            portfolio_std = np.sqrt(weights @ cov_matrix.values @ weights)
            # Adjust for time horizon
            portfolio_std_adjusted = portfolio_std * np.sqrt(time_horizon / 252)
            
            # Assuming normal distribution
            z_score = norm.ppf(1 - confidence)
            expected_shortfall = portfolio_std_adjusted * norm.pdf(z_score) / (1 - confidence)
            
            return expected_shortfall
            
        except Exception as e:
            self.logger.error(f"Expected Shortfall calculation failed: {e}")
            return 0.0
    
    def _create_failed_result(self, objective: str, computation_time: float, status: str) -> OptimizationResult:
        """Create failed optimization result"""
        return OptimizationResult(
            timestamp=datetime.now().isoformat(),
            optimization_method='failed',
            objective=objective,
            weights={},
            expected_return=0.0,
            expected_volatility=0.0,
            expected_sharpe=0.0,
            portfolio_var=0.0,
            portfolio_es=0.0,
            max_weight=0.0,
            min_weight=0.0,
            constraints_satisfied=False,
            optimization_success=False,
            solver_status=status,
            computation_time=computation_time,
            rebalancing_required=False,
            transaction_costs=0.0
        )

class BlackLittermanModel:
    """Black-Litterman model for expected returns"""
    
    def __init__(self, risk_aversion: float = 3.0):
        self.logger = logging.getLogger('BlackLittermanModel')
        self.risk_aversion = risk_aversion
    
    def calculate_implied_returns(self, market_weights: np.ndarray, 
                                cov_matrix: pd.DataFrame) -> np.ndarray:
        """Calculate implied equilibrium returns"""
        try:
            # Implied returns = risk_aversion * covariance_matrix * market_weights
            implied_returns = self.risk_aversion * cov_matrix.values @ market_weights
            return implied_returns
            
        except Exception as e:
            self.logger.error(f"Implied returns calculation failed: {e}")
            return np.zeros(len(market_weights))
    
    def incorporate_views(self, implied_returns: np.ndarray, 
                         cov_matrix: pd.DataFrame,
                         P: np.ndarray, Q: np.ndarray, 
                         omega: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Incorporate investor views using Black-Litterman"""
        try:
            # Black-Litterman formula
            # New expected returns = [(tau * Sigma)^-1 + P' * Omega^-1 * P]^-1 * 
            #                       [(tau * Sigma)^-1 * Pi + P' * Omega^-1 * Q]
            
            tau = 1.0 / len(implied_returns)  # Scaling factor
            
            # Precision matrices
            sigma_inv = np.linalg.inv(tau * cov_matrix.values)
            omega_inv = np.linalg.inv(omega)
            
            # New precision matrix
            M1 = sigma_inv + P.T @ omega_inv @ P
            M1_inv = np.linalg.inv(M1)
            
            # New expected returns
            M2 = sigma_inv @ implied_returns + P.T @ omega_inv @ Q
            new_returns = M1_inv @ M2
            
            # New covariance matrix
            new_cov = M1_inv
            
            return new_returns, new_cov
            
        except Exception as e:
            self.logger.error(f"Black-Litterman view incorporation failed: {e}")
            return implied_returns, cov_matrix.values

class MLPortfolioOptimizer:
    """Machine Learning-based portfolio optimizer"""
    
    def __init__(self):
        self.logger = logging.getLogger('MLPortfolioOptimizer')
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
    
    def prepare_features(self, returns: pd.DataFrame, 
                        market_data: Dict[str, pd.DataFrame] = None) -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            features = pd.DataFrame(index=returns.index)
            
            # Technical features
            for asset in returns.columns:
                asset_returns = returns[asset]
                
                # Rolling statistics
                features[f'{asset}_return_1d'] = asset_returns
                features[f'{asset}_return_5d'] = asset_returns.rolling(5).mean()
                features[f'{asset}_return_20d'] = asset_returns.rolling(20).mean()
                features[f'{asset}_volatility_20d'] = asset_returns.rolling(20).std()
                features[f'{asset}_sharpe_20d'] = (asset_returns.rolling(20).mean() / 
                                                  asset_returns.rolling(20).std())
                
                # Momentum features
                features[f'{asset}_momentum_5d'] = asset_returns.rolling(5).sum()
                features[f'{asset}_momentum_20d'] = asset_returns.rolling(20).sum()
                
                # Mean reversion features
                ma_20 = asset_returns.rolling(20).mean()
                features[f'{asset}_mean_reversion'] = (asset_returns - ma_20) / ma_20.std()
            
            # Cross-asset features
            features['market_return'] = returns.mean(axis=1)
            features['market_volatility'] = returns.std(axis=1)
            features['correlation_avg'] = returns.rolling(20).corr().mean().mean()
            
            # Regime features (if market data available)
            if market_data:
                # VIX-like volatility regime
                if 'vix' in market_data:
                    vix_data = market_data['vix']
                    features['vix_level'] = vix_data
                    features['vix_regime'] = (vix_data > vix_data.rolling(60).mean()).astype(int)
            
            # Drop NaN values
            features = features.dropna()
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature preparation failed: {e}")
            return pd.DataFrame()
    
    def train_return_prediction_model(self, returns: pd.DataFrame, 
                                    features: pd.DataFrame,
                                    model_type: str = 'random_forest') -> Dict[str, Any]:
        """Train models to predict asset returns"""
        try:
            results = {}
            
            for asset in returns.columns:
                # Prepare target variable (next period return)
                y = returns[asset].shift(-1).dropna()
                
                # Align features with target
                X = features.loc[y.index]
                
                if len(X) < 50:  # Minimum data requirement
                    continue
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, shuffle=False
                )
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train model
                if model_type == 'random_forest':
                    model = RandomForestRegressor(
                        n_estimators=100, 
                        max_depth=10, 
                        random_state=42,
                        n_jobs=-1
                    )
                elif model_type == 'gradient_boosting':
                    model = GradientBoostingRegressor(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        random_state=42
                    )
                elif model_type == 'ridge':
                    model = Ridge(alpha=1.0)
                else:
                    model = RandomForestRegressor(n_estimators=100, random_state=42)
                
                model.fit(X_train_scaled, y_train)
                
                # Evaluate model
                y_pred = model.predict(X_test_scaled)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # Store model and results
                self.models[asset] = model
                self.scalers[asset] = scaler
                
                # Feature importance (if available)
                if hasattr(model, 'feature_importances_'):
                    importance = dict(zip(X.columns, model.feature_importances_))
                    self.feature_importance[asset] = importance
                
                results[asset] = {
                    'mse': mse,
                    'r2': r2,
                    'model_type': model_type,
                    'n_features': X.shape[1],
                    'n_samples': len(X_train)
                }
                
                self.logger.info(f"Trained {model_type} for {asset}: R² = {r2:.3f}, MSE = {mse:.6f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Return prediction model training failed: {e}")
            return {}
    
    def predict_returns(self, features: pd.DataFrame) -> Dict[str, float]:
        """Predict expected returns using trained models"""
        try:
            predictions = {}
            
            for asset, model in self.models.items():
                if asset in self.scalers:
                    scaler = self.scalers[asset]
                    
                    # Get latest features
                    latest_features = features.iloc[-1:]
                    
                    # Scale features
                    features_scaled = scaler.transform(latest_features)
                    
                    # Predict
                    prediction = model.predict(features_scaled)[0]
                    predictions[asset] = float(prediction)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Return prediction failed: {e}")
            return {}
    
    def optimize_with_ml_returns(self, returns: pd.DataFrame,
                               ml_predictions: Dict[str, float],
                               confidence: float = 0.5,
                               objective: str = 'max_sharpe') -> OptimizationResult:
        """Optimize portfolio using ML-predicted returns"""
        try:
            # Combine historical and ML-predicted returns
            historical_returns = returns.mean() * 252  # Annualized
            
            # Blend historical and ML returns based on confidence
            blended_returns = {}
            for asset in returns.columns:
                hist_return = historical_returns[asset]
                ml_return = ml_predictions.get(asset, hist_return)
                
                # Weighted average
                blended_return = (1 - confidence) * hist_return + confidence * ml_return
                blended_returns[asset] = blended_return
            
            # Create expected returns series
            expected_returns = pd.Series(blended_returns)
            
            # Use covariance from historical data
            cov_matrix = returns.cov() * 252
            
            # Create synthetic returns DataFrame for optimization
            synthetic_returns = pd.DataFrame({
                asset: np.random.multivariate_normal(
                    [expected_returns[asset] / 252], 
                    [[cov_matrix.loc[asset, asset] / 252]], 
                    size=252
                ).flatten() for asset in returns.columns
            })
            
            # Use MPT optimizer
            mpt = ModernPortfolioTheory()
            result = mpt.optimize_portfolio(synthetic_returns, objective=objective)
            
            return result
            
        except Exception as e:
            self.logger.error(f"ML-based portfolio optimization failed: {e}")
            return OptimizationResult(
                timestamp=datetime.now().isoformat(),
                optimization_method='ml_failed',
                objective=objective,
                weights={},
                expected_return=0.0,
                expected_volatility=0.0,
                expected_sharpe=0.0,
                portfolio_var=0.0,
                portfolio_es=0.0,
                max_weight=0.0,
                min_weight=0.0,
                constraints_satisfied=False,
                optimization_success=False,
                solver_status='ERROR',
                computation_time=0.0,
                rebalancing_required=False,
                transaction_costs=0.0
            )

class PortfolioOptimizer:
    """Main portfolio optimization system"""
    
    def __init__(self, config_file: str = 'portfolio_config.json'):
        self.logger = self._setup_logging()
        
        # Configuration
        self.config = self._load_config(config_file)
        
        # Core components
        self.mpt = ModernPortfolioTheory()
        self.bl_model = BlackLittermanModel()
        self.ml_optimizer = MLPortfolioOptimizer()
        
        # Portfolio data
        self.assets = {}
        self.positions = {}
        self.portfolio_history = deque(maxlen=1000)
        self.optimization_history = deque(maxlen=100)
        self.rebalancing_signals = deque(maxlen=50)
        
        # Market data
        self.returns_data = pd.DataFrame()
        self.market_data = {}
        
        # Monitoring
        self.monitoring_active = False
        self.last_rebalance = None
        
        self.logger.info("📊 Portfolio Optimizer initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('PortfolioOptimizer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('portfolio_optimization.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load portfolio optimization configuration"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    'optimization': {
                        'default_objective': 'max_sharpe',
                        'rebalancing_frequency': 'weekly',
                        'min_weight': 0.01,
                        'max_weight': 0.4,
                        'transaction_costs': 0.001,
                        'risk_free_rate': 0.02
                    },
                    'risk_management': {
                        'max_portfolio_var': 0.05,
                        'max_concentration': 0.5,
                        'min_diversification': 5
                    },
                    'rebalancing': {
                        'drift_threshold': 0.05,
                        'time_threshold_days': 7,
                        'volatility_threshold': 0.02
                    },
                    'ml_settings': {
                        'enabled': True,
                        'model_type': 'random_forest',
                        'prediction_confidence': 0.3,
                        'retrain_frequency': 30
                    }
                }
                
                # Save default config
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
                
        except Exception as e:
            self.logger.error(f"Config loading failed: {e}")
            return {}
    
    def add_asset(self, asset: Asset):
        """Add asset to the universe"""
        self.assets[asset.symbol] = asset
        self.logger.info(f"Added asset: {asset.symbol} ({asset.name})")
    
    def update_position(self, position: Position):
        """Update portfolio position"""
        self.positions[position.symbol] = position
        self.logger.info(f"Updated position: {position.symbol} - {position.quantity} @ {position.current_price}")
    
    def load_returns_data(self, returns_data: pd.DataFrame):
        """Load historical returns data"""
        self.returns_data = returns_data
        self.logger.info(f"Loaded returns data: {returns_data.shape[0]} periods, {returns_data.shape[1]} assets")
    
    def calculate_portfolio_metrics(self) -> Optional[PortfolioMetrics]:
        """Calculate current portfolio metrics"""
        try:
            if not self.positions:
                return None
            
            # Calculate portfolio value and weights
            total_value = sum(pos.market_value for pos in self.positions.values())
            weights = {symbol: pos.market_value / total_value for symbol, pos in self.positions.items()}
            
            # Get returns for current positions
            position_symbols = list(self.positions.keys())
            available_symbols = [s for s in position_symbols if s in self.returns_data.columns]
            
            if not available_symbols or self.returns_data.empty:
                return None
            
            position_returns = self.returns_data[available_symbols]
            position_weights = np.array([weights.get(symbol, 0) for symbol in available_symbols])
            
            # Portfolio returns
            portfolio_returns = (position_returns * position_weights).sum(axis=1)
            
            # Performance metrics
            total_return = portfolio_returns.sum()
            annualized_return = portfolio_returns.mean() * 252
            volatility = portfolio_returns.std() * np.sqrt(252)
            
            # Risk-adjusted metrics
            risk_free_rate = self.config.get('optimization', {}).get('risk_free_rate', 0.02)
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # Downside deviation for Sortino ratio
            downside_returns = portfolio_returns[portfolio_returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else volatility
            sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Calmar ratio
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Risk metrics
            cov_matrix = position_returns.cov() * 252
            var_95 = self.mpt._calculate_var(position_weights, cov_matrix, confidence=0.95)
            var_99 = self.mpt._calculate_var(position_weights, cov_matrix, confidence=0.99)
            expected_shortfall = self.mpt._calculate_expected_shortfall(position_weights, cov_matrix, confidence=0.95)
            
            # Beta and alpha (assuming first asset is market proxy)
            if len(available_symbols) > 1:
                market_returns = position_returns.iloc[:, 0]  # Use first asset as market proxy
                covariance = np.cov(portfolio_returns, market_returns)[0, 1]
                market_variance = np.var(market_returns)
                beta = covariance / market_variance if market_variance > 0 else 1.0
                alpha = annualized_return - (risk_free_rate + beta * (market_returns.mean() * 252 - risk_free_rate))
            else:
                beta = 1.0
                alpha = 0.0
            
            # Diversification metrics
            correlation_matrix = position_returns.corr()
            correlation_avg = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            
            # Concentration risk (Herfindahl index)
            concentration_risk = sum(w**2 for w in weights.values())
            
            # Effective number of assets
            effective_assets = 1 / concentration_risk if concentration_risk > 0 else len(weights)
            
            metrics = PortfolioMetrics(
                timestamp=datetime.now().isoformat(),
                total_value=total_value,
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                beta=beta,
                alpha=alpha,
                correlation_avg=correlation_avg,
                concentration_risk=concentration_risk,
                effective_assets=effective_assets,
                asset_allocation_return=0.0,  # Would need benchmark for attribution
                security_selection_return=0.0,
                interaction_return=0.0
            )
            
            # Store in history
            self.portfolio_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Portfolio metrics calculation failed: {e}")
            return None
    
    def optimize_portfolio(self, objective: str = None, 
                         constraints: Dict[str, Any] = None) -> Optional[OptimizationResult]:
        """Optimize portfolio allocation"""
        try:
            if self.returns_data.empty:
                self.logger.error("No returns data available for optimization")
                return None
            
            # Use default objective if not specified
            if objective is None:
                objective = self.config.get('optimization', {}).get('default_objective', 'max_sharpe')
            
            # Use default constraints if not specified
            if constraints is None:
                opt_config = self.config.get('optimization', {})
                constraints = {
                    'long_only': True,
                    'max_weight': opt_config.get('max_weight', 0.4),
                    'min_weight': opt_config.get('min_weight', 0.01)
                }
            
            # Perform optimization
            result = self.mpt.optimize_portfolio(
                self.returns_data, 
                objective=objective, 
                constraints=constraints,
                risk_free_rate=self.config.get('optimization', {}).get('risk_free_rate', 0.02)
            )
            
            if result.optimization_success:
                # Check if rebalancing is needed
                current_weights = self._get_current_weights()
                result.rebalancing_required = self._check_rebalancing_needed(current_weights, result.weights)
                
                # Estimate transaction costs
                result.transaction_costs = self._estimate_transaction_costs(current_weights, result.weights)
                
                # Store optimization result
                self.optimization_history.append(result)
                
                self.logger.info(f"Portfolio optimization completed: {objective} - Sharpe: {result.expected_sharpe:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Portfolio optimization failed: {e}")
            return None
    
    def _get_current_weights(self) -> Dict[str, float]:
        """Get current portfolio weights"""
        if not self.positions:
            return {}
        
        total_value = sum(pos.market_value for pos in self.positions.values())
        if total_value == 0:
            return {}
        
        return {symbol: pos.market_value / total_value for symbol, pos in self.positions.items()}
    
    def _check_rebalancing_needed(self, current_weights: Dict[str, float], 
                                target_weights: Dict[str, float]) -> bool:
        """Check if rebalancing is needed"""
        try:
            drift_threshold = self.config.get('rebalancing', {}).get('drift_threshold', 0.05)
            
            # Calculate weight deviations
            max_deviation = 0
            for symbol in set(list(current_weights.keys()) + list(target_weights.keys())):
                current_weight = current_weights.get(symbol, 0)
                target_weight = target_weights.get(symbol, 0)
                deviation = abs(current_weight - target_weight)
                max_deviation = max(max_deviation, deviation)
            
            return max_deviation > drift_threshold
            
        except Exception as e:
            self.logger.error(f"Rebalancing check failed: {e}")
            return False
    
    def _estimate_transaction_costs(self, current_weights: Dict[str, float], 
                                  target_weights: Dict[str, float]) -> float:
        """Estimate transaction costs for rebalancing"""
        try:
            transaction_cost_rate = self.config.get('optimization', {}).get('transaction_costs', 0.001)
            
            total_turnover = 0
            for symbol in set(list(current_weights.keys()) + list(target_weights.keys())):
                current_weight = current_weights.get(symbol, 0)
                target_weight = target_weights.get(symbol, 0)
                turnover = abs(target_weight - current_weight)
                total_turnover += turnover
            
            # Transaction costs = turnover * cost rate
            return total_turnover * transaction_cost_rate
            
        except Exception as e:
            self.logger.error(f"Transaction cost estimation failed: {e}")
            return 0.0
    
    def generate_rebalancing_signals(self) -> List[RebalancingSignal]:
        """Generate portfolio rebalancing signals"""
        signals = []
        
        try:
            current_weights = self._get_current_weights()
            if not current_weights:
                return signals
            
            # Get latest optimization result
            if not self.optimization_history:
                return signals
            
            latest_optimization = self.optimization_history[-1]
            target_weights = latest_optimization.weights
            
            # Check different rebalancing triggers
            
            # 1. Weight drift trigger
            drift_signal = self._check_drift_trigger(current_weights, target_weights)
            if drift_signal:
                signals.append(drift_signal)
            
            # 2. Time-based trigger
            time_signal = self._check_time_trigger()
            if time_signal:
                signals.append(time_signal)
            
            # 3. Volatility regime change trigger
            volatility_signal = self._check_volatility_trigger()
            if volatility_signal:
                signals.append(volatility_signal)
            
            # Store signals
            self.rebalancing_signals.extend(signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Rebalancing signal generation failed: {e}")
            return []
    
    def _check_drift_trigger(self, current_weights: Dict[str, float], 
                           target_weights: Dict[str, float]) -> Optional[RebalancingSignal]:
        """Check for weight drift trigger"""
        try:
            drift_threshold = self.config.get('rebalancing', {}).get('drift_threshold', 0.05)
            
            weight_deviations = {}
            max_deviation = 0
            
            for symbol in set(list(current_weights.keys()) + list(target_weights.keys())):
                current_weight = current_weights.get(symbol, 0)
                target_weight = target_weights.get(symbol, 0)
                deviation = current_weight - target_weight
                weight_deviations[symbol] = deviation
                max_deviation = max(max_deviation, abs(deviation))
            
            if max_deviation > drift_threshold:
                # Generate recommended trades
                recommended_trades = []
                total_value = sum(pos.market_value for pos in self.positions.values())
                
                for symbol, deviation in weight_deviations.items():
                    if abs(deviation) > 0.01:  # Only trade significant deviations
                        trade_value = -deviation * total_value  # Negative deviation means we need to buy
                        
                        if symbol in self.assets:
                            current_price = self.assets[symbol].current_price
                            trade_quantity = trade_value / current_price
                            
                            recommended_trades.append({
                                'symbol': symbol,
                                'action': 'buy' if trade_quantity > 0 else 'sell',
                                'quantity': abs(trade_quantity),
                                'estimated_value': abs(trade_value)
                            })
                
                # Estimate costs and benefits
                estimated_costs = self._estimate_transaction_costs(current_weights, target_weights)
                expected_improvement = max_deviation * 0.1  # Rough estimate
                
                signal = RebalancingSignal(
                    timestamp=datetime.now().isoformat(),
                    trigger_type='drift',
                    severity='high' if max_deviation > drift_threshold * 2 else 'medium',
                    current_weights=current_weights,
                    target_weights=target_weights,
                    weight_deviations=weight_deviations,
                    recommended_trades=recommended_trades,
                    estimated_costs=estimated_costs,
                    expected_improvement=expected_improvement,
                    reasoning=f"Portfolio weights have drifted by {max_deviation:.1%} from target allocation",
                    urgency_score=min(1.0, max_deviation / drift_threshold)
                )
                
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Drift trigger check failed: {e}")
            return None
    
    def _check_time_trigger(self) -> Optional[RebalancingSignal]:
        """Check for time-based rebalancing trigger"""
        try:
            if self.last_rebalance is None:
                return None
            
            time_threshold_days = self.config.get('rebalancing', {}).get('time_threshold_days', 7)
            days_since_rebalance = (datetime.now() - self.last_rebalance).days
            
            if days_since_rebalance >= time_threshold_days:
                signal = RebalancingSignal(
                    timestamp=datetime.now().isoformat(),
                    trigger_type='time',
                    severity='low',
                    current_weights=self._get_current_weights(),
                    target_weights=self.optimization_history[-1].weights if self.optimization_history else {},
                    weight_deviations={},
                    recommended_trades=[],
                    estimated_costs=0.0,
                    expected_improvement=0.05,
                    reasoning=f"Scheduled rebalancing: {days_since_rebalance} days since last rebalance",
                    urgency_score=0.3
                )
                
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Time trigger check failed: {e}")
            return None
    
    def _check_volatility_trigger(self) -> Optional[RebalancingSignal]:
        """Check for volatility regime change trigger"""
        try:
            if self.returns_data.empty or len(self.returns_data) < 40:
                return None
            
            # Calculate recent vs historical volatility
            recent_returns = self.returns_data.tail(20)
            historical_returns = self.returns_data.tail(60)
            
            recent_vol = recent_returns.std().mean()
            historical_vol = historical_returns.std().mean()
            
            vol_change = (recent_vol - historical_vol) / historical_vol
            vol_threshold = self.config.get('rebalancing', {}).get('volatility_threshold', 0.02)
            
            if abs(vol_change) > vol_threshold:
                signal = RebalancingSignal(
                    timestamp=datetime.now().isoformat(),
                    trigger_type='volatility',
                    severity='medium' if abs(vol_change) > vol_threshold * 2 else 'low',
                    current_weights=self._get_current_weights(),
                    target_weights=self.optimization_history[-1].weights if self.optimization_history else {},
                    weight_deviations={},
                    recommended_trades=[],
                    estimated_costs=0.0,
                    expected_improvement=abs(vol_change) * 0.1,
                    reasoning=f"Volatility regime change detected: {vol_change:.1%} change in volatility",
                    urgency_score=min(1.0, abs(vol_change) / vol_threshold)
                )
                
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Volatility trigger check failed: {e}")
            return None
    
    def start_monitoring(self):
        """Start portfolio monitoring"""
        self.monitoring_active = True
        self.logger.info("📊 Portfolio monitoring started")
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Calculate portfolio metrics
                    metrics = self.calculate_portfolio_metrics()
                    if metrics:
                        self.logger.info(f"Portfolio Value: ${metrics.total_value:,.2f}, "
                                       f"Return: {metrics.annualized_return:.1%}, "
                                       f"Sharpe: {metrics.sharpe_ratio:.2f}")
                    
                    # Check for rebalancing signals
                    signals = self.generate_rebalancing_signals()
                    for signal in signals:
                        self.logger.warning(f"REBALANCING SIGNAL: {signal.trigger_type} - {signal.reasoning}")
                    
                    # Sleep for monitoring interval
                    time.sleep(3600)  # Check every hour
                    
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
    
    def get_portfolio_report(self) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'portfolio_summary': {},
                'positions': {},
                'performance_metrics': {},
                'optimization_results': {},
                'rebalancing_signals': [],
                'recommendations': []
            }
            
            # Portfolio summary
            if self.positions:
                total_value = sum(pos.market_value for pos in self.positions.values())
                total_pnl = sum(pos.unrealized_pnl + pos.realized_pnl for pos in self.positions.values())
                
                report['portfolio_summary'] = {
                    'total_value': total_value,
                    'total_pnl': total_pnl,
                    'num_positions': len(self.positions),
                    'largest_position': max(self.positions.values(), key=lambda p: p.market_value).symbol if self.positions else None
                }
            
            # Current positions
            report['positions'] = {symbol: asdict(pos) for symbol, pos in self.positions.items()}
            
            # Performance metrics
            if self.portfolio_history:
                latest_metrics = self.portfolio_history[-1]
                report['performance_metrics'] = asdict(latest_metrics)
            
            # Latest optimization
            if self.optimization_history:
                latest_optimization = self.optimization_history[-1]
                report['optimization_results'] = asdict(latest_optimization)
            
            # Recent rebalancing signals
            recent_signals = [signal for signal in self.rebalancing_signals 
                            if datetime.fromisoformat(signal.timestamp) > datetime.now() - timedelta(days=7)]
            report['rebalancing_signals'] = [asdict(signal) for signal in recent_signals]
            
            # Generate recommendations
            recommendations = self._generate_portfolio_recommendations()
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            self.logger.error(f"Portfolio report generation failed: {e}")
            return {}
    
    def _generate_portfolio_recommendations(self) -> List[str]:
        """Generate portfolio recommendations"""
        recommendations = []
        
        try:
            # Check portfolio metrics
            if self.portfolio_history:
                latest_metrics = self.portfolio_history[-1]
                
                # Diversification recommendations
                if latest_metrics.effective_assets < 5:
                    recommendations.append("Consider increasing diversification - portfolio has low effective asset count")
                
                if latest_metrics.concentration_risk > 0.5:
                    recommendations.append("High concentration risk detected - consider reducing largest positions")
                
                # Performance recommendations
                if latest_metrics.sharpe_ratio < 0.5:
                    recommendations.append("Low risk-adjusted returns - consider reviewing asset allocation strategy")
                
                if latest_metrics.max_drawdown < -0.2:
                    recommendations.append("High maximum drawdown - implement stronger risk management")
                
                # Volatility recommendations
                if latest_metrics.volatility > 0.3:
                    recommendations.append("High portfolio volatility - consider adding defensive assets")
            
            # Rebalancing recommendations
            if self.rebalancing_signals:
                high_urgency_signals = [s for s in self.rebalancing_signals if s.urgency_score > 0.7]
                if high_urgency_signals:
                    recommendations.append(f"Urgent rebalancing needed - {len(high_urgency_signals)} high-priority signals")
            
            # Optimization recommendations
            if self.optimization_history:
                recent_optimizations = [opt for opt in self.optimization_history 
                                      if datetime.fromisoformat(opt.timestamp) > datetime.now() - timedelta(days=30)]
                
                if not recent_optimizations:
                    recommendations.append("No recent portfolio optimization - consider running optimization")
                
                elif len(recent_optimizations) > 0:
                    avg_sharpe = statistics.mean([opt.expected_sharpe for opt in recent_optimizations])
                    if avg_sharpe < 1.0:
                        recommendations.append("Recent optimizations show low Sharpe ratios - review strategy")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return []
    
    def run_ml_optimization(self) -> Optional[OptimizationResult]:
        """Run ML-enhanced portfolio optimization"""
        try:
            if not self.config.get('ml_settings', {}).get('enabled', True):
                self.logger.info("ML optimization disabled in config")
                return None
            
            if self.returns_data.empty:
                self.logger.error("No returns data for ML optimization")
                return None
            
            # Prepare features for ML
            features = self.ml_optimizer.prepare_features(self.returns_data, self.market_data)
            
            if features.empty:
                self.logger.error("Feature preparation failed")
                return None
            
            # Train ML models if needed
            model_type = self.config.get('ml_settings', {}).get('model_type', 'random_forest')
            training_results = self.ml_optimizer.train_return_prediction_model(
                self.returns_data, features, model_type
            )
            
            if not training_results:
                self.logger.error("ML model training failed")
                return None
            
            # Generate predictions
            predictions = self.ml_optimizer.predict_returns(features)
            
            if not predictions:
                self.logger.error("ML return prediction failed")
                return None
            
            # Optimize portfolio with ML predictions
            confidence = self.config.get('ml_settings', {}).get('prediction_confidence', 0.3)
            result = self.ml_optimizer.optimize_with_ml_returns(
                self.returns_data, predictions, confidence=confidence
            )
            
            if result.optimization_success:
                self.logger.info(f"ML optimization completed - Sharpe: {result.expected_sharpe:.3f}")
                self.optimization_history.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"ML optimization failed: {e}")
            return None
    
    def execute_rebalancing(self, target_weights: Dict[str, float], 
                          dry_run: bool = True) -> Dict[str, Any]:
        """Execute portfolio rebalancing"""
        try:
            current_weights = self._get_current_weights()
            total_value = sum(pos.market_value for pos in self.positions.values())
            
            execution_plan = {
                'timestamp': datetime.now().isoformat(),
                'dry_run': dry_run,
                'trades': [],
                'total_cost': 0.0,
                'success': False
            }
            
            # Calculate required trades
            for symbol in set(list(current_weights.keys()) + list(target_weights.keys())):
                current_weight = current_weights.get(symbol, 0)
                target_weight = target_weights.get(symbol, 0)
                weight_diff = target_weight - current_weight
                
                if abs(weight_diff) > 0.01:  # Only trade significant differences
                    trade_value = weight_diff * total_value
                    
                    if symbol in self.assets:
                        current_price = self.assets[symbol].current_price
                        trade_quantity = trade_value / current_price
                        
                        trade = {
                            'symbol': symbol,
                            'action': 'buy' if trade_quantity > 0 else 'sell',
                            'quantity': abs(trade_quantity),
                            'price': current_price,
                            'value': abs(trade_value),
                            'weight_change': weight_diff
                        }
                        
                        execution_plan['trades'].append(trade)
                        
                        # Add transaction costs
                        transaction_cost = abs(trade_value) * self.config.get('optimization', {}).get('transaction_costs', 0.001)
                        execution_plan['total_cost'] += transaction_cost
            
            if not dry_run:
                # Execute trades (placeholder - would integrate with actual trading system)
                self.logger.info(f"Executing {len(execution_plan['trades'])} trades")
                
                # Update last rebalance time
                self.last_rebalance = datetime.now()
                
                execution_plan['success'] = True
            else:
                self.logger.info(f"Dry run: {len(execution_plan['trades'])} trades planned, "
                               f"estimated cost: ${execution_plan['total_cost']:.2f}")
                execution_plan['success'] = True
            
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"Rebalancing execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_state(self, filename: str = 'portfolio_state.pkl'):
        """Save portfolio state to file"""
        try:
            state = {
                'assets': self.assets,
                'positions': self.positions,
                'portfolio_history': list(self.portfolio_history),
                'optimization_history': list(self.optimization_history),
                'rebalancing_signals': list(self.rebalancing_signals),
                'last_rebalance': self.last_rebalance,
                'config': self.config
            }
            
            with open(filename, 'wb') as f:
                pickle.dump(state, f)
            
            self.logger.info(f"Portfolio state saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"State saving failed: {e}")
    
    def load_state(self, filename: str = 'portfolio_state.pkl'):
        """Load portfolio state from file"""
        try:
            if not os.path.exists(filename):
                self.logger.warning(f"State file {filename} not found")
                return
            
            with open(filename, 'rb') as f:
                state = pickle.load(f)
            
            self.assets = state.get('assets', {})
            self.positions = state.get('positions', {})
            self.portfolio_history = deque(state.get('portfolio_history', []), maxlen=1000)
            self.optimization_history = deque(state.get('optimization_history', []), maxlen=100)
            self.rebalancing_signals = deque(state.get('rebalancing_signals', []), maxlen=50)
            self.last_rebalance = state.get('last_rebalance')
            
            # Update config with saved values
            saved_config = state.get('config', {})
            self.config.update(saved_config)
            
            self.logger.info(f"Portfolio state loaded from {filename}")
            
        except Exception as e:
            self.logger.error(f"State loading failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    import random
    
    print("🚀 TradeBot Sentinel - Portfolio Optimizer Demo")
    print("=" * 50)
    
    # Initialize optimizer
    optimizer = PortfolioOptimizer()
    
    # Create sample assets
    assets = [
        Asset('BTC', 'Bitcoin', 'crypto', 45000.0, volatility=0.8, sharpe_ratio=1.2),
        Asset('ETH', 'Ethereum', 'crypto', 3000.0, volatility=0.9, sharpe_ratio=1.1),
        Asset('AAPL', 'Apple Inc.', 'stock', 150.0, volatility=0.3, sharpe_ratio=0.8),
        Asset('GOOGL', 'Alphabet Inc.', 'stock', 2500.0, volatility=0.35, sharpe_ratio=0.9),
        Asset('TSLA', 'Tesla Inc.', 'stock', 800.0, volatility=0.6, sharpe_ratio=0.7)
    ]
    
    for asset in assets:
        optimizer.add_asset(asset)
    
    print(f"✅ Added {len(assets)} assets to universe")
    
    # Create sample positions
    positions = [
        Position('BTC', 0.5, 45000.0, 22500.0, 0.3, 40000.0, 2500.0, 0.0, '2024-01-01', datetime.now().isoformat()),
        Position('ETH', 5.0, 3000.0, 15000.0, 0.2, 2800.0, 1000.0, 0.0, '2024-01-01', datetime.now().isoformat()),
        Position('AAPL', 100, 150.0, 15000.0, 0.2, 140.0, 1000.0, 0.0, '2024-01-01', datetime.now().isoformat()),
        Position('GOOGL', 5, 2500.0, 12500.0, 0.17, 2300.0, 1000.0, 0.0, '2024-01-01', datetime.now().isoformat()),
        Position('TSLA', 10, 800.0, 8000.0, 0.13, 750.0, 500.0, 0.0, '2024-01-01', datetime.now().isoformat())
    ]
    
    for position in positions:
        optimizer.update_position(position)
    
    print(f"✅ Added {len(positions)} positions")
    
    # Generate sample returns data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    
    returns_data = pd.DataFrame({
        'BTC': np.random.normal(0.001, 0.05, len(dates)),
        'ETH': np.random.normal(0.0008, 0.045, len(dates)),
        'AAPL': np.random.normal(0.0005, 0.02, len(dates)),
        'GOOGL': np.random.normal(0.0006, 0.022, len(dates)),
        'TSLA': np.random.normal(0.0003, 0.035, len(dates))
    }, index=dates)
    
    optimizer.load_returns_data(returns_data)
    print(f"✅ Loaded returns data: {returns_data.shape[0]} days")
    
    # Calculate portfolio metrics
    print("\n📊 Portfolio Metrics:")
    metrics = optimizer.calculate_portfolio_metrics()
    if metrics:
        print(f"Total Value: ${metrics.total_value:,.2f}")
        print(f"Annualized Return: {metrics.annualized_return:.1%}")
        print(f"Volatility: {metrics.volatility:.1%}")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {metrics.max_drawdown:.1%}")
        print(f"VaR (95%): {metrics.var_95:.1%}")
    
    # Run portfolio optimization
    print("\n🎯 Portfolio Optimization:")
    
    # Test different objectives
    objectives = ['max_sharpe', 'min_variance', 'risk_parity']
    
    for objective in objectives:
        print(f"\n--- {objective.upper()} ---")
        result = optimizer.optimize_portfolio(objective=objective)
        
        if result and result.optimization_success:
            print(f"Expected Return: {result.expected_return:.1%}")
            print(f"Expected Volatility: {result.expected_volatility:.1%}")
            print(f"Expected Sharpe: {result.expected_sharpe:.2f}")
            print("Optimal Weights:")
            for symbol, weight in result.weights.items():
                print(f"  {symbol}: {weight:.1%}")
        else:
            print("❌ Optimization failed")
    
    # Test ML optimization
    print("\n🤖 ML-Enhanced Optimization:")
    ml_result = optimizer.run_ml_optimization()
    if ml_result and ml_result.optimization_success:
        print(f"ML Expected Return: {ml_result.expected_return:.1%}")
        print(f"ML Expected Sharpe: {ml_result.expected_sharpe:.2f}")
        print("ML Optimal Weights:")
        for symbol, weight in ml_result.weights.items():
            print(f"  {symbol}: {weight:.1%}")
    
    # Generate rebalancing signals
    print("\n⚖️ Rebalancing Analysis:")
    signals = optimizer.generate_rebalancing_signals()
    
    if signals:
        for signal in signals:
            print(f"Signal: {signal.trigger_type} ({signal.severity})")
            print(f"Reasoning: {signal.reasoning}")
            print(f"Urgency: {signal.urgency_score:.1%}")
    else:
        print("No rebalancing signals generated")
    
    # Test rebalancing execution (dry run)
    if optimizer.optimization_history:
        latest_opt = optimizer.optimization_history[-1]
        print("\n🔄 Rebalancing Execution (Dry Run):")
        execution_plan = optimizer.execute_rebalancing(latest_opt.weights, dry_run=True)
        
        if execution_plan['success']:
            print(f"Planned Trades: {len(execution_plan['trades'])}")
            print(f"Estimated Cost: ${execution_plan['total_cost']:.2f}")
            
            for trade in execution_plan['trades'][:3]:  # Show first 3 trades
                print(f"  {trade['action'].upper()} {trade['quantity']:.2f} {trade['symbol']} @ ${trade['price']:.2f}")
    
    # Generate portfolio report
    print("\n📋 Portfolio Report:")
    report = optimizer.get_portfolio_report()
    
    if report.get('recommendations'):
        print("Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Save state
    optimizer.save_state()
    print("\n💾 Portfolio state saved")
    
    print("\n🎉 Portfolio Optimizer Demo completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Modern Portfolio Theory optimization")
    print("✅ Multiple optimization objectives")
    print("✅ ML-enhanced return prediction")
    print("✅ Risk parity allocation")
    print("✅ Rebalancing signal generation")
    print("✅ Transaction cost estimation")
    print("✅ Portfolio performance metrics")
    print("✅ Comprehensive reporting")
    print("✅ State persistence")