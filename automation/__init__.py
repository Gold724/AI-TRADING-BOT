#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Advanced Automation Layer
Modular automation components for live trading, monitoring, and reporting
"""

__version__ = "1.0.0"
__author__ = "TradeBot Sentinel Team"

from .trade_executor import TradeExecutor
from .strategy_engine import StrategyEngine
from .monitoring_dashboard import MonitoringDashboard
from .alert_system import AlertSystem
from .backtesting_engine import BacktestingEngine
from .continuous_improvement import ContinuousImprovement

__all__ = [
    'TradeExecutor',
    'StrategyEngine', 
    'MonitoringDashboard',
    'AlertSystem',
    'BacktestingEngine',
    'ContinuousImprovement'
]