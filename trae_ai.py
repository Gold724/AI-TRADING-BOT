#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import argparse
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.ai_agent")


class TraeAIAgent:
    """Market AI Agent for TRAE Trading Sentinel.
    
    This agent analyzes price feeds, candle patterns, and news to generate trading signals.
    It can trigger stealth execution calls when confluences are met.
    """
    
    def __init__(self, config_path: str = "config/trae_ai_config.json"):
        """Initialize the TRAE AI Agent.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize data directories
        self.data_dir = self.config.get("data_dir", "data/ai_agent")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize price data storage
        self.price_data = {}
        self.indicators = {}
        self.signals = []
        self.last_analysis_time = {}
        
        # Load historical data if available
        self._load_historical_data()
        
        logger.info("TRAE AI Agent initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        default_config = {
            "data_dir": "data/ai_agent",
            "analysis_interval": 300,  # 5 minutes
            "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
            "timeframes": ["M5", "M15", "H1", "H4"],
            "indicators": {
                "moving_averages": ["SMA", "EMA"],
                "oscillators": ["RSI", "MACD", "Stochastic"],
                "volatility": ["Bollinger Bands", "ATR"],
                "trend": ["ADX", "Ichimoku"]
            },
            "strategies": {
                "trend_following": {
                    "enabled": True,
                    "weight": 0.4
                },
                "mean_reversion": {
                    "enabled": True,
                    "weight": 0.3
                },
                "breakout": {
                    "enabled": True,
                    "weight": 0.2
                },
                "pattern_recognition": {
                    "enabled": True,
                    "weight": 0.1
                }
            },
            "risk_management": {
                "max_risk_per_trade": 0.01,  # 1% of account
                "max_daily_risk": 0.05,      # 5% of account
                "default_stop_loss": 30,     # pips
                "default_take_profit": 60    # pips
            },
            "execution": {
                "endpoint": "http://localhost:5000/api/trade/stealth",
                "api_key": "${TRAE_API_KEY}",
                "auto_execute": False,
                "confirmation_required": True
            },
            "learning": {
                "enabled": True,
                "learn_from_trades": True,
                "adaptation_rate": 0.1,
                "min_samples": 30
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    loaded_config = json.load(f)
                
                # Merge with default config
                for key, value in loaded_config.items():
                    default_config[key] = value
                
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                
                # Save default config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=2)
                
                logger.info(f"Default configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
        
        return default_config
    
    def _load_historical_data(self) -> None:
        """Load historical price data if available."""
        try:
            for symbol in self.config["symbols"]:
                for timeframe in self.config["timeframes"]:
                    file_path = os.path.join(self.data_dir, f"{symbol}_{timeframe}.csv")
                    
                    if os.path.exists(file_path):
                        # Load data from CSV
                        df = pd.read_csv(file_path, parse_dates=["timestamp"])
                        
                        # Store in price_data dictionary
                        key = f"{symbol}_{timeframe}"
                        self.price_data[key] = df
                        
                        logger.info(f"Loaded historical data for {symbol} {timeframe} from {file_path}")
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def _save_historical_data(self, symbol: str, timeframe: str) -> None:
        """Save historical price data to disk.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., M5, H1)
        """
        try:
            key = f"{symbol}_{timeframe}"
            if key in self.price_data:
                file_path = os.path.join(self.data_dir, f"{key}.csv")
                self.price_data[key].to_csv(file_path, index=False)
                logger.info(f"Saved historical data for {symbol} {timeframe} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving historical data for {symbol} {timeframe}: {e}")
    
    def fetch_price_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Fetch price data for a symbol and timeframe.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., M5, H1)
            limit (int): Number of candles to fetch
            
        Returns:
            pd.DataFrame: Price data
        """
        try:
            # Check if we need to fetch new data
            key = f"{symbol}_{timeframe}"
            current_time = datetime.now()
            
            # Determine if we need to fetch new data based on last analysis time
            if key in self.last_analysis_time:
                time_diff = (current_time - self.last_analysis_time[key]).total_seconds()
                if time_diff < self.config["analysis_interval"]:
                    logger.debug(f"Using cached data for {symbol} {timeframe}, last updated {time_diff:.1f}s ago")
                    return self.price_data.get(key, pd.DataFrame())
            
            # In a real implementation, this would fetch data from a broker API or data provider
            # For this example, we'll generate synthetic data if we don't have historical data
            
            if key not in self.price_data or self.price_data[key].empty:
                # Generate synthetic data for demonstration
                logger.info(f"Generating synthetic data for {symbol} {timeframe}")
                
                # Create date range
                end_time = current_time
                
                # Determine time delta based on timeframe
                if timeframe == "M1":
                    delta = timedelta(minutes=1)
                elif timeframe == "M5":
                    delta = timedelta(minutes=5)
                elif timeframe == "M15":
                    delta = timedelta(minutes=15)
                elif timeframe == "M30":
                    delta = timedelta(minutes=30)
                elif timeframe == "H1":
                    delta = timedelta(hours=1)
                elif timeframe == "H4":
                    delta = timedelta(hours=4)
                elif timeframe == "D1":
                    delta = timedelta(days=1)
                else:
                    delta = timedelta(minutes=5)  # Default to M5
                
                # Create timestamps
                timestamps = [end_time - delta * i for i in range(limit, 0, -1)]
                
                # Generate price data
                if symbol == "EURUSD":
                    base_price = 1.1000
                    volatility = 0.0002
                elif symbol == "GBPUSD":
                    base_price = 1.3000
                    volatility = 0.0003
                elif symbol == "USDJPY":
                    base_price = 110.00
                    volatility = 0.03
                elif symbol == "XAUUSD":
                    base_price = 1800.00
                    volatility = 0.5
                else:
                    base_price = 1.0000
                    volatility = 0.0002
                
                # Generate random walk
                prices = [base_price]
                for i in range(1, limit):
                    change = np.random.normal(0, volatility)
                    new_price = prices[-1] + change
                    prices.append(new_price)
                
                # Create OHLC data
                data = []
                for i in range(limit):
                    close = prices[i]
                    high = close + abs(np.random.normal(0, volatility))
                    low = close - abs(np.random.normal(0, volatility))
                    open_price = close - np.random.normal(0, volatility)
                    volume = np.random.randint(100, 1000)
                    
                    data.append({
                        "timestamp": timestamps[i],
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume
                    })
                
                # Create DataFrame
                df = pd.DataFrame(data)
                
                # Store in price_data dictionary
                self.price_data[key] = df
            else:
                # In a real implementation, fetch new data and append to existing data
                logger.info(f"Fetching new data for {symbol} {timeframe}")
                
                # For this example, we'll just add a new candle with some random movement
                df = self.price_data[key].copy()
                
                # Get the last candle
                last_candle = df.iloc[-1]
                
                # Determine time delta based on timeframe
                if timeframe == "M1":
                    delta = timedelta(minutes=1)
                elif timeframe == "M5":
                    delta = timedelta(minutes=5)
                elif timeframe == "M15":
                    delta = timedelta(minutes=15)
                elif timeframe == "M30":
                    delta = timedelta(minutes=30)
                elif timeframe == "H1":
                    delta = timedelta(hours=1)
                elif timeframe == "H4":
                    delta = timedelta(hours=4)
                elif timeframe == "D1":
                    delta = timedelta(days=1)
                else:
                    delta = timedelta(minutes=5)  # Default to M5
                
                # Create new timestamp
                new_timestamp = last_candle["timestamp"] + delta
                
                # If the new timestamp is in the future, use current time
                if new_timestamp > current_time:
                    new_timestamp = current_time
                
                # Generate new candle with some random movement
                if symbol == "USDJPY" or symbol == "XAUUSD":
                    volatility = 0.01 * last_candle["close"]
                else:
                    volatility = 0.0002 * last_candle["close"]
                
                close = last_candle["close"] + np.random.normal(0, volatility)
                high = close + abs(np.random.normal(0, volatility/2))
                low = close - abs(np.random.normal(0, volatility/2))
                open_price = last_candle["close"]
                volume = np.random.randint(100, 1000)
                
                # Create new candle
                new_candle = {
                    "timestamp": new_timestamp,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                }
                
                # Append to DataFrame
                df = df.append(new_candle, ignore_index=True)
                
                # Keep only the last 'limit' candles
                if len(df) > limit:
                    df = df.iloc[-limit:]
                
                # Update price_data dictionary
                self.price_data[key] = df
            
            # Update last analysis time
            self.last_analysis_time[key] = current_time
            
            # Save historical data
            self._save_historical_data(symbol, timeframe)
            
            return self.price_data[key]
        except Exception as e:
            logger.error(f"Error fetching price data for {symbol} {timeframe}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Calculate technical indicators for a symbol and timeframe.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., M5, H1)
            
        Returns:
            Dict[str, Any]: Dictionary of indicators
        """
        try:
            key = f"{symbol}_{timeframe}"
            
            # Fetch price data if not available
            if key not in self.price_data or self.price_data[key].empty:
                self.fetch_price_data(symbol, timeframe)
            
            df = self.price_data[key]
            
            # Initialize indicators dictionary
            indicators = {}
            
            # Calculate moving averages
            if "moving_averages" in self.config["indicators"]:
                indicators["moving_averages"] = {}
                
                # Simple Moving Average (SMA)
                if "SMA" in self.config["indicators"]["moving_averages"]:
                    indicators["moving_averages"]["SMA"] = {}
                    for period in [20, 50, 200]:
                        indicators["moving_averages"]["SMA"][f"SMA{period}"] = df["close"].rolling(window=period).mean().iloc[-1]
                
                # Exponential Moving Average (EMA)
                if "EMA" in self.config["indicators"]["moving_averages"]:
                    indicators["moving_averages"]["EMA"] = {}
                    for period in [12, 26, 200]:
                        indicators["moving_averages"]["EMA"][f"EMA{period}"] = df["close"].ewm(span=period).mean().iloc[-1]
            
            # Calculate oscillators
            if "oscillators" in self.config["indicators"]:
                indicators["oscillators"] = {}
                
                # Relative Strength Index (RSI)
                if "RSI" in self.config["indicators"]["oscillators"]:
                    delta = df["close"].diff()
                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)
                    avg_gain = gain.rolling(window=14).mean()
                    avg_loss = loss.rolling(window=14).mean()
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    indicators["oscillators"]["RSI"] = rsi.iloc[-1]
                
                # Moving Average Convergence Divergence (MACD)
                if "MACD" in self.config["indicators"]["oscillators"]:
                    ema12 = df["close"].ewm(span=12).mean()
                    ema26 = df["close"].ewm(span=26).mean()
                    macd_line = ema12 - ema26
                    signal_line = macd_line.ewm(span=9).mean()
                    histogram = macd_line - signal_line
                    
                    indicators["oscillators"]["MACD"] = {
                        "macd_line": macd_line.iloc[-1],
                        "signal_line": signal_line.iloc[-1],
                        "histogram": histogram.iloc[-1]
                    }
                
                # Stochastic Oscillator
                if "Stochastic" in self.config["indicators"]["oscillators"]:
                    k_period = 14
                    d_period = 3
                    
                    low_min = df["low"].rolling(window=k_period).min()
                    high_max = df["high"].rolling(window=k_period).max()
                    
                    k = 100 * ((df["close"] - low_min) / (high_max - low_min))
                    d = k.rolling(window=d_period).mean()
                    
                    indicators["oscillators"]["Stochastic"] = {
                        "k": k.iloc[-1],
                        "d": d.iloc[-1]
                    }
            
            # Calculate volatility indicators
            if "volatility" in self.config["indicators"]:
                indicators["volatility"] = {}
                
                # Bollinger Bands
                if "Bollinger Bands" in self.config["indicators"]["volatility"]:
                    period = 20
                    std_dev = 2
                    
                    sma = df["close"].rolling(window=period).mean()
                    std = df["close"].rolling(window=period).std()
                    
                    upper_band = sma + (std * std_dev)
                    lower_band = sma - (std * std_dev)
                    
                    indicators["volatility"]["Bollinger Bands"] = {
                        "middle": sma.iloc[-1],
                        "upper": upper_band.iloc[-1],
                        "lower": lower_band.iloc[-1]
                    }
                
                # Average True Range (ATR)
                if "ATR" in self.config["indicators"]["volatility"]:
                    period = 14
                    
                    high_low = df["high"] - df["low"]
                    high_close = (df["high"] - df["close"].shift()).abs()
                    low_close = (df["low"] - df["close"].shift()).abs()
                    
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = ranges.max(axis=1)
                    
                    atr = true_range.rolling(window=period).mean()
                    indicators["volatility"]["ATR"] = atr.iloc[-1]
            
            # Calculate trend indicators
            if "trend" in self.config["indicators"]:
                indicators["trend"] = {}
                
                # Average Directional Index (ADX)
                if "ADX" in self.config["indicators"]["trend"]:
                    period = 14
                    
                    # Calculate +DM and -DM
                    plus_dm = df["high"].diff()
                    minus_dm = df["low"].diff()
                    plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm.abs()), 0)
                    minus_dm = minus_dm.abs().where((minus_dm < 0) & (minus_dm.abs() > plus_dm), 0)
                    
                    # Calculate ATR
                    high_low = df["high"] - df["low"]
                    high_close = (df["high"] - df["close"].shift()).abs()
                    low_close = (df["low"] - df["close"].shift()).abs()
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = ranges.max(axis=1)
                    atr = true_range.rolling(window=period).mean()
                    
                    # Calculate +DI and -DI
                    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
                    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
                    
                    # Calculate DX and ADX
                    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
                    adx = dx.rolling(window=period).mean()
                    
                    indicators["trend"]["ADX"] = {
                        "adx": adx.iloc[-1],
                        "plus_di": plus_di.iloc[-1],
                        "minus_di": minus_di.iloc[-1]
                    }
                
                # Ichimoku Cloud
                if "Ichimoku" in self.config["indicators"]["trend"]:
                    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
                    period9_high = df["high"].rolling(window=9).max()
                    period9_low = df["low"].rolling(window=9).min()
                    tenkan_sen = (period9_high + period9_low) / 2
                    
                    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
                    period26_high = df["high"].rolling(window=26).max()
                    period26_low = df["low"].rolling(window=26).min()
                    kijun_sen = (period26_high + period26_low) / 2
                    
                    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
                    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
                    
                    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
                    period52_high = df["high"].rolling(window=52).max()
                    period52_low = df["low"].rolling(window=52).min()
                    senkou_span_b = ((period52_high + period52_low) / 2).shift(26)
                    
                    # Chikou Span (Lagging Span): Close price shifted backwards 26 periods
                    chikou_span = df["close"].shift(-26)
                    
                    indicators["trend"]["Ichimoku"] = {
                        "tenkan_sen": tenkan_sen.iloc[-1],
                        "kijun_sen": kijun_sen.iloc[-1],
                        "senkou_span_a": senkou_span_a.iloc[-1] if not pd.isna(senkou_span_a.iloc[-1]) else None,
                        "senkou_span_b": senkou_span_b.iloc[-1] if not pd.isna(senkou_span_b.iloc[-1]) else None,
                        "chikou_span": chikou_span.iloc[-1] if not pd.isna(chikou_span.iloc[-1]) else None
                    }
            
            # Store indicators
            self.indicators[key] = indicators
            
            return indicators
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol} {timeframe}: {e}")
            return {}
    
    def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """Analyze market conditions for a symbol across all timeframes.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            analysis = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "timeframes": {},
                "overall": {}
            }
            
            # Analyze each timeframe
            for timeframe in self.config["timeframes"]:
                # Calculate indicators
                indicators = self.calculate_indicators(symbol, timeframe)
                
                # Analyze indicators
                timeframe_analysis = self._analyze_indicators(symbol, timeframe, indicators)
                
                # Store analysis
                analysis["timeframes"][timeframe] = timeframe_analysis
            
            # Calculate overall analysis across timeframes
            analysis["overall"] = self._calculate_overall_analysis(symbol, analysis["timeframes"])
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing market for {symbol}: {e}")
            return {}
    
    def _analyze_indicators(self, symbol: str, timeframe: str, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze indicators for a symbol and timeframe.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., M5, H1)
            indicators (Dict[str, Any]): Dictionary of indicators
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            analysis = {
                "trend": {
                    "direction": "neutral",
                    "strength": 0,
                    "signals": []
                },
                "momentum": {
                    "direction": "neutral",
                    "strength": 0,
                    "signals": []
                },
                "volatility": {
                    "level": "medium",
                    "signals": []
                },
                "support_resistance": {
                    "support": [],
                    "resistance": []
                },
                "patterns": {
                    "detected": [],
                    "strength": 0
                },
                "signals": {
                    "buy": [],
                    "sell": [],
                    "neutral": []
                },
                "recommendation": {
                    "action": "neutral",
                    "confidence": 0,
                    "reasons": []
                }
            }
            
            # Get price data
            key = f"{symbol}_{timeframe}"
            df = self.price_data.get(key, pd.DataFrame())
            
            if df.empty:
                return analysis
            
            current_price = df["close"].iloc[-1]
            
            # Analyze trend
            if "moving_averages" in indicators:
                ma_signals = []
                
                if "SMA" in indicators["moving_averages"]:
                    sma_data = indicators["moving_averages"]["SMA"]
                    
                    # Check SMA20 vs SMA50 (short-term trend)
                    if "SMA20" in sma_data and "SMA50" in sma_data:
                        if sma_data["SMA20"] > sma_data["SMA50"]:
                            ma_signals.append(("bullish", "SMA20 above SMA50", 0.6))
                        elif sma_data["SMA20"] < sma_data["SMA50"]:
                            ma_signals.append(("bearish", "SMA20 below SMA50", 0.6))
                    
                    # Check price vs SMA200 (long-term trend)
                    if "SMA200" in sma_data:
                        if current_price > sma_data["SMA200"]:
                            ma_signals.append(("bullish", "Price above SMA200", 0.7))
                        elif current_price < sma_data["SMA200"]:
                            ma_signals.append(("bearish", "Price below SMA200", 0.7))
                
                if "EMA" in indicators["moving_averages"]:
                    ema_data = indicators["moving_averages"]["EMA"]
                    
                    # Check EMA12 vs EMA26 (short-term trend)
                    if "EMA12" in ema_data and "EMA26" in ema_data:
                        if ema_data["EMA12"] > ema_data["EMA26"]:
                            ma_signals.append(("bullish", "EMA12 above EMA26", 0.65))
                        elif ema_data["EMA12"] < ema_data["EMA26"]:
                            ma_signals.append(("bearish", "EMA12 below EMA26", 0.65))
                
                # Determine overall trend direction and strength
                bullish_count = sum(1 for s in ma_signals if s[0] == "bullish")
                bearish_count = sum(1 for s in ma_signals if s[0] == "bearish")
                
                if bullish_count > bearish_count:
                    analysis["trend"]["direction"] = "bullish"
                    analysis["trend"]["strength"] = min(1.0, bullish_count / len(ma_signals) if ma_signals else 0)
                elif bearish_count > bullish_count:
                    analysis["trend"]["direction"] = "bearish"
                    analysis["trend"]["strength"] = min(1.0, bearish_count / len(ma_signals) if ma_signals else 0)
                
                # Store signals
                analysis["trend"]["signals"] = ma_signals
            
            # Analyze momentum
            if "oscillators" in indicators:
                momentum_signals = []
                
                if "RSI" in indicators["oscillators"]:
                    rsi = indicators["oscillators"]["RSI"]
                    
                    if rsi > 70:
                        momentum_signals.append(("bearish", f"RSI overbought ({rsi:.1f})", 0.7))
                    elif rsi < 30:
                        momentum_signals.append(("bullish", f"RSI oversold ({rsi:.1f})", 0.7))
                    elif rsi > 50:
                        momentum_signals.append(("bullish", f"RSI above 50 ({rsi:.1f})", 0.5))
                    elif rsi < 50:
                        momentum_signals.append(("bearish", f"RSI below 50 ({rsi:.1f})", 0.5))
                
                if "MACD" in indicators["oscillators"]:
                    macd = indicators["oscillators"]["MACD"]
                    
                    if macd["macd_line"] > macd["signal_line"]:
                        momentum_signals.append(("bullish", "MACD line above signal line", 0.6))
                    elif macd["macd_line"] < macd["signal_line"]:
                        momentum_signals.append(("bearish", "MACD line below signal line", 0.6))
                    
                    if macd["histogram"] > 0 and macd["histogram"] > macd["histogram"]:
                        momentum_signals.append(("bullish", "MACD histogram increasing", 0.55))
                    elif macd["histogram"] < 0 and macd["histogram"] < macd["histogram"]:
                        momentum_signals.append(("bearish", "MACD histogram decreasing", 0.55))
                
                if "Stochastic" in indicators["oscillators"]:
                    stoch = indicators["oscillators"]["Stochastic"]
                    
                    if stoch["k"] > 80 and stoch["d"] > 80:
                        momentum_signals.append(("bearish", "Stochastic overbought", 0.65))
                    elif stoch["k"] < 20 and stoch["d"] < 20:
                        momentum_signals.append(("bullish", "Stochastic oversold", 0.65))
                    
                    if stoch["k"] > stoch["d"]:
                        momentum_signals.append(("bullish", "Stochastic K above D", 0.55))
                    elif stoch["k"] < stoch["d"]:
                        momentum_signals.append(("bearish", "Stochastic K below D", 0.55))
                
                # Determine overall momentum direction and strength
                bullish_count = sum(1 for s in momentum_signals if s[0] == "bullish")
                bearish_count = sum(1 for s in momentum_signals if s[0] == "bearish")
                
                if bullish_count > bearish_count:
                    analysis["momentum"]["direction"] = "bullish"
                    analysis["momentum"]["strength"] = min(1.0, bullish_count / len(momentum_signals) if momentum_signals else 0)
                elif bearish_count > bullish_count:
                    analysis["momentum"]["direction"] = "bearish"
                    analysis["momentum"]["strength"] = min(1.0, bearish_count / len(momentum_signals) if momentum_signals else 0)
                
                # Store signals
                analysis["momentum"]["signals"] = momentum_signals
            
            # Analyze volatility
            if "volatility" in indicators:
                volatility_signals = []
                
                if "Bollinger Bands" in indicators["volatility"]:
                    bb = indicators["volatility"]["Bollinger Bands"]
                    
                    # Calculate bandwidth
                    bandwidth = (bb["upper"] - bb["lower"]) / bb["middle"]
                    
                    if bandwidth > 0.05:  # High volatility
                        analysis["volatility"]["level"] = "high"
                        volatility_signals.append(("high", f"Bollinger Bandwidth: {bandwidth:.4f}", 0.7))
                    elif bandwidth < 0.02:  # Low volatility
                        analysis["volatility"]["level"] = "low"
                        volatility_signals.append(("low", f"Bollinger Bandwidth: {bandwidth:.4f}", 0.7))
                    else:  # Medium volatility
                        analysis["volatility"]["level"] = "medium"
                        volatility_signals.append(("medium", f"Bollinger Bandwidth: {bandwidth:.4f}", 0.7))
                    
                    # Check for price near bands
                    if current_price > bb["upper"]:
                        volatility_signals.append(("bearish", "Price above upper Bollinger Band", 0.6))
                    elif current_price < bb["lower"]:
                        volatility_signals.append(("bullish", "Price below lower Bollinger Band", 0.6))
                
                if "ATR" in indicators["volatility"]:
                    atr = indicators["volatility"]["ATR"]
                    atr_percent = atr / current_price * 100
                    
                    if atr_percent > 1.0:  # High volatility (>1% ATR)
                        volatility_signals.append(("high", f"ATR: {atr_percent:.2f}%", 0.65))
                    elif atr_percent < 0.5:  # Low volatility (<0.5% ATR)
                        volatility_signals.append(("low", f"ATR: {atr_percent:.2f}%", 0.65))
                    else:  # Medium volatility
                        volatility_signals.append(("medium", f"ATR: {atr_percent:.2f}%", 0.65))
                
                # Store signals
                analysis["volatility"]["signals"] = volatility_signals
            
            # Analyze support and resistance levels
            # This is a simplified approach - in a real implementation, you would use more sophisticated methods
            recent_df = df.tail(50)  # Look at recent price action
            
            # Find local minima and maxima
            local_min = []
            local_max = []
            
            for i in range(1, len(recent_df) - 1):
                if recent_df["low"].iloc[i] < recent_df["low"].iloc[i-1] and recent_df["low"].iloc[i] < recent_df["low"].iloc[i+1]:
                    local_min.append(recent_df["low"].iloc[i])
                
                if recent_df["high"].iloc[i] > recent_df["high"].iloc[i-1] and recent_df["high"].iloc[i] > recent_df["high"].iloc[i+1]:
                    local_max.append(recent_df["high"].iloc[i])
            
            # Group close levels
            def group_levels(levels, threshold_percent=0.001):
                if not levels:
                    return []
                
                grouped = []
                current_group = [levels[0]]
                
                for level in levels[1:]:
                    # Check if level is within threshold of current group average
                    group_avg = sum(current_group) / len(current_group)
                    threshold = group_avg * threshold_percent
                    
                    if abs(level - group_avg) <= threshold:
                        current_group.append(level)
                    else:
                        # Add current group average to grouped levels
                        grouped.append(sum(current_group) / len(current_group))
                        # Start new group
                        current_group = [level]
                
                # Add last group
                if current_group:
                    grouped.append(sum(current_group) / len(current_group))
                
                return grouped
            
            # Group and sort support/resistance levels
            support_levels = sorted(group_levels(local_min))
            resistance_levels = sorted(group_levels(local_max))
            
            # Filter levels that are close to current price
            support_levels = [level for level in support_levels if level < current_price]
            resistance_levels = [level for level in resistance_levels if level > current_price]
            
            # Take closest few levels
            support_levels = support_levels[-3:] if support_levels else []
            resistance_levels = resistance_levels[:3] if resistance_levels else []
            
            analysis["support_resistance"]["support"] = support_levels
            analysis["support_resistance"]["resistance"] = resistance_levels
            
            # Detect patterns (simplified)
            patterns = []
            
            # Check for potential patterns in recent candles
            last_candles = df.tail(5)
            
            # Bullish engulfing
            if len(last_candles) >= 2:
                prev_candle = last_candles.iloc[-2]
                curr_candle = last_candles.iloc[-1]
                
                if prev_candle["close"] < prev_candle["open"] and curr_candle["close"] > curr_candle["open"] and \
                   curr_candle["open"] <= prev_candle["close"] and curr_candle["close"] > prev_candle["open"]:
                    patterns.append(("bullish", "Bullish Engulfing", 0.7))
            
            # Bearish engulfing
            if len(last_candles) >= 2:
                prev_candle = last_candles.iloc[-2]
                curr_candle = last_candles.iloc[-1]
                
                if prev_candle["close"] > prev_candle["open"] and curr_candle["close"] < curr_candle["open"] and \
                   curr_candle["open"] >= prev_candle["close"] and curr_candle["close"] < prev_candle["open"]:
                    patterns.append(("bearish", "Bearish Engulfing", 0.7))
            
            # Doji
            if len(last_candles) >= 1:
                curr_candle = last_candles.iloc[-1]
                body_size = abs(curr_candle["close"] - curr_candle["open"])
                range_size = curr_candle["high"] - curr_candle["low"]
                
                if range_size > 0 and body_size / range_size < 0.1:
                    if curr_candle["close"] > curr_candle["open"]:
                        patterns.append(("neutral", "Doji (slight bullish)", 0.5))
                    else:
                        patterns.append(("neutral", "Doji (slight bearish)", 0.5))
            
            # Store patterns
            analysis["patterns"]["detected"] = [p[1] for p in patterns]
            analysis["patterns"]["strength"] = sum(p[2] for p in patterns) / len(patterns) if patterns else 0
            
            # Compile signals
            for direction, reason, strength in analysis["trend"]["signals"] + analysis["momentum"]["signals"] + \
                                            [(s[0], s[1], s[2]) for s in volatility_signals if s[0] in ["bullish", "bearish"]] + \
                                            [p for p in patterns if p[0] in ["bullish", "bearish", "neutral"]]:
                if direction == "bullish":
                    analysis["signals"]["buy"].append((reason, strength))
                elif direction == "bearish":
                    analysis["signals"]["sell"].append((reason, strength))
                else:
                    analysis["signals"]["neutral"].append((reason, strength))
            
            # Make recommendation
            buy_signals = analysis["signals"]["buy"]
            sell_signals = analysis["signals"]["sell"]
            neutral_signals = analysis["signals"]["neutral"]
            
            buy_strength = sum(s[1] for s in buy_signals) / len(buy_signals) if buy_signals else 0
            sell_strength = sum(s[1] for s in sell_signals) / len(sell_signals) if sell_signals else 0
            neutral_strength = sum(s[1] for s in neutral_signals) / len(neutral_signals) if neutral_signals else 0
            
            # Apply strategy weights
            strategy_weights = self.config["strategies"]
            
            # Trend following gives more weight to trend signals
            if strategy_weights.get("trend_following", {}).get("enabled", False):
                trend_weight = strategy_weights["trend_following"]["weight"]
                if analysis["trend"]["direction"] == "bullish":
                    buy_strength += analysis["trend"]["strength"] * trend_weight
                elif analysis["trend"]["direction"] == "bearish":
                    sell_strength += analysis["trend"]["strength"] * trend_weight
            
            # Mean reversion gives more weight to overbought/oversold signals
            if strategy_weights.get("mean_reversion", {}).get("enabled", False):
                reversion_weight = strategy_weights["mean_reversion"]["weight"]
                
                # Look for oversold conditions to buy
                oversold_signals = [s for s in buy_signals if "oversold" in s[0].lower() or "below lower" in s[0].lower()]
                if oversold_signals:
                    avg_strength = sum(s[1] for s in oversold_signals) / len(oversold_signals)
                    buy_strength += avg_strength * reversion_weight
                
                # Look for overbought conditions to sell
                overbought_signals = [s for s in sell_signals if "overbought" in s[0].lower() or "above upper" in s[0].lower()]
                if overbought_signals:
                    avg_strength = sum(s[1] for s in overbought_signals) / len(overbought_signals)
                    sell_strength += avg_strength * reversion_weight
            
            # Determine final recommendation
            if buy_strength > sell_strength and buy_strength > neutral_strength and buy_strength > 0.6:
                action = "buy"
                confidence = buy_strength
                reasons = [s[0] for s in buy_signals[:3]]  # Top 3 reasons
            elif sell_strength > buy_strength and sell_strength > neutral_strength and sell_strength > 0.6:
                action = "sell"
                confidence = sell_strength
                reasons = [s[0] for s in sell_signals[:3]]  # Top 3 reasons
            else:
                action = "neutral"
                confidence = max(neutral_strength, 0.5)  # At least 0.5 confidence for neutral
                reasons = ["Conflicting signals", "Waiting for clearer direction"]
            
            analysis["recommendation"] = {
                "action": action,
                "confidence": confidence,
                "reasons": reasons
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing indicators for {symbol} {timeframe}: {e}")
            return {}
    
    def _calculate_overall_analysis(self, symbol: str, timeframe_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall analysis across timeframes.
        
        Args:
            symbol (str): Trading symbol
            timeframe_analyses (Dict[str, Any]): Analysis results for each timeframe
            
        Returns:
            Dict[str, Any]: Overall analysis
        """
        try:
            # Initialize overall analysis
            overall = {
                "trend": {
                    "direction": "neutral",
                    "strength": 0
                },
                "momentum": {
                    "direction": "neutral",
                    "strength": 0
                },
                "volatility": {
                    "level": "medium"
                },
                "recommendation": {
                    "action": "neutral",
                    "confidence": 0,
                    "reasons": [],
                    "timeframes": {}
                }
            }
            
            # Assign weights to timeframes (higher weight for longer timeframes)
            timeframe_weights = {
                "M5": 0.1,
                "M15": 0.15,
                "M30": 0.2,
                "H1": 0.25,
                "H4": 0.3,
                "D1": 0.4
            }
            
            # Normalize weights based on available timeframes
            available_weights = {tf: timeframe_weights.get(tf, 0.1) for tf in timeframe_analyses.keys()}
            total_weight = sum(available_weights.values())
            normalized_weights = {tf: w / total_weight for tf, w in available_weights.items()}
            
            # Calculate weighted trend and momentum
            trend_directions = {"bullish": 0, "bearish": 0, "neutral": 0}
            momentum_directions = {"bullish": 0, "bearish": 0, "neutral": 0}
            volatility_levels = {"high": 0, "medium": 0, "low": 0}
            
            for tf, analysis in timeframe_analyses.items():
                weight = normalized_weights[tf]
                
                # Trend
                trend_dir = analysis["trend"]["direction"]
                trend_strength = analysis["trend"]["strength"]
                trend_directions[trend_dir] += weight * trend_strength
                
                # Momentum
                momentum_dir = analysis["momentum"]["direction"]
                momentum_strength = analysis["momentum"]["strength"]
                momentum_directions[momentum_dir] += weight * momentum_strength
                
                # Volatility
                volatility_level = analysis["volatility"]["level"]
                volatility_levels[volatility_level] += weight
            
            # Determine overall trend direction
            if trend_directions["bullish"] > trend_directions["bearish"] and trend_directions["bullish"] > trend_directions["neutral"]:
                overall["trend"]["direction"] = "bullish"
                overall["trend"]["strength"] = trend_directions["bullish"]
            elif trend_directions["bearish"] > trend_directions["bullish"] and trend_directions["bearish"] > trend_directions["neutral"]:
                overall["trend"]["direction"] = "bearish"
                overall["trend"]["strength"] = trend_directions["bearish"]
            else:
                overall["trend"]["direction"] = "neutral"
                overall["trend"]["strength"] = trend_directions["neutral"]
            
            # Determine overall momentum direction
            if momentum_directions["bullish"] > momentum_directions["bearish"] and momentum_directions["bullish"] > momentum_directions["neutral"]:
                overall["momentum"]["direction"] = "bullish"
                overall["momentum"]["strength"] = momentum_directions["bullish"]
            elif momentum_directions["bearish"] > momentum_directions["bullish"] and momentum_directions["bearish"] > momentum_directions["neutral"]:
                overall["momentum"]["direction"] = "bearish"
                overall["momentum"]["strength"] = momentum_directions["bearish"]
            else:
                overall["momentum"]["direction"] = "neutral"
                overall["momentum"]["strength"] = momentum_directions["neutral"]
            
            # Determine overall volatility level
            max_volatility = max(volatility_levels.items(), key=lambda x: x[1])
            overall["volatility"]["level"] = max_volatility[0]
            
            # Collect recommendations from each timeframe
            recommendations = {}
            for tf, analysis in timeframe_analyses.items():
                action = analysis["recommendation"]["action"]
                confidence = analysis["recommendation"]["confidence"]
                reasons = analysis["recommendation"]["reasons"]
                
                recommendations[tf] = {
                    "action": action,
                    "confidence": confidence,
                    "reasons": reasons
                }
            
            # Calculate overall recommendation
            buy_confidence = 0
            sell_confidence = 0
            neutral_confidence = 0
            
            for tf, rec in recommendations.items():
                weight = normalized_weights[tf]
                
                if rec["action"] == "buy":
                    buy_confidence += rec["confidence"] * weight
                elif rec["action"] == "sell":
                    sell_confidence += rec["confidence"] * weight
                else:  # neutral
                    neutral_confidence += rec["confidence"] * weight
            
            # Determine final recommendation
            if buy_confidence > sell_confidence and buy_confidence > neutral_confidence and buy_confidence > 0.6:
                action = "buy"
                confidence = buy_confidence
                
                # Collect reasons from bullish timeframes
                reasons = []
                for tf, rec in recommendations.items():
                    if rec["action"] == "buy":
                        for reason in rec["reasons"]:
                            if reason not in reasons:
                                reasons.append(f"{reason} ({tf})")
                                if len(reasons) >= 3:
                                    break
            elif sell_confidence > buy_confidence and sell_confidence > neutral_confidence and sell_confidence > 0.6:
                action = "sell"
                confidence = sell_confidence
                
                # Collect reasons from bearish timeframes
                reasons = []
                for tf, rec in recommendations.items():
                    if rec["action"] == "sell":
                        for reason in rec["reasons"]:
                            if reason not in reasons:
                                reasons.append(f"{reason} ({tf})")
                                if len(reasons) >= 3:
                                    break
            else:
                action = "neutral"
                confidence = max(neutral_confidence, 0.5)  # At least 0.5 confidence for neutral
                reasons = ["Conflicting signals across timeframes", "Waiting for clearer direction"]
            
            overall["recommendation"] = {
                "action": action,
                "confidence": confidence,
                "reasons": reasons[:3],  # Top 3 reasons
                "timeframes": recommendations
            }
            
            return overall
        except Exception as e:
            logger.error(f"Error calculating overall analysis for {symbol}: {e}")
            return {}
    
    def generate_signal(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a trading signal based on market analysis.
        
        Args:
            analysis (Dict[str, Any]): Market analysis
            
        Returns:
            Optional[Dict[str, Any]]: Trading signal or None if no signal
        """
        try:
            # Check if analysis recommends an action with sufficient confidence
            recommendation = analysis["overall"]["recommendation"]
            
            if recommendation["action"] == "neutral" or recommendation["confidence"] < 0.7:
                logger.info(f"No signal generated for {analysis['symbol']}: {recommendation['action']} with confidence {recommendation['confidence']:.2f}")
                return None
            
            # Generate signal
            signal = {
                "signal_id": f"TRAE_AI_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "symbol": analysis["symbol"],
                "direction": "BUY" if recommendation["action"] == "buy" else "SELL",
                "strategy": "trae_ai",
                "confidence": recommendation["confidence"],
                "reasons": recommendation["reasons"],
                "timeframe": "multi",  # Multiple timeframes analyzed
                "source": "trae_ai"
            }
            
            # Add risk management parameters
            risk_config = self.config["risk_management"]
            
            # Default stop loss and take profit in pips
            signal["stop_loss"] = risk_config["default_stop_loss"]
            signal["take_profit"] = risk_config["default_take_profit"]
            
            # Adjust based on volatility
            volatility_level = analysis["overall"]["volatility"]["level"]
            if volatility_level == "high":
                signal["stop_loss"] = int(signal["stop_loss"] * 1.5)  # Wider stop for high volatility
                signal["take_profit"] = int(signal["take_profit"] * 1.5)  # Wider target for high volatility
            elif volatility_level == "low":
                signal["stop_loss"] = int(signal["stop_loss"] * 0.7)  # Tighter stop for low volatility
                signal["take_profit"] = int(signal["take_profit"] * 0.7)  # Tighter target for low volatility
            
            # Store signal
            self.signals.append(signal)
            self._save_signals()
            
            logger.info(f"Generated {signal['direction']} signal for {signal['symbol']} with confidence {signal['confidence']:.2f}")
            return signal
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
    
    def _save_signals(self) -> None:
        """Save signals to disk."""
        try:
            file_path = os.path.join(self.data_dir, "signals.json")
            with open(file_path, "w") as f:
                json.dump(self.signals, f, indent=2)
            logger.debug(f"Saved signals to {file_path}")
        except Exception as e:
            logger.error(f"Error saving signals: {e}")
    
    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trading signal by calling the stealth execution endpoint.
        
        Args:
            signal (Dict[str, Any]): Trading signal
            
        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            # Check if auto-execution is enabled
            if not self.config["execution"]["auto_execute"]:
                logger.info(f"Auto-execution disabled, signal not executed: {signal['signal_id']}")
                return {
                    "success": False,
                    "message": "Auto-execution disabled",
                    "signal_id": signal["signal_id"]
                }
            
            # Prepare request data
            endpoint = self.config["execution"]["endpoint"]
            api_key = self.config["execution"]["api_key"]
            
            # Replace environment variables
            if api_key.startswith("${"): 
                env_var = api_key[2:-1]  # Remove ${ and }
                api_key = os.environ.get(env_var, "")
            
            # Prepare request payload
            payload = {
                "signal_id": signal["signal_id"],
                "symbol": signal["symbol"],
                "direction": signal["direction"],
                "strategy": signal["strategy"],
                "stop_loss": signal["stop_loss"],
                "take_profit": signal["take_profit"],
                "confidence": signal["confidence"],
                "source": "trae_ai"
            }
            
            # Add API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": api_key
            }
            
            # Check if confirmation is required
            if self.config["execution"]["confirmation_required"]:
                logger.info(f"Signal requires confirmation: {signal['signal_id']}")
                return {
                    "success": False,
                    "message": "Confirmation required",
                    "signal_id": signal["signal_id"],
                    "payload": payload
                }
            
            # Send request to stealth execution endpoint
            logger.info(f"Executing signal: {signal['signal_id']}")
            response = requests.post(endpoint, json=payload, headers=headers)
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Signal executed successfully: {signal['signal_id']}")
                return {
                    "success": True,
                    "message": "Signal executed successfully",
                    "signal_id": signal["signal_id"],
                    "result": result
                }
            else:
                logger.error(f"Error executing signal: {signal['signal_id']} - {response.status_code} {response.text}")
                return {
                    "success": False,
                    "message": f"Error: {response.status_code} {response.text}",
                    "signal_id": signal["signal_id"]
                }
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "signal_id": signal.get("signal_id", "unknown")
            }
    
    def run_analysis_cycle(self) -> List[Dict[str, Any]]:
        """Run a complete analysis cycle for all configured symbols.
        
        Returns:
            List[Dict[str, Any]]: List of generated signals
        """
        try:
            generated_signals = []
            
            # Analyze each symbol
            for symbol in self.config["symbols"]:
                logger.info(f"Analyzing {symbol}...")
                
                # Analyze market
                analysis = self.analyze_market(symbol)
                
                # Generate signal
                signal = self.generate_signal(analysis)
                
                if signal:
                    generated_signals.append(signal)
                    
                    # Execute signal if auto-execution is enabled
                    if self.config["execution"]["auto_execute"]:
                        execution_result = self.execute_signal(signal)
                        logger.info(f"Execution result: {execution_result}")
            
            return generated_signals
        except Exception as e:
            logger.error(f"Error running analysis cycle: {e}")
            return []
    
    def start(self, interval: int = None) -> None:
        """Start the TRAE AI Agent.
        
        Args:
            interval (int, optional): Analysis interval in seconds. Defaults to config value.
        """
        if interval is None:
            interval = self.config.get("analysis_interval", 300)  # Default to 5 minutes
        
        logger.info(f"Starting TRAE AI Agent with analysis interval of {interval} seconds")
        
        try:
            while True:
                logger.info("Running analysis cycle...")
                signals = self.run_analysis_cycle()
                
                if signals:
                    logger.info(f"Generated {len(signals)} signals")
                else:
                    logger.info("No signals generated")
                
                logger.info(f"Sleeping for {interval} seconds...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("TRAE AI Agent stopped by user")
        except Exception as e:
            logger.error(f"Error in TRAE AI Agent: {e}")
    
    def run_once(self) -> List[Dict[str, Any]]:
        """Run a single analysis cycle.
        
        Returns:
            List[Dict[str, Any]]: List of generated signals
        """
        logger.info("Running single analysis cycle...")
        return self.run_analysis_cycle()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE AI Agent for market analysis and signal generation")
    parser.add_argument("--config", type=str, default="config/trae_ai_config.json", help="Path to configuration file")
    parser.add_argument("--interval", type=int, help="Analysis interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run a single analysis cycle and exit")
    parser.add_argument("--symbol", type=str, help="Analyze a specific symbol only")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no execution)")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set logging level")
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create TRAE AI Agent
    agent = TraeAIAgent(config_path=args.config)
    
    # Override config with command line arguments
    if args.symbol:
        agent.config["symbols"] = [args.symbol]
    
    if args.dry_run:
        agent.config["execution"]["auto_execute"] = False
        logger.info("Running in dry-run mode (no execution)")
    
    # Run agent
    if args.once:
        signals = agent.run_once()
        logger.info(f"Generated {len(signals)} signals")
        for signal in signals:
            logger.info(f"Signal: {signal['direction']} {signal['symbol']} (confidence: {signal['confidence']:.2f})")
    else:
        agent.start(interval=args.interval)


if __name__ == "__main__":
    main()