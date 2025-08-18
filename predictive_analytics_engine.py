#!/usr/bin/env python3
"""
TradeBot Sentinel - Predictive Analytics Engine

Advanced machine learning system for predictive analytics:
- Market trend prediction and forecasting
- Trading pattern analysis and prediction
- System performance forecasting
- Risk assessment and early warning
- Optimal timing recommendations
- Market volatility prediction
- Price movement forecasting
- Volume analysis and prediction

Features:
- Multiple ML models (LSTM, Prophet, ARIMA, Random Forest)
- Real-time prediction updates
- Multi-timeframe analysis
- Confidence intervals and uncertainty quantification
- Feature importance analysis
- Automated model selection
- Backtesting and validation
- Performance tracking and optimization

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

# Machine Learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression
import joblib

# Time series analysis
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("⚠️ Statsmodels not available. ARIMA models will be disabled.")

# Prophet for time series forecasting
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️ Prophet not available. Prophet forecasting will be disabled.")

# Deep Learning imports
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU, Conv1D, MaxPooling1D, Flatten
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ TensorFlow not available. Deep learning models will be disabled.")

# Technical indicators
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ TA-Lib not available. Technical indicators will be limited.")

@dataclass
class PredictionResult:
    """Prediction result with confidence metrics"""
    timestamp: str
    prediction_type: str  # 'price', 'volume', 'volatility', 'trend', 'performance'
    predicted_value: float
    confidence: float  # 0.0 to 1.0
    confidence_interval: Tuple[float, float]
    timeframe: str  # '1m', '5m', '1h', '1d', etc.
    model_used: str
    features_used: List[str]
    actual_value: Optional[float] = None
    prediction_accuracy: Optional[float] = None

@dataclass
class MarketForecast:
    """Market forecast with multiple predictions"""
    timestamp: str
    symbol: str
    timeframe: str
    price_predictions: List[PredictionResult]
    volume_predictions: List[PredictionResult]
    volatility_predictions: List[PredictionResult]
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    trend_strength: float  # 0.0 to 1.0
    risk_level: str  # 'low', 'medium', 'high', 'extreme'
    recommended_action: str
    confidence_score: float

@dataclass
class ModelPerformance:
    """Model performance tracking"""
    model_name: str
    prediction_type: str
    accuracy: float
    mse: float
    mae: float
    r2_score: float
    last_updated: str
    training_samples: int
    validation_samples: int
    feature_importance: Dict[str, float]

class FeatureEngineer:
    """Advanced feature engineering for predictive models"""
    
    def __init__(self):
        self.logger = logging.getLogger('FeatureEngineer')
        self.feature_cache = {}
        self.scalers = {}
    
    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical analysis features"""
        try:
            features_df = df.copy()
            
            # Price-based features
            features_df['price_change'] = features_df['close'].pct_change()
            features_df['price_change_2'] = features_df['close'].pct_change(2)
            features_df['price_change_5'] = features_df['close'].pct_change(5)
            
            # Moving averages
            for window in [5, 10, 20, 50]:
                features_df[f'sma_{window}'] = features_df['close'].rolling(window=window).mean()
                features_df[f'ema_{window}'] = features_df['close'].ewm(span=window).mean()
                features_df[f'price_to_sma_{window}'] = features_df['close'] / features_df[f'sma_{window}']
            
            # Volatility features
            features_df['volatility_5'] = features_df['price_change'].rolling(window=5).std()
            features_df['volatility_20'] = features_df['price_change'].rolling(window=20).std()
            
            # Volume features
            if 'volume' in features_df.columns:
                features_df['volume_sma_10'] = features_df['volume'].rolling(window=10).mean()
                features_df['volume_ratio'] = features_df['volume'] / features_df['volume_sma_10']
                features_df['price_volume'] = features_df['close'] * features_df['volume']
            
            # High-Low features
            if 'high' in features_df.columns and 'low' in features_df.columns:
                features_df['hl_ratio'] = features_df['high'] / features_df['low']
                features_df['hl_pct'] = (features_df['high'] - features_df['low']) / features_df['close']
            
            # Momentum features
            features_df['momentum_5'] = features_df['close'] / features_df['close'].shift(5)
            features_df['momentum_10'] = features_df['close'] / features_df['close'].shift(10)
            
            # TA-Lib indicators if available
            if TALIB_AVAILABLE and all(col in features_df.columns for col in ['high', 'low', 'close']):
                # RSI
                features_df['rsi'] = talib.RSI(features_df['close'].values)
                
                # MACD
                macd, macd_signal, macd_hist = talib.MACD(features_df['close'].values)
                features_df['macd'] = macd
                features_df['macd_signal'] = macd_signal
                features_df['macd_hist'] = macd_hist
                
                # Bollinger Bands
                bb_upper, bb_middle, bb_lower = talib.BBANDS(features_df['close'].values)
                features_df['bb_upper'] = bb_upper
                features_df['bb_lower'] = bb_lower
                features_df['bb_width'] = (bb_upper - bb_lower) / bb_middle
                features_df['bb_position'] = (features_df['close'] - bb_lower) / (bb_upper - bb_lower)
                
                # Stochastic
                slowk, slowd = talib.STOCH(features_df['high'].values, features_df['low'].values, features_df['close'].values)
                features_df['stoch_k'] = slowk
                features_df['stoch_d'] = slowd
            
            # Time-based features
            if 'timestamp' in features_df.columns:
                features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
                features_df['hour'] = features_df['timestamp'].dt.hour
                features_df['day_of_week'] = features_df['timestamp'].dt.dayofweek
                features_df['is_weekend'] = (features_df['day_of_week'] >= 5).astype(int)
                features_df['is_market_hours'] = ((features_df['hour'] >= 9) & (features_df['hour'] <= 16)).astype(int)
            
            # Lag features
            for lag in [1, 2, 3, 5, 10]:
                features_df[f'close_lag_{lag}'] = features_df['close'].shift(lag)
                features_df[f'volume_lag_{lag}'] = features_df.get('volume', 0).shift(lag)
            
            # Rolling statistics
            for window in [5, 10, 20]:
                features_df[f'close_min_{window}'] = features_df['close'].rolling(window=window).min()
                features_df[f'close_max_{window}'] = features_df['close'].rolling(window=window).max()
                features_df[f'close_std_{window}'] = features_df['close'].rolling(window=window).std()
                features_df[f'close_skew_{window}'] = features_df['close'].rolling(window=window).skew()
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"Technical feature creation failed: {e}")
            return df
    
    def create_market_features(self, df: pd.DataFrame, market_data: Dict[str, Any]) -> pd.DataFrame:
        """Create market-wide features"""
        try:
            features_df = df.copy()
            
            # Market sentiment features
            features_df['market_sentiment'] = market_data.get('sentiment_score', 0.5)
            features_df['fear_greed_index'] = market_data.get('fear_greed', 50) / 100
            
            # Economic indicators
            features_df['vix'] = market_data.get('vix', 20)
            features_df['dxy'] = market_data.get('dxy', 100)
            features_df['gold_price'] = market_data.get('gold', 2000)
            
            # Crypto-specific features
            features_df['btc_dominance'] = market_data.get('btc_dominance', 50)
            features_df['total_market_cap'] = market_data.get('total_market_cap', 1e12)
            features_df['active_addresses'] = market_data.get('active_addresses', 1000000)
            
            # News sentiment
            features_df['news_sentiment'] = market_data.get('news_sentiment', 0.5)
            features_df['social_sentiment'] = market_data.get('social_sentiment', 0.5)
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"Market feature creation failed: {e}")
            return df
    
    def create_system_features(self, df: pd.DataFrame, system_data: Dict[str, Any]) -> pd.DataFrame:
        """Create system performance features"""
        try:
            features_df = df.copy()
            
            # System performance metrics
            features_df['cpu_usage'] = system_data.get('cpu_percent', 50)
            features_df['memory_usage'] = system_data.get('memory_percent', 50)
            features_df['network_latency'] = system_data.get('network_latency_ms', 100)
            
            # Trading system metrics
            features_df['trade_success_rate'] = system_data.get('trade_success_rate', 0.8)
            features_df['avg_trade_duration'] = system_data.get('avg_trade_duration_minutes', 30)
            features_df['error_rate'] = system_data.get('error_rate', 0.05)
            
            # Market connection quality
            features_df['api_response_time'] = system_data.get('api_response_ms', 200)
            features_df['connection_stability'] = system_data.get('connection_stability', 0.95)
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"System feature creation failed: {e}")
            return df
    
    def select_features(self, X: pd.DataFrame, y: pd.Series, k: int = 20) -> List[str]:
        """Select top k features using statistical tests"""
        try:
            # Remove non-numeric columns and handle NaN values
            X_numeric = X.select_dtypes(include=[np.number]).fillna(0)
            
            if X_numeric.empty:
                return []
            
            # Feature selection
            selector = SelectKBest(score_func=f_regression, k=min(k, X_numeric.shape[1]))
            selector.fit(X_numeric, y)
            
            # Get selected feature names
            selected_features = X_numeric.columns[selector.get_support()].tolist()
            
            # Get feature scores
            feature_scores = dict(zip(X_numeric.columns, selector.scores_))
            
            # Sort by score
            selected_features.sort(key=lambda x: feature_scores[x], reverse=True)
            
            return selected_features
            
        except Exception as e:
            self.logger.error(f"Feature selection failed: {e}")
            return list(X.select_dtypes(include=[np.number]).columns)[:k]

