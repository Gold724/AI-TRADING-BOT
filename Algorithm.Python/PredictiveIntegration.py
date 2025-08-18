from AlgorithmImports import *
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import sys
import os

# Add the parent directory to sys.path to import predictive_analytics_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from predictive_analytics_engine import PredictiveAnalyticsEngine, PredictionResult
    PREDICTIVE_ENGINE_AVAILABLE = True
except ImportError:
    PREDICTIVE_ENGINE_AVAILABLE = False
    print("⚠️ Predictive Analytics Engine not available")

@dataclass
class MLPrediction:
    """Container for ML prediction data"""
    price_prediction: float
    volatility_prediction: float
    trend_strength: float
    confidence: float
    model_used: str
    prediction_horizon: int  # hours
    features_used: List[str]
    timestamp: datetime

@dataclass
class EntryTimingSignal:
    """Container for ML-based entry timing signals"""
    signal_strength: float  # -1 to 1
    optimal_entry_time: datetime
    predicted_move: float  # Expected price move
    confidence: float
    risk_score: float
    supporting_models: List[str]

class PredictiveIntegrationMixin:
    """Mixin class to add predictive analytics to trading strategies"""
    
    def initialize_predictive_engine(self):
        """Initialize the predictive analytics engine"""
        if not PREDICTIVE_ENGINE_AVAILABLE:
            self.Debug("⚠️ Predictive Analytics Engine not available")
            self.use_ml_predictions = False
            return
        
        try:
            self.predictive_engine = PredictiveAnalyticsEngine()
            self.use_ml_predictions = True
            self.ml_predictions = {}
            self.last_ml_update = None
            self.ml_update_interval = timedelta(hours=1)  # Update predictions hourly
            
            # ML prediction parameters
            self.ml_confidence_threshold = 0.6
            self.ml_prediction_weight = 0.3  # Weight in final decision
            self.ml_lookback_hours = 168  # 1 week of data for training
            
            self.Debug("✅ Predictive Analytics Engine initialized")
            
        except Exception as e:
            self.Debug(f"❌ Failed to initialize Predictive Engine: {e}")
            self.use_ml_predictions = False
    
    def update_ml_predictions(self, symbol: Symbol, current_price: float):
        """Update ML predictions for the given symbol"""
        if not self.use_ml_predictions:
            return
        
        # Check if update is needed
        if (self.last_ml_update and 
            self.Time - self.last_ml_update < self.ml_update_interval):
            return
        
        try:
            # Prepare market data for ML engine
            market_data = self.prepare_market_data_for_ml(symbol, current_price)
            
            if len(market_data) < 50:  # Need sufficient data
                self.Debug("⚠️ Insufficient data for ML predictions")
                return
            
            # Add market data to predictive engine
            for data_point in market_data:
                self.predictive_engine.add_market_data(data_point)
            
            # Generate predictions
            symbol_str = str(symbol).replace(' ', '_')
            
            # Price predictions
            price_predictions = self.predictive_engine.predict_price(
                symbol_str, '1h', 24
            )
            
            # Volatility predictions
            vol_predictions = self.predictive_engine.predict_volatility(
                symbol_str, '1h', 24
            )
            
            # Market forecast
            forecast = self.predictive_engine.generate_market_forecast(
                symbol_str, '1h'
            )
            
            # Store predictions
            self.ml_predictions[symbol] = {
                'price_predictions': price_predictions,
                'volatility_predictions': vol_predictions,
                'market_forecast': forecast,
                'timestamp': self.Time
            }
            
            self.last_ml_update = self.Time
            
            self.Debug(f"🤖 Updated ML predictions for {symbol} - "
                      f"Price: {len(price_predictions)}, Vol: {len(vol_predictions)}")
            
        except Exception as e:
            self.Debug(f"❌ ML prediction update failed: {e}")
    
    def prepare_market_data_for_ml(self, symbol: Symbol, current_price: float) -> List[Dict]:
        """Prepare market data in the format expected by ML engine"""
        market_data = []
        
        try:
            # Get historical data
            history = self.History(symbol, self.ml_lookback_hours, Resolution.Hour)
            
            if history.empty:
                return market_data
            
            # Convert to the format expected by predictive engine
            for index, row in history.iterrows():
                if hasattr(index, 'levels') and len(index.levels) >= 2:
                    # Multi-index (Symbol, Time)
                    timestamp = index[1] if len(index) > 1 else index[0]
                else:
                    # Single index (Time)
                    timestamp = index
                
                data_point = {
                    'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                    'symbol': str(symbol).replace(' ', '_'),
                    'open': float(row['open']) if 'open' in row else float(current_price),
                    'high': float(row['high']) if 'high' in row else float(current_price),
                    'low': float(row['low']) if 'low' in row else float(current_price),
                    'close': float(row['close']) if 'close' in row else float(current_price),
                    'volume': float(row['volume']) if 'volume' in row else 1000000
                }
                
                market_data.append(data_point)
            
            # Add current data point
            current_data = {
                'timestamp': self.Time.isoformat(),
                'symbol': str(symbol).replace(' ', '_'),
                'open': float(current_price),
                'high': float(current_price),
                'low': float(current_price),
                'close': float(current_price),
                'volume': 1000000  # Default volume
            }
            market_data.append(current_data)
            
        except Exception as e:
            self.Debug(f"❌ Failed to prepare market data: {e}")
        
        return market_data
    
    def get_ml_entry_timing_signal(self, symbol: Symbol, signal_direction: int) -> Optional[EntryTimingSignal]:
        """Get ML-based entry timing signal"""
        if not self.use_ml_predictions or symbol not in self.ml_predictions:
            return None
        
        try:
            predictions = self.ml_predictions[symbol]
            price_preds = predictions['price_predictions']
            vol_preds = predictions['volatility_predictions']
            forecast = predictions['market_forecast']
            
            if not price_preds:
                return None
            
            # Analyze next few hours for optimal entry
            best_entry_time = self.Time
            best_signal_strength = 0
            predicted_move = 0
            confidence = 0
            risk_score = 0.5
            supporting_models = []
            
            # Look at next 6 hours of predictions
            for i, pred in enumerate(price_preds[:6]):
                if pred.confidence < self.ml_confidence_threshold:
                    continue
                
                # Calculate expected move
                current_price = self.Securities[symbol].Price
                expected_move = (pred.predicted_value - current_price) / current_price
                
                # Check if move aligns with signal direction
                move_direction = 1 if expected_move > 0 else -1
                
                if move_direction == signal_direction:
                    signal_strength = abs(expected_move) * pred.confidence
                    
                    if signal_strength > best_signal_strength:
                        best_signal_strength = signal_strength
                        best_entry_time = datetime.fromisoformat(pred.timestamp)
                        predicted_move = expected_move
                        confidence = pred.confidence
                        supporting_models.append(pred.model_used)
            
            # Adjust for volatility
            if vol_preds:
                avg_vol = sum(v.predicted_value for v in vol_preds[:6]) / len(vol_preds[:6])
                risk_score = min(1.0, avg_vol / 0.02)  # Normalize to 2% volatility
            
            # Use market forecast for additional context
            if forecast:
                if hasattr(forecast, 'trend_strength'):
                    best_signal_strength *= (1 + forecast.trend_strength * 0.2)
                if hasattr(forecast, 'confidence_score'):
                    confidence = (confidence + forecast.confidence_score) / 2
            
            if best_signal_strength > 0.1:  # Minimum threshold
                return EntryTimingSignal(
                    signal_strength=best_signal_strength,
                    optimal_entry_time=best_entry_time,
                    predicted_move=predicted_move,
                    confidence=confidence,
                    risk_score=risk_score,
                    supporting_models=supporting_models
                )
            
        except Exception as e:
            self.Debug(f"❌ ML entry timing signal failed: {e}")
        
        return None
    
    def get_ml_price_prediction(self, symbol: Symbol, hours_ahead: int = 1) -> Optional[MLPrediction]:
        """Get ML price prediction for specified hours ahead"""
        if not self.use_ml_predictions or symbol not in self.ml_predictions:
            return None
        
        try:
            predictions = self.ml_predictions[symbol]
            price_preds = predictions['price_predictions']
            vol_preds = predictions['volatility_predictions']
            
            if not price_preds or len(price_preds) < hours_ahead:
                return None
            
            # Get prediction for specified time horizon
            target_pred = price_preds[hours_ahead - 1]
            vol_pred = vol_preds[hours_ahead - 1] if len(vol_preds) >= hours_ahead else None
            
            # Calculate trend strength
            trend_strength = 0
            if len(price_preds) >= 3:
                prices = [p.predicted_value for p in price_preds[:3]]
                if prices[0] < prices[1] < prices[2]:
                    trend_strength = 0.8  # Strong uptrend
                elif prices[0] > prices[1] > prices[2]:
                    trend_strength = -0.8  # Strong downtrend
                else:
                    # Calculate slope
                    x = np.array([0, 1, 2])
                    y = np.array(prices)
                    slope = np.polyfit(x, y, 1)[0]
                    trend_strength = np.tanh(slope / (prices[0] * 0.01))  # Normalize
            
            return MLPrediction(
                price_prediction=target_pred.predicted_value,
                volatility_prediction=vol_pred.predicted_value if vol_pred else 0.02,
                trend_strength=trend_strength,
                confidence=target_pred.confidence,
                model_used=target_pred.model_used,
                prediction_horizon=hours_ahead,
                features_used=target_pred.features_used,
                timestamp=datetime.fromisoformat(target_pred.timestamp)
            )
            
        except Exception as e:
            self.Debug(f"❌ ML price prediction failed: {e}")
        
        return None
    
    def apply_ml_filter(self, base_signal_strength: float, symbol: Symbol, 
                       signal_direction: int) -> Tuple[float, Dict[str, Any]]:
        """Apply ML filter to enhance base trading signal"""
        if not self.use_ml_predictions:
            return base_signal_strength, {'ml_applied': False}
        
        try:
            # Get ML predictions
            ml_prediction = self.get_ml_price_prediction(symbol, 1)
            entry_timing = self.get_ml_entry_timing_signal(symbol, signal_direction)
            
            ml_info = {
                'ml_applied': True,
                'ml_prediction': None,
                'entry_timing': None,
                'ml_adjustment': 0
            }
            
            if not ml_prediction:
                return base_signal_strength, ml_info
            
            ml_info['ml_prediction'] = {
                'price': ml_prediction.price_prediction,
                'confidence': ml_prediction.confidence,
                'trend_strength': ml_prediction.trend_strength
            }
            
            # Calculate ML adjustment
            ml_adjustment = 0
            
            # Price prediction alignment
            current_price = self.Securities[symbol].Price
            predicted_move = (ml_prediction.price_prediction - current_price) / current_price
            predicted_direction = 1 if predicted_move > 0 else -1
            
            if predicted_direction == signal_direction:
                # ML agrees with signal
                alignment_boost = abs(predicted_move) * ml_prediction.confidence * 2
                ml_adjustment += alignment_boost
            else:
                # ML disagrees with signal
                alignment_penalty = -abs(predicted_move) * ml_prediction.confidence
                ml_adjustment += alignment_penalty
            
            # Trend strength adjustment
            if abs(ml_prediction.trend_strength) > 0.3:
                trend_direction = 1 if ml_prediction.trend_strength > 0 else -1
                if trend_direction == signal_direction:
                    ml_adjustment += abs(ml_prediction.trend_strength) * 0.5
                else:
                    ml_adjustment -= abs(ml_prediction.trend_strength) * 0.3
            
            # Entry timing adjustment
            if entry_timing:
                ml_info['entry_timing'] = {
                    'signal_strength': entry_timing.signal_strength,
                    'confidence': entry_timing.confidence,
                    'predicted_move': entry_timing.predicted_move
                }
                
                # Boost signal if optimal entry time is now or soon
                time_to_optimal = (entry_timing.optimal_entry_time - self.Time).total_seconds() / 3600
                if 0 <= time_to_optimal <= 2:  # Within next 2 hours
                    timing_boost = entry_timing.signal_strength * (2 - time_to_optimal) / 2
                    ml_adjustment += timing_boost
            
            # Apply confidence weighting
            ml_adjustment *= ml_prediction.confidence
            
            # Apply ML weight to final adjustment
            final_adjustment = ml_adjustment * self.ml_prediction_weight
            
            # Calculate enhanced signal strength
            enhanced_signal = base_signal_strength + final_adjustment
            enhanced_signal = max(-3, min(3, enhanced_signal))  # Clamp to [-3, 3]
            
            ml_info['ml_adjustment'] = final_adjustment
            
            self.Debug(f"🤖 ML Filter Applied - Base: {base_signal_strength:.2f}, "
                      f"Enhanced: {enhanced_signal:.2f}, Adjustment: {final_adjustment:.2f}")
            
            return enhanced_signal, ml_info
            
        except Exception as e:
            self.Debug(f"❌ ML filter application failed: {e}")
            return base_signal_strength, {'ml_applied': False, 'error': str(e)}
    
    def should_retrain_ml_models(self) -> bool:
        """Determine if ML models should be retrained"""
        if not self.use_ml_predictions:
            return False
        
        # Retrain weekly or if performance degrades
        if not hasattr(self, 'last_ml_retrain'):
            self.last_ml_retrain = self.Time - timedelta(days=8)  # Force initial training
        
        days_since_retrain = (self.Time - self.last_ml_retrain).days
        
        # Retrain weekly
        if days_since_retrain >= 7:
            return True
        
        # Check performance degradation (placeholder)
        # In production, this would check prediction accuracy
        
        return False
    
    def retrain_ml_models(self, symbol: Symbol):
        """Retrain ML models with recent data"""
        if not self.use_ml_predictions:
            return
        
        try:
            self.Debug("🔄 Retraining ML models...")
            
            # Prepare training data
            market_data = self.prepare_market_data_for_ml(symbol, self.Securities[symbol].Price)
            
            if len(market_data) < 100:
                self.Debug("⚠️ Insufficient data for ML retraining")
                return
            
            # Add data to engine
            for data_point in market_data:
                self.predictive_engine.add_market_data(data_point)
            
            # Retrain models
            success = self.predictive_engine.retrain_all_models()
            
            if success:
                self.last_ml_retrain = self.Time
                self.Debug("✅ ML models retrained successfully")
            else:
                self.Debug("❌ ML model retraining failed")
                
        except Exception as e:
            self.Debug(f"❌ ML retraining error: {e}")