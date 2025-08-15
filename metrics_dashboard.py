# metrics_dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Try to import from other modules
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_strategy_performance(self, strategy_name):
            return {}
        def get_daily_drawdown(self):
            return 0.0

try:
    from risk_control import RiskController
except ImportError:
    # Define a minimal version if the import fails
    class RiskController:
        def get_risk_config(self, strategy_name):
            return {}

try:
    from strategy_manager import StrategyManager
except ImportError:
    # Define a minimal version if the import fails
    class StrategyManager:
        def get_enabled_strategies(self):
            return []
        def get_strategy_config(self, strategy_name):
            return {}

try:
    from emergency_protocol import EmergencyProtocol
except ImportError:
    # Define a minimal version if the import fails
    class EmergencyProtocol:
        def load_emergency_state(self):
            return {"active": False, "level": "normal"}
        def load_emergency_log(self):
            return []

try:
    from news_guard import NewsGuard
except ImportError:
    # Define a minimal version if the import fails
    class NewsGuard:
        def get_upcoming_events(self):
            return []
        def get_recent_events(self):
            return []

# Constants
DATA_DIR = os.path.join("data")
TRADE_HISTORY_FILE = os.path.join(DATA_DIR, "trade_history.json")
STRATEGY_STATS_FILE = os.path.join(DATA_DIR, "strategy_stats.json")
RISK_CONFIG_FILE = os.path.join(DATA_DIR, "risk_config.json")
STRATEGY_CONFIG_FILE = os.path.join(DATA_DIR, "strategy_config.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

# Set page config
st.set_page_config(
    page_title="TRAE Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
evaluator = TradePerformanceEvaluator(TRADE_HISTORY_FILE, STRATEGY_STATS_FILE)
risk_controller = RiskController()
strategy_manager = StrategyManager()
emergency_protocol = EmergencyProtocol()
news_guard = NewsGuard()

# Helper functions
def load_trade_history() -> List[Dict]:
    """Load trade history from file

    Returns:
        List[Dict]: List of trade records
    """
    try:
        if os.path.exists(TRADE_HISTORY_FILE):
            with open(TRADE_HISTORY_FILE, "r") as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        st.error(f"Error loading trade history: {e}")
        return []

def load_strategy_stats() -> Dict:
    """Load strategy statistics from file

    Returns:
        Dict: Strategy statistics
    """
    try:
        if os.path.exists(STRATEGY_STATS_FILE):
            with open(STRATEGY_STATS_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        st.error(f"Error loading strategy statistics: {e}")
        return {}

def load_risk_config() -> Dict:
    """Load risk configuration from file

    Returns:
        Dict: Risk configuration
    """
    try:
        if os.path.exists(RISK_CONFIG_FILE):
            with open(RISK_CONFIG_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        st.error(f"Error loading risk configuration: {e}")
        return {}

def load_strategy_config() -> Dict:
    """Load strategy configuration from file

    Returns:
        Dict: Strategy configuration
    """
    try:
        if os.path.exists(STRATEGY_CONFIG_FILE):
            with open(STRATEGY_CONFIG_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        st.error(f"Error loading strategy configuration: {e}")
        return {}

def get_trades_df(trades: List[Dict]) -> pd.DataFrame:
    """Convert trades list to DataFrame

    Args:
        trades (List[Dict]): List of trade records

    Returns:
        pd.DataFrame: DataFrame of trades
    """
    if not trades:
        return pd.DataFrame()
        
    df = pd.DataFrame(trades)
    
    # Convert timestamp to datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Convert open_time and close_time to datetime if they exist
    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"])
    if "close_time" in df.columns:
        df["close_time"] = pd.to_datetime(df["close_time"])
        
    return df

def get_daily_pnl(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily P&L from trades

    Args:
        trades_df (pd.DataFrame): DataFrame of trades

    Returns:
        pd.DataFrame: Daily P&L
    """
    if trades_df.empty:
        return pd.DataFrame()
        
    # Use close_time if available, otherwise use timestamp
    time_col = "close_time" if "close_time" in trades_df.columns else "timestamp"
    
    if time_col not in trades_df.columns:
        return pd.DataFrame()
        
    # Group by date and sum profit_loss
    daily_pnl = trades_df.groupby(trades_df[time_col].dt.date)["profit_loss"].sum().reset_index()
    daily_pnl.columns = ["date", "profit_loss"]
    
    # Convert date to datetime
    daily_pnl["date"] = pd.to_datetime(daily_pnl["date"])
    
    # Sort by date
    daily_pnl = daily_pnl.sort_values("date")
    
    # Calculate cumulative P&L
    daily_pnl["cumulative_pnl"] = daily_pnl["profit_loss"].cumsum()
    
    return daily_pnl

def get_strategy_performance(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate strategy performance metrics

    Args:
        trades_df (pd.DataFrame): DataFrame of trades

    Returns:
        pd.DataFrame: Strategy performance metrics
    """
    if trades_df.empty or "strategy" not in trades_df.columns:
        return pd.DataFrame()
        
    # Group by strategy
    strategy_performance = trades_df.groupby("strategy").agg(
        trade_count=("profit_loss", "count"),
        win_count=("profit_loss", lambda x: (x > 0).sum()),
        loss_count=("profit_loss", lambda x: (x <= 0).sum()),
        total_profit=("profit_loss", lambda x: x[x > 0].sum()),
        total_loss=("profit_loss", lambda x: x[x <= 0].sum()),
        net_profit=("profit_loss", "sum"),
        avg_profit=("profit_loss", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
        avg_loss=("profit_loss", lambda x: x[x <= 0].mean() if (x <= 0).any() else 0),
    ).reset_index()
    
    # Calculate win rate and profit factor
    strategy_performance["win_rate"] = strategy_performance["win_count"] / strategy_performance["trade_count"] * 100
    strategy_performance["profit_factor"] = abs(strategy_performance["total_profit"] / strategy_performance["total_loss"]) if strategy_performance["total_loss"].any() else float("inf")
    
    return strategy_performance

def get_symbol_performance(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate symbol performance metrics

    Args:
        trades_df (pd.DataFrame): DataFrame of trades

    Returns:
        pd.DataFrame: Symbol performance metrics
    """
    if trades_df.empty or "symbol" not in trades_df.columns:
        return pd.DataFrame()
        
    # Group by symbol
    symbol_performance = trades_df.groupby("symbol").agg(
        trade_count=("profit_loss", "count"),
        win_count=("profit_loss", lambda x: (x > 0).sum()),
        loss_count=("profit_loss", lambda x: (x <= 0).sum()),
        total_profit=("profit_loss", lambda x: x[x > 0].sum()),
        total_loss=("profit_loss", lambda x: x[x <= 0].sum()),
        net_profit=("profit_loss", "sum"),
        avg_profit=("profit_loss", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
        avg_loss=("profit_loss", lambda x: x[x <= 0].mean() if (x <= 0).any() else 0),
    ).reset_index()
    
    # Calculate win rate and profit factor
    symbol_performance["win_rate"] = symbol_performance["win_count"] / symbol_performance["trade_count"] * 100
    symbol_performance["profit_factor"] = abs(symbol_performance["total_profit"] / symbol_performance["total_loss"]) if symbol_performance["total_loss"].any() else float("inf")
    
    return symbol_performance

def get_market_condition_performance(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate performance by market condition

    Args:
        trades_df (pd.DataFrame): DataFrame of trades

    Returns:
        pd.DataFrame: Market condition performance metrics
    """
    if trades_df.empty or "market_condition" not in trades_df.columns:
        return pd.DataFrame()
        
    # Group by market condition
    market_performance = trades_df.groupby("market_condition").agg(
        trade_count=("profit_loss", "count"),
        win_count=("profit_loss", lambda x: (x > 0).sum()),
        loss_count=("profit_loss", lambda x: (x <= 0).sum()),
        total_profit=("profit_loss", lambda x: x[x > 0].sum()),
        total_loss=("profit_loss", lambda x: x[x <= 0].sum()),
        net_profit=("profit_loss", "sum"),
        avg_profit=("profit_loss", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
        avg_loss=("profit_loss", lambda x: x[x <= 0].mean() if (x <= 0).any() else 0),
    ).reset_index()
    
    # Calculate win rate and profit factor
    market_performance["win_rate"] = market_performance["win_count"] / market_performance["trade_count"] * 100
    market_performance["profit_factor"] = abs(market_performance["total_profit"] / market_performance["total_loss"]) if market_performance["total_loss"].any() else float("inf")
    
    return market_performance

def get_drawdown_periods(daily_pnl: pd.DataFrame) -> pd.DataFrame:
    """Calculate drawdown periods

    Args:
        daily_pnl (pd.DataFrame): Daily P&L

    Returns:
        pd.DataFrame: Drawdown periods
    """
    if daily_pnl.empty:
        return pd.DataFrame()
        
    # Calculate drawdown
    daily_pnl["peak"] = daily_pnl["cumulative_pnl"].cummax()
    daily_pnl["drawdown"] = daily_pnl["cumulative_pnl"] - daily_pnl["peak"]
    daily_pnl["drawdown_pct"] = daily_pnl["drawdown"] / daily_pnl["peak"] * 100
    
    # Identify drawdown periods
    daily_pnl["is_drawdown"] = daily_pnl["drawdown"] < 0
    daily_pnl["drawdown_start"] = daily_pnl["is_drawdown"] & ~daily_pnl["is_drawdown"].shift(1).fillna(False)
    daily_pnl["drawdown_end"] = ~daily_pnl["is_drawdown"] & daily_pnl["is_drawdown"].shift(1).fillna(False)
    
    # Get drawdown periods
    drawdown_starts = daily_pnl[daily_pnl["drawdown_start"]]["date"].tolist()
    drawdown_ends = daily_pnl[daily_pnl["drawdown_end"]]["date"].tolist()
    
    # Handle case where last period is still in drawdown
    if len(drawdown_starts) > len(drawdown_ends):
        drawdown_ends.append(daily_pnl["date"].iloc[-1])
        
    # Create drawdown periods DataFrame
    drawdown_periods = pd.DataFrame({
        "start_date": drawdown_starts,
        "end_date": drawdown_ends
    })
    
    if drawdown_periods.empty:
        return pd.DataFrame()
        
    # Calculate drawdown metrics
    drawdown_periods["duration"] = (drawdown_periods["end_date"] - drawdown_periods["start_date"]).dt.days
    
    # Calculate max drawdown for each period
    max_drawdowns = []
    for i, row in drawdown_periods.iterrows():
        period_data = daily_pnl[(daily_pnl["date"] >= row["start_date"]) & (daily_pnl["date"] <= row["end_date"])]
        max_drawdowns.append(period_data["drawdown"].min())
        
    drawdown_periods["max_drawdown"] = max_drawdowns
    drawdown_periods["max_drawdown_pct"] = drawdown_periods["max_drawdown"] / daily_pnl["peak"].max() * 100
    
    return drawdown_periods

# Dashboard layout
st.title("TRAE Trading Dashboard")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Overview", "Strategy Performance", "Symbol Analysis", "Risk Management", "News Impact", "System Status"]
)

# Load data
trades = load_trade_history()
trades_df = get_trades_df(trades)
daily_pnl = get_daily_pnl(trades_df)
strategy_performance = get_strategy_performance(trades_df)
symbol_performance = get_symbol_performance(trades_df)
market_performance = get_market_condition_performance(trades_df)

# Date filter
st.sidebar.title("Date Filter")
if not trades_df.empty and "timestamp" in trades_df.columns:
    min_date = trades_df["timestamp"].min().date()
    max_date = trades_df["timestamp"].max().date()
    
    start_date = st.sidebar.date_input("Start Date", min_date)
    end_date = st.sidebar.date_input("End Date", max_date)
    
    # Filter trades by date
    if "timestamp" in trades_df.columns:
        filtered_trades_df = trades_df[(trades_df["timestamp"].dt.date >= start_date) & 
                                      (trades_df["timestamp"].dt.date <= end_date)]
    else:
        filtered_trades_df = trades_df
else:
    filtered_trades_df = trades_df
    
# Strategy filter
st.sidebar.title("Strategy Filter")
if not trades_df.empty and "strategy" in trades_df.columns:
    strategies = ["All"] + sorted(trades_df["strategy"].unique().tolist())
    selected_strategy = st.sidebar.selectbox("Select Strategy", strategies)
    
    # Filter trades by strategy
    if selected_strategy != "All":
        filtered_trades_df = filtered_trades_df[filtered_trades_df["strategy"] == selected_strategy]
else:
    selected_strategy = "All"

# Symbol filter
st.sidebar.title("Symbol Filter")
if not trades_df.empty and "symbol" in trades_df.columns:
    symbols = ["All"] + sorted(trades_df["symbol"].unique().tolist())
    selected_symbol = st.sidebar.selectbox("Select Symbol", symbols)
    
    # Filter trades by symbol
    if selected_symbol != "All":
        filtered_trades_df = filtered_trades_df[filtered_trades_df["symbol"] == selected_symbol]
else:
    selected_symbol = "All"

# Recalculate metrics with filtered data
filtered_daily_pnl = get_daily_pnl(filtered_trades_df)
filtered_strategy_performance = get_strategy_performance(filtered_trades_df)
filtered_symbol_performance = get_symbol_performance(filtered_trades_df)
filtered_market_performance = get_market_condition_performance(filtered_trades_df)

# Overview page
if page == "Overview":
    st.header("Trading System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Total profit
    total_profit = filtered_trades_df["profit_loss"].sum() if not filtered_trades_df.empty else 0
    col1.metric("Total Profit/Loss", f"${total_profit:.2f}")
    
    # Win rate
    if not filtered_trades_df.empty:
        win_rate = (filtered_trades_df["profit_loss"] > 0).mean() * 100
    else:
        win_rate = 0
    col2.metric("Win Rate", f"{win_rate:.2f}%")
    
    # Trade count
    trade_count = len(filtered_trades_df) if not filtered_trades_df.empty else 0
    col3.metric("Total Trades", trade_count)
    
    # Profit factor
    if not filtered_trades_df.empty:
        total_wins = filtered_trades_df[filtered_trades_df["profit_loss"] > 0]["profit_loss"].sum()
        total_losses = abs(filtered_trades_df[filtered_trades_df["profit_loss"] <= 0]["profit_loss"].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")
    else:
        profit_factor = 0
    col4.metric("Profit Factor", f"{profit_factor:.2f}")
    
    # Daily P&L chart
    st.subheader("Daily Profit/Loss")
    if not filtered_daily_pnl.empty:
        fig = px.bar(
            filtered_daily_pnl,
            x="date",
            y="profit_loss",
            color=filtered_daily_pnl["profit_loss"] > 0,
            color_discrete_map={True: "green", False: "red"},
            labels={"date": "Date", "profit_loss": "Profit/Loss"},
            title="Daily Profit/Loss"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trade data available for the selected filters.")
    
    # Equity curve
    st.subheader("Equity Curve")
    if not filtered_daily_pnl.empty:
        fig = px.line(
            filtered_daily_pnl,
            x="date",
            y="cumulative_pnl",
            labels={"date": "Date", "cumulative_pnl": "Cumulative P&L"},
            title="Equity Curve"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trade data available for the selected filters.")
    
    # Recent trades
    st.subheader("Recent Trades")
    if not filtered_trades_df.empty:
        recent_trades = filtered_trades_df.sort_values("timestamp", ascending=False).head(10)
        
        # Format for display
        display_trades = recent_trades.copy()
        if "timestamp" in display_trades.columns:
            display_trades["timestamp"] = display_trades["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        if "open_time" in display_trades.columns:
            display_trades["open_time"] = display_trades["open_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        if "close_time" in display_trades.columns:
            display_trades["close_time"] = display_trades["close_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Select columns to display
        display_cols = ["timestamp", "strategy", "symbol", "type", "profit_loss", "market_condition"]
        display_cols = [col for col in display_cols if col in display_trades.columns]
        
        st.dataframe(display_trades[display_cols], use_container_width=True)
    else:
        st.info("No trade data available for the selected filters.")
    
    # System status
    st.subheader("System Status")
    
    # Emergency status
    emergency_state = emergency_protocol.load_emergency_state()
    
    col1, col2 = st.columns(2)
    
    # Emergency status
    col1.markdown("### Emergency Status")
    if emergency_state["active"]:
        col1.error(f"⚠️ Emergency Active: {emergency_state['level'].upper()}")
        col1.markdown(f"**Reason:** {emergency_state['reason']}")
        col1.markdown(f"**Trading Status:** {'PAUSED' if emergency_state['trading_paused'] else 'Active with caution'}")
    else:
        col1.success("✅ No Active Emergency")
    
    # News events
    col2.markdown("### Upcoming News Events")
    upcoming_events = news_guard.get_upcoming_news()
    
    if upcoming_events:
        events_df = pd.DataFrame(upcoming_events)
        col2.dataframe(events_df, use_container_width=True)
    else:
        col2.info("No upcoming high-impact news events.")

# Strategy Performance page
elif page == "Strategy Performance":
    st.header("Strategy Performance Analysis")
    
    # Strategy performance table
    st.subheader("Strategy Performance Metrics")
    if not filtered_strategy_performance.empty:
        # Format for display
        display_df = filtered_strategy_performance.copy()
        display_df["win_rate"] = display_df["win_rate"].round(2)
        display_df["profit_factor"] = display_df["profit_factor"].round(2)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Strategy comparison chart
        st.subheader("Strategy Comparison")
        
        # Net profit by strategy
        fig = px.bar(
            filtered_strategy_performance,
            x="strategy",
            y="net_profit",
            color="net_profit",
            color_continuous_scale="RdYlGn",
            labels={"strategy": "Strategy", "net_profit": "Net Profit"},
            title="Net Profit by Strategy"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Win rate by strategy
        fig = px.bar(
            filtered_strategy_performance,
            x="strategy",
            y="win_rate",
            color="win_rate",
            color_continuous_scale="RdYlGn",
            labels={"strategy": "Strategy", "win_rate": "Win Rate (%)"},
            title="Win Rate by Strategy"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Profit factor by strategy
        fig = px.bar(
            filtered_strategy_performance,
            x="strategy",
            y="profit_factor",
            color="profit_factor",
            color_continuous_scale="RdYlGn",
            labels={"strategy": "Strategy", "profit_factor": "Profit Factor"},
            title="Profit Factor by Strategy"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Strategy performance over time
        st.subheader("Strategy Performance Over Time")
        
        if not filtered_trades_df.empty and "strategy" in filtered_trades_df.columns and "timestamp" in filtered_trades_df.columns:
            # Group by strategy and date
            strategy_daily = filtered_trades_df.groupby(["strategy", pd.Grouper(key="timestamp", freq="D")])["profit_loss"].sum().reset_index()
            
            # Calculate cumulative P&L by strategy
            strategy_daily["cumulative_pnl"] = strategy_daily.groupby("strategy")["profit_loss"].cumsum()
            
            # Plot cumulative P&L by strategy
            fig = px.line(
                strategy_daily,
                x="timestamp",
                y="cumulative_pnl",
                color="strategy",
                labels={"timestamp": "Date", "cumulative_pnl": "Cumulative P&L", "strategy": "Strategy"},
                title="Cumulative P&L by Strategy"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No strategy performance data available for the selected filters.")
    
    # Strategy details
    if selected_strategy != "All":
        st.subheader(f"Strategy Details: {selected_strategy}")
        
        # Get strategy configuration
        strategy_config = strategy_manager.get_strategy_config(selected_strategy)
        
        if strategy_config:
            # Display strategy configuration
            st.json(strategy_config)
            
            # Get strategy performance from evaluator
            strategy_stats = evaluator.get_strategy_performance(selected_strategy)
            
            if strategy_stats:
                st.subheader("Strategy Statistics")
                st.json(strategy_stats)

# Symbol Analysis page
elif page == "Symbol Analysis":
    st.header("Symbol Performance Analysis")
    
    # Symbol performance table
    st.subheader("Symbol Performance Metrics")
    if not filtered_symbol_performance.empty:
        # Format for display
        display_df = filtered_symbol_performance.copy()
        display_df["win_rate"] = display_df["win_rate"].round(2)
        display_df["profit_factor"] = display_df["profit_factor"].round(2)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Symbol comparison chart
        st.subheader("Symbol Comparison")
        
        # Net profit by symbol
        fig = px.bar(
            filtered_symbol_performance,
            x="symbol",
            y="net_profit",
            color="net_profit",
            color_continuous_scale="RdYlGn",
            labels={"symbol": "Symbol", "net_profit": "Net Profit"},
            title="Net Profit by Symbol"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Win rate by symbol
        fig = px.bar(
            filtered_symbol_performance,
            x="symbol",
            y="win_rate",
            color="win_rate",
            color_continuous_scale="RdYlGn",
            labels={"symbol": "Symbol", "win_rate": "Win Rate (%)"},
            title="Win Rate by Symbol"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade count by symbol
        fig = px.bar(
            filtered_symbol_performance,
            x="symbol",
            y="trade_count",
            color="trade_count",
            color_continuous_scale="Blues",
            labels={"symbol": "Symbol", "trade_count": "Trade Count"},
            title="Trade Count by Symbol"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Symbol performance by strategy
        st.subheader("Symbol Performance by Strategy")
        
        if not filtered_trades_df.empty and "strategy" in filtered_trades_df.columns and "symbol" in filtered_trades_df.columns:
            # Group by strategy and symbol
            strategy_symbol = filtered_trades_df.groupby(["strategy", "symbol"])["profit_loss"].sum().reset_index()
            
            # Create heatmap
            pivot_table = strategy_symbol.pivot_table(
                values="profit_loss",
                index="strategy",
                columns="symbol",
                aggfunc="sum"
            )
            
            fig = px.imshow(
                pivot_table,
                color_continuous_scale="RdYlGn",
                labels={"color": "Profit/Loss"},
                title="Profit/Loss by Strategy and Symbol"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No symbol performance data available for the selected filters.")
    
    # Symbol details
    if selected_symbol != "All":
        st.subheader(f"Symbol Details: {selected_symbol}")
        
        # Symbol trades over time
        if not filtered_trades_df.empty and "symbol" in filtered_trades_df.columns and "timestamp" in filtered_trades_df.columns:
            # Filter trades for selected symbol
            symbol_trades = filtered_trades_df[filtered_trades_df["symbol"] == selected_symbol]
            
            # Group by date
            symbol_daily = symbol_trades.groupby(pd.Grouper(key="timestamp", freq="D"))["profit_loss"].sum().reset_index()
            symbol_daily["cumulative_pnl"] = symbol_daily["profit_loss"].cumsum()
            
            # Plot cumulative P&L for symbol
            fig = px.line(
                symbol_daily,
                x="timestamp",
                y="cumulative_pnl",
                labels={"timestamp": "Date", "cumulative_pnl": "Cumulative P&L"},
                title=f"Cumulative P&L for {selected_symbol}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade distribution by hour
            if "timestamp" in symbol_trades.columns:
                symbol_trades["hour"] = symbol_trades["timestamp"].dt.hour
                hour_counts = symbol_trades.groupby("hour").size().reset_index(name="count")
                
                fig = px.bar(
                    hour_counts,
                    x="hour",
                    y="count",
                    labels={"hour": "Hour of Day (UTC)", "count": "Trade Count"},
                    title=f"Trade Distribution by Hour for {selected_symbol}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Win rate by hour
                hour_wins = symbol_trades.groupby("hour")["profit_loss"].apply(lambda x: (x > 0).mean() * 100).reset_index(name="win_rate")
                
                fig = px.bar(
                    hour_wins,
                    x="hour",
                    y="win_rate",
                    color="win_rate",
                    color_continuous_scale="RdYlGn",
                    labels={"hour": "Hour of Day (UTC)", "win_rate": "Win Rate (%)"},
                    title=f"Win Rate by Hour for {selected_symbol}"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No trade data available for {selected_symbol} with the selected filters.")

# Risk Management page
elif page == "Risk Management":
    st.header("Risk Management")
    
    # Risk configuration
    risk_config = load_risk_config()
    
    # Daily drawdown
    daily_drawdown = evaluator.get_daily_drawdown()
    
    col1, col2, col3 = st.columns(3)
    
    # Daily drawdown
    col1.metric("Daily Drawdown", f"{daily_drawdown:.2f}%")
    
    # Max drawdown
    if not filtered_daily_pnl.empty:
        filtered_daily_pnl["peak"] = filtered_daily_pnl["cumulative_pnl"].cummax()
        filtered_daily_pnl["drawdown"] = (filtered_daily_pnl["cumulative_pnl"] - filtered_daily_pnl["peak"]) / filtered_daily_pnl["peak"] * 100
        max_drawdown = abs(filtered_daily_pnl["drawdown"].min()) if not filtered_daily_pnl.empty else 0
    else:
        max_drawdown = 0
    col2.metric("Max Drawdown", f"{max_drawdown:.2f}%")
    
    # Current risk level
    if risk_config and "global_risk_level" in risk_config:
        risk_level = risk_config["global_risk_level"]
    else:
        risk_level = "normal"
    col3.metric("Current Risk Level", risk_level.upper())
    
    # Drawdown chart
    st.subheader("Drawdown Analysis")
    if not filtered_daily_pnl.empty:
        # Calculate drawdown
        filtered_daily_pnl["peak"] = filtered_daily_pnl["cumulative_pnl"].cummax()
        filtered_daily_pnl["drawdown"] = (filtered_daily_pnl["cumulative_pnl"] - filtered_daily_pnl["peak"]) / filtered_daily_pnl["peak"] * 100
        
        # Plot drawdown
        fig = px.area(
            filtered_daily_pnl,
            x="date",
            y="drawdown",
            labels={"date": "Date", "drawdown": "Drawdown (%)"},
            title="Drawdown Over Time"
        )
        fig.update_traces(fill='tozeroy', line=dict(color='red'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Drawdown periods
        drawdown_periods = get_drawdown_periods(filtered_daily_pnl)
        
        if not drawdown_periods.empty:
            st.subheader("Drawdown Periods")
            
            # Format for display
            display_df = drawdown_periods.copy()
            display_df["start_date"] = display_df["start_date"].dt.strftime("%Y-%m-%d")
            display_df["end_date"] = display_df["end_date"].dt.strftime("%Y-%m-%d")
            display_df["max_drawdown_pct"] = display_df["max_drawdown_pct"].round(2)
            
            st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No drawdown data available for the selected filters.")
    
    # Risk settings by strategy
    st.subheader("Risk Settings by Strategy")
    
    if risk_config and "strategies" in risk_config:
        # Create DataFrame from risk config
        risk_data = []
        for strategy, config in risk_config["strategies"].items():
            risk_data.append({
                "strategy": strategy,
                **config
            })
            
        if risk_data:
            risk_df = pd.DataFrame(risk_data)
            st.dataframe(risk_df, use_container_width=True)
    else:
        st.info("No risk configuration data available.")
    
    # Consecutive losses analysis
    st.subheader("Consecutive Losses Analysis")
    
    if not filtered_trades_df.empty:
        # Calculate consecutive wins/losses
        filtered_trades_df = filtered_trades_df.sort_values("timestamp")
        filtered_trades_df["is_win"] = filtered_trades_df["profit_loss"] > 0
        filtered_trades_df["streak_change"] = filtered_trades_df["is_win"] != filtered_trades_df["is_win"].shift(1)
        filtered_trades_df["streak_id"] = filtered_trades_df["streak_change"].cumsum()
        
        # Group by streak
        streaks = filtered_trades_df.groupby(["streak_id", "is_win"]).size().reset_index(name="streak_length")
        
        # Get win and loss streaks
        win_streaks = streaks[streaks["is_win"]]["streak_length"]
        loss_streaks = streaks[~streaks["is_win"]]["streak_length"]
        
        col1, col2 = st.columns(2)
        
        # Win streaks
        col1.subheader("Win Streaks")
        if not win_streaks.empty:
            col1.metric("Max Win Streak", win_streaks.max())
            col1.metric("Average Win Streak", f"{win_streaks.mean():.2f}")
            
            # Win streak distribution
            fig = px.histogram(
                win_streaks,
                nbins=10,
                labels={"value": "Streak Length", "count": "Frequency"},
                title="Win Streak Distribution"
            )
            col1.plotly_chart(fig, use_container_width=True)
        else:
            col1.info("No win streaks available.")
        
        # Loss streaks
        col2.subheader("Loss Streaks")
        if not loss_streaks.empty:
            col2.metric("Max Loss Streak", loss_streaks.max())
            col2.metric("Average Loss Streak", f"{loss_streaks.mean():.2f}")
            
            # Loss streak distribution
            fig = px.histogram(
                loss_streaks,
                nbins=10,
                labels={"value": "Streak Length", "count": "Frequency"},
                title="Loss Streak Distribution"
            )
            col2.plotly_chart(fig, use_container_width=True)
        else:
            col2.info("No loss streaks available.")
    else:
        st.info("No trade data available for streak analysis.")

# News Impact page
elif page == "News Impact":
    st.header("News Impact Analysis")
    
    # News events
    st.subheader("Recent News Events")
    recent_events = news_guard.get_recent_events()
    
    if recent_events:
        events_df = pd.DataFrame(recent_events)
        st.dataframe(events_df, use_container_width=True)
    else:
        st.info("No recent news events available.")
    
    # News impact on trades
    st.subheader("News Impact on Trades")
    
    if not filtered_trades_df.empty and "news_avoided" in filtered_trades_df.columns:
        # Compare performance with and without news
        news_avoided = filtered_trades_df[filtered_trades_df["news_avoided"] == True]
        normal_trades = filtered_trades_df[filtered_trades_df["news_avoided"] == False]
        
        col1, col2 = st.columns(2)
        
        # News avoided trades
        col1.subheader("News Avoided Trades")
        if not news_avoided.empty:
            col1.metric("Count", len(news_avoided))
            col1.metric("Win Rate", f"{(news_avoided['profit_loss'] > 0).mean() * 100:.2f}%")
            col1.metric("Average Profit", f"${news_avoided['profit_loss'].mean():.2f}")
        else:
            col1.info("No news avoided trades available.")
        
        # Normal trades
        col2.subheader("Normal Trades")
        if not normal_trades.empty:
            col2.metric("Count", len(normal_trades))
            col2.metric("Win Rate", f"{(normal_trades['profit_loss'] > 0).mean() * 100:.2f}%")
            col2.metric("Average Profit", f"${normal_trades['profit_loss'].mean():.2f}")
        else:
            col2.info("No normal trades available.")
        
        # News impact by symbol
        st.subheader("News Impact by Symbol")
        
        if not filtered_trades_df.empty and "symbol" in filtered_trades_df.columns and "news_avoided" in filtered_trades_df.columns:
            # Group by symbol and news_avoided
            symbol_news = filtered_trades_df.groupby(["symbol", "news_avoided"])["profit_loss"].agg(["mean", "count"]).reset_index()
            
            # Pivot for comparison
            symbol_news_pivot = symbol_news.pivot_table(
                index="symbol",
                columns="news_avoided",
                values=["mean", "count"]
            )
            
            # Flatten column names
            symbol_news_pivot.columns = [f"{col[0]}_{col[1]}" for col in symbol_news_pivot.columns]
            symbol_news_pivot = symbol_news_pivot.reset_index()
            
            # Rename columns
            symbol_news_pivot = symbol_news_pivot.rename(columns={
                "mean_False": "avg_profit_normal",
                "mean_True": "avg_profit_news_avoided",
                "count_False": "count_normal",
                "count_True": "count_news_avoided"
            })
            
            # Fill NaN values
            symbol_news_pivot = symbol_news_pivot.fillna(0)
            
            # Calculate difference
            symbol_news_pivot["profit_difference"] = symbol_news_pivot["avg_profit_news_avoided"] - symbol_news_pivot["avg_profit_normal"]
            
            # Format for display
            display_df = symbol_news_pivot.copy()
            display_df["avg_profit_normal"] = display_df["avg_profit_normal"].round(2)
            display_df["avg_profit_news_avoided"] = display_df["avg_profit_news_avoided"].round(2)
            display_df["profit_difference"] = display_df["profit_difference"].round(2)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Plot profit difference
            fig = px.bar(
                symbol_news_pivot,
                x="symbol",
                y="profit_difference",
                color="profit_difference",
                color_continuous_scale="RdYlGn",
                labels={"symbol": "Symbol", "profit_difference": "Profit Difference (News Avoided - Normal)"},
                title="Impact of News Avoidance by Symbol"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No news impact data available for the selected filters.")

# System Status page
elif page == "System Status":
    st.header("System Status")
    
    # Emergency status
    st.subheader("Emergency Status")
    emergency_state = emergency_protocol.load_emergency_state()
    
    if emergency_state["active"]:
        st.error(f"⚠️ Emergency Active: {emergency_state['level'].upper()}")
        st.markdown(f"**Reason:** {emergency_state['reason']}")
        st.markdown(f"**Start Time:** {emergency_state['start_time']}")
        st.markdown(f"**Trading Status:** {'PAUSED' if emergency_state['trading_paused'] else 'Active with caution'}")
        
        if emergency_state["affected_strategies"]:
            st.markdown(f"**Affected Strategies:** {', '.join(emergency_state['affected_strategies'])}")
        if emergency_state["affected_symbols"]:
            st.markdown(f"**Affected Symbols:** {', '.join(emergency_state['affected_symbols'])}")
    else:
        st.success("✅ No Active Emergency")
    
    # Emergency log
    st.subheader("Emergency Log")
    emergency_log = emergency_protocol.load_emergency_log()
    
    if emergency_log:
        # Convert to DataFrame
        log_df = pd.DataFrame(emergency_log)
        
        # Convert timestamp to datetime
        if "timestamp" in log_df.columns:
            log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
            log_df = log_df.sort_values("timestamp", ascending=False)
        
        # Format for display
        display_cols = ["timestamp", "level", "reason", "emergency_active", "trading_paused"]
        display_cols = [col for col in display_cols if col in log_df.columns]
        
        st.dataframe(log_df[display_cols], use_container_width=True)
    else:
        st.info("No emergency log entries available.")
    
    # Active strategies
    st.subheader("Active Strategies")
    enabled_strategies = strategy_manager.get_enabled_strategies()
    
    if enabled_strategies:
        # Create DataFrame
        strategies_df = pd.DataFrame({"strategy": enabled_strategies})
        
        # Add strategy configurations
        configs = []
        for strategy in enabled_strategies:
            config = strategy_manager.get_strategy_config(strategy)
            configs.append(config if config else {})
            
        # Display strategies
        st.dataframe(strategies_df, use_container_width=True)
        
        # Display strategy configurations
        st.subheader("Strategy Configurations")
        for i, strategy in enumerate(enabled_strategies):
            with st.expander(f"Strategy: {strategy}"):
                st.json(configs[i])
    else:
        st.info("No active strategies available.")
    
    # System metrics
    st.subheader("System Metrics")
    
    # Placeholder for system metrics (CPU, memory, etc.)
    col1, col2, col3 = st.columns(3)
    
    col1.metric("CPU Usage", "25%")
    col2.metric("Memory Usage", "512 MB")
    col3.metric("Disk Usage", "2.1 GB")
    
    # Uptime
    st.metric("System Uptime", "3 days 12 hours")
    
    # Last update
    st.metric("Last Data Update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Add auto-refresh
st.sidebar.title("Dashboard Settings")
refresh_interval = st.sidebar.slider("Auto-refresh interval (seconds)", 0, 300, 0)

if refresh_interval > 0:
    st.sidebar.write(f"Dashboard will refresh every {refresh_interval} seconds.")
    time.sleep(refresh_interval)
    st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("TRAE Trading Dashboard - Powered by Streamlit")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")