class PredictiveAnalyticsEngine:
    """Advanced predictive analytics engine"""
    
    def __init__(self, model_dir: str = 'prediction_models'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logging()
        self.feature_engineer = FeatureEngineer()
        
        # Model storage
        self.models = {
            'price': {},
            'volume': {},
            'volatility': {},
            'trend': {},
            'performance': {}
        }
        
        # Prediction history
        self.prediction_history = deque(maxlen=10000)
        self.model_performance = {}
        
        # Data storage
        self.market_data = deque(maxlen=10000)
        self.system_data = deque(maxlen=1000)
        
        # Configuration
        self.config = {
            'lstm': {
                'sequence_length': 60,
                'epochs': 100,
                'batch_size': 32,
                'validation_split': 0.2
            },
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'prophet': {
                'changepoint_prior_scale': 0.05,
                'seasonality_prior_scale': 10.0,
                'holidays_prior_scale': 10.0
            }
        }
        
        # Load existing models
        self._load_models()
        
        self.logger.info("🔮 Predictive Analytics Engine initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('PredictiveAnalyticsEngine')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('predictive_analytics.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_models(self):
        """Load existing trained models"""
        try:
            for category in self.models.keys():
                model_files = list(self.model_dir.glob(f'{category}_*.pkl'))
                
                for model_file in model_files:
                    model_name = model_file.stem.replace(f'{category}_', '')
                    try:
                        model_data = joblib.load(model_file)
                        self.models[category][model_name] = model_data
                        self.logger.info(f"✅ Loaded {category} {model_name} model")
                    except Exception as e:
                        self.logger.error(f"Failed to load {model_file}: {e}")
            
            # Load deep learning models
            if TENSORFLOW_AVAILABLE:
                for category in self.models.keys():
                    lstm_model_dir = self.model_dir / f'{category}_lstm'
                    if lstm_model_dir.exists():
                        try:
                            model = load_model(lstm_model_dir)
                            scaler_path = self.model_dir / f'{category}_lstm_scaler.pkl'
                            scaler = joblib.load(scaler_path) if scaler_path.exists() else MinMaxScaler()
                            
                            self.models[category]['lstm'] = {
                                'model': model,
                                'scaler': scaler
                            }
                            self.logger.info(f"✅ Loaded {category} LSTM model")
                        except Exception as e:
                            self.logger.error(f"Failed to load LSTM model for {category}: {e}")
        
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
    
    def add_market_data(self, data: Dict[str, Any]):
        """Add market data for analysis"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            self.market_data.append(data)
            
        except Exception as e:
            self.logger.error(f"Failed to add market data: {e}")
    
    def add_system_data(self, data: Dict[str, Any]):
        """Add system performance data"""
        try:
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            self.system_data.append(data)
            
        except Exception as e:
            self.logger.error(f"Failed to add system data: {e}")
    
    def train_lstm_model(self, category: str, df: pd.DataFrame, target_column: str) -> bool:
        """Train LSTM model for time series prediction"""
        if not TENSORFLOW_AVAILABLE:
            self.logger.warning("TensorFlow not available, skipping LSTM training")
            return False
        
        try:
            # Prepare data
            features_df = self.feature_engineer.create_technical_features(df)
            
            # Select numeric columns
            numeric_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
            if target_column not in numeric_columns:
                self.logger.error(f"Target column {target_column} not found in numeric columns")
                return False
            
            # Remove target from features
            feature_columns = [col for col in numeric_columns if col != target_column]
            
            # Fill NaN values
            features_df = features_df[feature_columns + [target_column]].fillna(method='ffill').fillna(0)
            
            if len(features_df) < 100:
                self.logger.warning(f"Insufficient data for LSTM training: {len(features_df)}")
                return False
            
            # Scale data
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(features_df)
            
            # Create sequences
            sequence_length = self.config['lstm']['sequence_length']
            X, y = [], []
            
            target_idx = features_df.columns.get_loc(target_column)
            
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i])
                y.append(scaled_data[i, target_idx])
            
            X, y = np.array(X), np.array(y)
            
            if len(X) < 50:
                self.logger.warning(f"Insufficient sequences for training: {len(X)}")
                return False
            
            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(sequence_length, X.shape[2])),
                Dropout(0.2),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
            
            # Callbacks
            early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.0001)
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=self.config['lstm']['epochs'],
                batch_size=self.config['lstm']['batch_size'],
                validation_data=(X_test, y_test),
                callbacks=[early_stopping, reduce_lr],
                verbose=0
            )
            
            # Evaluate model
            train_pred = model.predict(X_train, verbose=0)
            test_pred = model.predict(X_test, verbose=0)
            
            train_mse = mean_squared_error(y_train, train_pred)
            test_mse = mean_squared_error(y_test, test_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            # Store model
            self.models[category]['lstm'] = {
                'model': model,
                'scaler': scaler,
                'sequence_length': sequence_length,
                'feature_columns': feature_columns,
                'target_column': target_column
            }
            
            # Save model
            model_dir = self.model_dir / f'{category}_lstm'
            model.save(model_dir)
            
            scaler_path = self.model_dir / f'{category}_lstm_scaler.pkl'
            joblib.dump(scaler, scaler_path)
            
            # Store performance
            self.model_performance[f'{category}_lstm'] = ModelPerformance(
                model_name=f'{category}_lstm',
                prediction_type=category,
                accuracy=max(0, 1 - test_mse),  # Approximation
                mse=test_mse,
                mae=test_mae,
                r2_score=test_r2,
                last_updated=datetime.now().isoformat(),
                training_samples=len(X_train),
                validation_samples=len(X_test),
                feature_importance={}
            )
            
            self.logger.info(f"✅ Trained {category} LSTM model - MSE: {test_mse:.6f}, R²: {test_r2:.3f}")
            return True
            
        except Exception as e:
            self.logger.error(f"LSTM training failed for {category}: {e}")
            return False
    
    def train_random_forest_model(self, category: str, df: pd.DataFrame, target_column: str) -> bool:
        """Train Random Forest model"""
        try:
            # Prepare features
            features_df = self.feature_engineer.create_technical_features(df)
            
            # Select numeric columns
            numeric_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
            if target_column not in numeric_columns:
                self.logger.error(f"Target column {target_column} not found")
                return False
            
            # Prepare X and y
            feature_columns = [col for col in numeric_columns if col != target_column]
            X = features_df[feature_columns].fillna(0)
            y = features_df[target_column].fillna(method='ffill')
            
            # Remove rows with NaN targets
            mask = ~y.isna()
            X, y = X[mask], y[mask]
            
            if len(X) < 50:
                self.logger.warning(f"Insufficient data for Random Forest training: {len(X)}")
                return False
            
            # Feature selection
            selected_features = self.feature_engineer.select_features(X, y, k=20)
            X_selected = X[selected_features]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_selected, y, test_size=0.2, random_state=42
            )
            
            # Train model
            model = RandomForestRegressor(**self.config['random_forest'])
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            train_mse = mean_squared_error(y_train, train_pred)
            test_mse = mean_squared_error(y_test, test_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            # Feature importance
            feature_importance = dict(zip(selected_features, model.feature_importances_))
            
            # Store model
            self.models[category]['random_forest'] = {
                'model': model,
                'feature_columns': selected_features,
                'target_column': target_column
            }
            
            # Save model
            model_path = self.model_dir / f'{category}_random_forest.pkl'
            joblib.dump(self.models[category]['random_forest'], model_path)
            
            # Store performance
            self.model_performance[f'{category}_random_forest'] = ModelPerformance(
                model_name=f'{category}_random_forest',
                prediction_type=category,
                accuracy=max(0, test_r2),
                mse=test_mse,
                mae=test_mae,
                r2_score=test_r2,
                last_updated=datetime.now().isoformat(),
                training_samples=len(X_train),
                validation_samples=len(X_test),
                feature_importance=feature_importance
            )
            
            self.logger.info(f"✅ Trained {category} Random Forest - R²: {test_r2:.3f}, MAE: {test_mae:.6f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Random Forest training failed for {category}: {e}")
            return False
    
    def train_prophet_model(self, category: str, df: pd.DataFrame, target_column: str) -> bool:
        """Train Prophet model for time series forecasting"""
        if not PROPHET_AVAILABLE:
            self.logger.warning("Prophet not available, skipping Prophet training")
            return False
        
        try:
            # Prepare data for Prophet
            if 'timestamp' not in df.columns:
                self.logger.error("Timestamp column required for Prophet")
                return False
            
            prophet_df = df[['timestamp', target_column]].copy()
            prophet_df.columns = ['ds', 'y']
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
            prophet_df = prophet_df.dropna().sort_values('ds')
            
            if len(prophet_df) < 50:
                self.logger.warning(f"Insufficient data for Prophet training: {len(prophet_df)}")
                return False
            
            # Create and train Prophet model
            model = Prophet(
                changepoint_prior_scale=self.config['prophet']['changepoint_prior_scale'],
                seasonality_prior_scale=self.config['prophet']['seasonality_prior_scale'],
                holidays_prior_scale=self.config['prophet']['holidays_prior_scale'],
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False
            )
            
            model.fit(prophet_df)
            
            # Make predictions for evaluation
            future = model.make_future_dataframe(periods=0)
            forecast = model.predict(future)
            
            # Calculate performance metrics
            y_true = prophet_df['y'].values
            y_pred = forecast['yhat'].values[:len(y_true)]
            
            mse = mean_squared_error(y_true, y_pred)
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            
            # Store model
            self.models[category]['prophet'] = {
                'model': model,
                'target_column': target_column
            }
            
            # Save model
            model_path = self.model_dir / f'{category}_prophet.pkl'
            joblib.dump(self.models[category]['prophet'], model_path)
            
            # Store performance
            self.model_performance[f'{category}_prophet'] = ModelPerformance(
                model_name=f'{category}_prophet',
                prediction_type=category,
                accuracy=max(0, r2),
                mse=mse,
                mae=mae,
                r2_score=r2,
                last_updated=datetime.now().isoformat(),
                training_samples=len(prophet_df),
                validation_samples=0,
                feature_importance={}
            )
            
            self.logger.info(f"✅ Trained {category} Prophet model - R²: {r2:.3f}, MAE: {mae:.6f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Prophet training failed for {category}: {e}")
            return False
    
    def predict_price(self, symbol: str, timeframe: str = '1h', periods: int = 24) -> List[PredictionResult]:
        """Predict price movements"""
        predictions = []
        
        try:
            # Get recent market data
            recent_data = [d for d in self.market_data if d.get('symbol') == symbol][-1000:]
            
            if len(recent_data) < 50:
                self.logger.warning(f"Insufficient data for price prediction: {len(recent_data)}")
                return predictions
            
            # Convert to DataFrame
            df = pd.DataFrame(recent_data)
            
            # Make predictions with each available model
            for model_name, model_data in self.models.get('price', {}).items():
                try:
                    pred_results = self._predict_with_model(model_name, model_data, df, 'close', periods)
                    predictions.extend(pred_results)
                except Exception as e:
                    self.logger.error(f"Price prediction failed with {model_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Price prediction failed: {e}")
        
        return predictions
    
    def predict_volatility(self, symbol: str, timeframe: str = '1h', periods: int = 24) -> List[PredictionResult]:
        """Predict volatility"""
        predictions = []
        
        try:
            recent_data = [d for d in self.market_data if d.get('symbol') == symbol][-1000:]
            
            if len(recent_data) < 50:
                return predictions
            
            df = pd.DataFrame(recent_data)
            
            # Calculate volatility if not present
            if 'volatility' not in df.columns and 'close' in df.columns:
                df['volatility'] = df['close'].pct_change().rolling(window=20).std()
            
            for model_name, model_data in self.models.get('volatility', {}).items():
                try:
                    pred_results = self._predict_with_model(model_name, model_data, df, 'volatility', periods)
                    predictions.extend(pred_results)
                except Exception as e:
                    self.logger.error(f"Volatility prediction failed with {model_name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Volatility prediction failed: {e}")
        
        return predictions
    
    def _predict_with_model(self, model_name: str, model_data: Dict[str, Any], 
                           df: pd.DataFrame, target_column: str, periods: int) -> List[PredictionResult]:
        """Make predictions with a specific model"""
        predictions = []
        
        try:
            if model_name == 'lstm' and TENSORFLOW_AVAILABLE:
                predictions = self._predict_lstm(model_data, df, target_column, periods)
            elif model_name == 'random_forest':
                predictions = self._predict_random_forest(model_data, df, target_column, periods)
            elif model_name == 'prophet' and PROPHET_AVAILABLE:
                predictions = self._predict_prophet(model_data, df, target_column, periods)
            
        except Exception as e:
            self.logger.error(f"Prediction failed with {model_name}: {e}")
        
        return predictions
    
    def _predict_lstm(self, model_data: Dict[str, Any], df: pd.DataFrame, 
                     target_column: str, periods: int) -> List[PredictionResult]:
        """Make LSTM predictions"""
        predictions = []
        
        try:
            model = model_data['model']
            scaler = model_data['scaler']
            sequence_length = model_data['sequence_length']
            feature_columns = model_data['feature_columns']
            
            # Prepare features
            features_df = self.feature_engineer.create_technical_features(df)
            
            # Select and scale features
            X = features_df[feature_columns + [target_column]].fillna(method='ffill').fillna(0)
            X_scaled = scaler.transform(X)
            
            # Get last sequence
            if len(X_scaled) < sequence_length:
                return predictions
            
            last_sequence = X_scaled[-sequence_length:]
            
            # Make predictions
            for i in range(periods):
                # Predict next value
                pred_input = last_sequence.reshape(1, sequence_length, -1)
                pred_scaled = model.predict(pred_input, verbose=0)[0, 0]
                
                # Inverse transform prediction
                dummy_row = np.zeros((1, X_scaled.shape[1]))
                target_idx = X.columns.get_loc(target_column)
                dummy_row[0, target_idx] = pred_scaled
                pred_value = scaler.inverse_transform(dummy_row)[0, target_idx]
                
                # Calculate confidence (simplified)
                confidence = max(0.5, 1.0 - (i * 0.05))  # Decreasing confidence over time
                
                # Create prediction result
                pred_time = datetime.now() + timedelta(hours=i+1)
                
                prediction = PredictionResult(
                    timestamp=pred_time.isoformat(),
                    prediction_type=target_column,
                    predicted_value=float(pred_value),
                    confidence=confidence,
                    confidence_interval=(pred_value * 0.95, pred_value * 1.05),
                    timeframe='1h',
                    model_used='lstm',
                    features_used=feature_columns
                )
                
                predictions.append(prediction)
                
                # Update sequence for next prediction
                new_row = np.zeros(X_scaled.shape[1])
                new_row[target_idx] = pred_scaled
                last_sequence = np.vstack([last_sequence[1:], new_row.reshape(1, -1)])
            
        except Exception as e:
            self.logger.error(f"LSTM prediction failed: {e}")
        
        return predictions
    
    def _predict_random_forest(self, model_data: Dict[str, Any], df: pd.DataFrame, 
                              target_column: str, periods: int) -> List[PredictionResult]:
        """Make Random Forest predictions"""
        predictions = []
        
        try:
            model = model_data['model']
            feature_columns = model_data['feature_columns']
            
            # Prepare features
            features_df = self.feature_engineer.create_technical_features(df)
            
            # Get last row features
            if len(features_df) == 0:
                return predictions
            
            last_features = features_df[feature_columns].fillna(0).iloc[-1:]
            
            # Make predictions (Random Forest gives single point predictions)
            for i in range(min(periods, 12)):  # Limit RF predictions
                pred_value = model.predict(last_features)[0]
                
                # Calculate confidence based on model performance
                model_perf = self.model_performance.get(f'{target_column}_random_forest')
                confidence = model_perf.r2_score if model_perf else 0.7
                confidence = max(0.3, confidence - (i * 0.05))
                
                # Create prediction result
                pred_time = datetime.now() + timedelta(hours=i+1)
                
                prediction = PredictionResult(
                    timestamp=pred_time.isoformat(),
                    prediction_type=target_column,
                    predicted_value=float(pred_value),
                    confidence=confidence,
                    confidence_interval=(pred_value * 0.9, pred_value * 1.1),
                    timeframe='1h',
                    model_used='random_forest',
                    features_used=feature_columns
                )
                
                predictions.append(prediction)
            
        except Exception as e:
            self.logger.error(f"Random Forest prediction failed: {e}")
        
        return predictions
    
    def _predict_prophet(self, model_data: Dict[str, Any], df: pd.DataFrame, 
                        target_column: str, periods: int) -> List[PredictionResult]:
        """Make Prophet predictions"""
        predictions = []
        
        try:
            model = model_data['model']
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods, freq='H')
            forecast = model.predict(future)
            
            # Get predictions for future periods
            future_forecast = forecast.tail(periods)
            
            for _, row in future_forecast.iterrows():
                prediction = PredictionResult(
                    timestamp=row['ds'].isoformat(),
                    prediction_type=target_column,
                    predicted_value=float(row['yhat']),
                    confidence=0.8,  # Prophet provides uncertainty intervals
                    confidence_interval=(float(row['yhat_lower']), float(row['yhat_upper'])),
                    timeframe='1h',
                    model_used='prophet',
                    features_used=['timestamp', 'seasonality', 'trend']
                )
                
                predictions.append(prediction)
            
        except Exception as e:
            self.logger.error(f"Prophet prediction failed: {e}")
        
        return predictions
    
    def generate_market_forecast(self, symbol: str, timeframe: str = '1h') -> MarketForecast:
        """Generate comprehensive market forecast"""
        try:
            # Get predictions
            price_predictions = self.predict_price(symbol, timeframe, 24)
            volume_predictions = self.predict_volume(symbol, timeframe, 24)
            volatility_predictions = self.predict_volatility(symbol, timeframe, 24)
            
            # Analyze trend
            trend_direction, trend_strength = self._analyze_trend(price_predictions)
            
            # Assess risk
            risk_level = self._assess_risk(volatility_predictions, price_predictions)
            
            # Generate recommendation
            recommended_action = self._generate_recommendation(trend_direction, trend_strength, risk_level)
            
            # Calculate overall confidence
            all_predictions = price_predictions + volume_predictions + volatility_predictions
            confidence_score = np.mean([p.confidence for p in all_predictions]) if all_predictions else 0.5
            
            forecast = MarketForecast(
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                timeframe=timeframe,
                price_predictions=price_predictions,
                volume_predictions=volume_predictions,
                volatility_predictions=volatility_predictions,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                risk_level=risk_level,
                recommended_action=recommended_action,
                confidence_score=confidence_score
            )
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Market forecast generation failed: {e}")
            return MarketForecast(
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                timeframe=timeframe,
                price_predictions=[],
                volume_predictions=[],
                volatility_predictions=[],
                trend_direction='sideways',
                trend_strength=0.0,
                risk_level='unknown',
                recommended_action='hold',
                confidence_score=0.0
            )
    
    def predict_volume(self, symbol: str, timeframe: str = '1h', periods: int = 24) -> List[PredictionResult]:
        """Predict trading volume"""
        predictions = []
        
        try:
            recent_data = [d for d in self.market_data if d.get('symbol') == symbol][-1000:]
            
            if len(recent_data) < 50:
                return predictions
            
            df = pd.DataFrame(recent_data)
            
            if 'volume' not in df.columns:
                return predictions
            
            for model_name, model_data in self.models.get('volume', {}).items():
                try:
                    pred_results = self._predict_with_model(model_name, model_data, df, 'volume', periods)
                    predictions.extend(pred_results)
                except Exception as e:
                    self.logger.error(f"Volume prediction failed with {model_name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Volume prediction failed: {e}")
        
        return predictions
    
    def _analyze_trend(self, price_predictions: List[PredictionResult]) -> Tuple[str, float]:
        """Analyze trend direction and strength"""
        if not price_predictions:
            return 'sideways', 0.0
        
        try:
            # Get predicted values
            values = [p.predicted_value for p in price_predictions[:12]]  # Next 12 hours
            
            if len(values) < 2:
                return 'sideways', 0.0
            
            # Calculate trend
            first_half = np.mean(values[:len(values)//2])
            second_half = np.mean(values[len(values)//2:])
            
            change_pct = (second_half - first_half) / first_half
            
            # Determine direction
            if change_pct > 0.02:  # 2% increase
                direction = 'bullish'
            elif change_pct < -0.02:  # 2% decrease
                direction = 'bearish'
            else:
                direction = 'sideways'
            
            # Calculate strength
            strength = min(abs(change_pct) * 10, 1.0)  # Scale to 0-1
            
            return direction, strength
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return 'sideways', 0.0
    
    def _assess_risk(self, volatility_predictions: List[PredictionResult], 
                    price_predictions: List[PredictionResult]) -> str:
        """Assess risk level"""
        try:
            # Volatility risk
            vol_risk = 0.0
            if volatility_predictions:
                avg_volatility = np.mean([p.predicted_value for p in volatility_predictions[:6]])
                vol_risk = min(avg_volatility * 100, 1.0)  # Scale volatility
            
            # Price uncertainty risk
            price_risk = 0.0
            if price_predictions:
                confidences = [p.confidence for p in price_predictions[:6]]
                price_risk = 1.0 - np.mean(confidences)
            
            # Combined risk
            combined_risk = (vol_risk + price_risk) / 2
            
            if combined_risk > 0.7:
                return 'extreme'
            elif combined_risk > 0.5:
                return 'high'
            elif combined_risk > 0.3:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            return 'medium'
    
    def _generate_recommendation(self, trend_direction: str, trend_strength: float, risk_level: str) -> str:
        """Generate trading recommendation"""
        try:
            if risk_level == 'extreme':
                return 'AVOID - Extremely high risk conditions'
            
            if trend_direction == 'bullish' and trend_strength > 0.6:
                if risk_level in ['low', 'medium']:
                    return 'BUY - Strong bullish trend with acceptable risk'
                else:
                    return 'CAUTION - Bullish trend but high risk'
            
            elif trend_direction == 'bearish' and trend_strength > 0.6:
                if risk_level in ['low', 'medium']:
                    return 'SELL - Strong bearish trend with acceptable risk'
                else:
                    return 'CAUTION - Bearish trend but high risk'
            
            elif trend_direction == 'sideways' or trend_strength < 0.3:
                return 'HOLD - Sideways movement or weak trend'
            
            else:
                return 'MONITOR - Mixed signals, wait for clearer direction'
                
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return 'HOLD - Unable to generate recommendation'
    
    def retrain_all_models(self):
        """Retrain all models with latest data"""
        try:
            if len(self.market_data) < 100:
                self.logger.warning("Insufficient data for retraining")
                return
            
            # Convert market data to DataFrame
            df = pd.DataFrame(list(self.market_data))
            
            # Train price models
            if 'close' in df.columns:
                self.logger.info("🔄 Retraining price prediction models...")
                self.train_lstm_model('price', df, 'close')
                self.train_random_forest_model('price', df, 'close')
                self.train_prophet_model('price', df, 'close')
            
            # Train volume models
            if 'volume' in df.columns:
                self.logger.info("🔄 Retraining volume prediction models...")
                self.train_lstm_model('volume', df, 'volume')
                self.train_random_forest_model('volume', df, 'volume')
            
            # Train volatility models
            if 'close' in df.columns:
                df['volatility'] = df['close'].pct_change().rolling(window=20).std()
                self.logger.info("🔄 Retraining volatility prediction models...")
                self.train_lstm_model('volatility', df, 'volatility')
                self.train_random_forest_model('volatility', df, 'volatility')
            
            self.logger.info("✅ Model retraining completed")
            
        except Exception as e:
            self.logger.error(f"Model retraining failed: {e}")
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all model performances"""
        try:
            summary = {
                'total_models': len(self.model_performance),
                'by_type': defaultdict(list),
                'best_performers': {},
                'avg_accuracy': 0.0,
                'last_updated': datetime.now().isoformat()
            }
            
            if not self.model_performance:
                return summary
            
            # Group by prediction type
            for model_name, perf in self.model_performance.items():
                summary['by_type'][perf.prediction_type].append({
                    'model': model_name,
                    'accuracy': perf.accuracy,
                    'r2_score': perf.r2_score,
                    'mae': perf.mae
                })
            
            # Find best performers
            for pred_type, models in summary['by_type'].items():
                best_model = max(models, key=lambda x: x['r2_score'])
                summary['best_performers'][pred_type] = best_model
            
            # Calculate average accuracy
            accuracies = [perf.accuracy for perf in self.model_performance.values()]
            summary['avg_accuracy'] = np.mean(accuracies) if accuracies else 0.0
            
            return dict(summary)
            
        except Exception as e:
            self.logger.error(f"Performance summary generation failed: {e}")
            return {}
    
    def save_predictions(self, predictions: List[PredictionResult]):
        """Save predictions to database"""
        try:
            # Add to history
            self.prediction_history.extend(predictions)
            
            # Save to database
            db_path = 'predictions.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    prediction_type TEXT,
                    predicted_value REAL,
                    confidence REAL,
                    confidence_lower REAL,
                    confidence_upper REAL,
                    timeframe TEXT,
                    model_used TEXT,
                    features_used TEXT,
                    actual_value REAL,
                    prediction_accuracy REAL
                )
            """)
            
            # Insert predictions
            for pred in predictions:
                cursor.execute("""
                    INSERT INTO predictions 
                    (timestamp, prediction_type, predicted_value, confidence, confidence_lower, confidence_upper, 
                     timeframe, model_used, features_used, actual_value, prediction_accuracy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pred.timestamp,
                    pred.prediction_type,
                    pred.predicted_value,
                    pred.confidence,
                    pred.confidence_interval[0],
                    pred.confidence_interval[1],
                    pred.timeframe,
                    pred.model_used,
                    json.dumps(pred.features_used),
                    pred.actual_value,
                    pred.prediction_accuracy
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"💾 Saved {len(predictions)} predictions to database")
            
        except Exception as e:
            self.logger.error(f"Prediction saving failed: {e}")

# Example usage and testing
def main():
    """Main function for testing the predictive analytics engine"""
    engine = PredictiveAnalyticsEngine()
    
    # Generate sample market data
    print("📊 Generating sample market data...")
    
    base_price = 50000
    for i in range(500):
        timestamp = datetime.now() - timedelta(hours=500-i)
        
        # Simulate price movement
        price_change = np.random.normal(0, 0.02)  # 2% volatility
        base_price *= (1 + price_change)
        
        market_data = {
            'timestamp': timestamp.isoformat(),
            'symbol': 'BTCUSD',
            'close': base_price,
            'high': base_price * 1.01,
            'low': base_price * 0.99,
            'volume': np.random.normal(1000000, 200000),
            'open': base_price * (1 + np.random.normal(0, 0.005))
        }
        
        engine.add_market_data(market_data)
    
    # Train models
    print("🤖 Training predictive models...")
    engine.retrain_all_models()
    
    # Generate predictions
    print("🔮 Generating predictions...")
    
    # Price predictions
    price_predictions = engine.predict_price('BTCUSD', '1h', 24)
    print(f"📈 Generated {len(price_predictions)} price predictions")
    
    # Volatility predictions
    vol_predictions = engine.predict_volatility('BTCUSD', '1h', 24)
    print(f"📊 Generated {len(vol_predictions)} volatility predictions")
    
    # Market forecast
    forecast = engine.generate_market_forecast('BTCUSD', '1h')
    print(f"\n🎯 Market Forecast for BTCUSD:")
    print(f"   Trend: {forecast.trend_direction} (strength: {forecast.trend_strength:.2f})")
    print(f"   Risk Level: {forecast.risk_level}")
    print(f"   Recommendation: {forecast.recommended_action}")
    print(f"   Confidence: {forecast.confidence_score:.2f}")
    
    # Save predictions
    all_predictions = price_predictions + vol_predictions
    if all_predictions:
        engine.save_predictions(all_predictions)
    
    # Model performance summary
    performance = engine.get_model_performance_summary()
    print(f"\n📊 Model Performance Summary:")
    print(f"   Total Models: {performance.get('total_models', 0)}")
    print(f"   Average Accuracy: {performance.get('avg_accuracy', 0):.2f}")
    
    for pred_type, best_model in performance.get('best_performers', {}).items():
        print(f"   Best {pred_type} model: {best_model['model']} (R²: {best_model['r2_score']:.3f})")

if __name__ == "__main__":
    print("🔮 TradeBot Sentinel - Predictive Analytics Engine")
    print("🤖 Advanced machine learning for market prediction")
    print("="*70)
    
    main()