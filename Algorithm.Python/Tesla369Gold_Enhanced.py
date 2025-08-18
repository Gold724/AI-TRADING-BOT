from AlgorithmImports import *
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from PredictiveIntegration import PredictiveIntegrationMixin, MLPrediction, EntryTimingSignal
from AdvancedRiskManagement import AdvancedRiskManager, RiskMetrics, DynamicStopLoss, PositionRisk
from AdvancedTechnicalIndicators import AdvancedTechnicalIndicators, TechnicalSignalSummary, RSIDivergence, MACDAnalysis, ATRVolatilityFilter, IchimokuAnalysis
from SmartExitStrategies import SmartExitManager, TrailingStopConfig, PartialProfitConfig, TimeBasedExitConfig, ExitSignal
from ReinforcementLearning import ReinforcementLearningManager, QLearningConfig, QState, QAction

@dataclass
class SentimentData:
    """Container for sentiment analysis data"""
    score: float  # -1 to 1 (bearish to bullish)
    confidence: float  # 0 to 1
    source: str
    timestamp: datetime
    components: Dict[str, float] = None

class Tesla369GoldEnhanced(QCAlgorithm, PredictiveIntegrationMixin):
    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetCash(100000)  # paper cash; risk is governed by contract sizing
        self.UniverseSettings.Resolution = Resolution.Minute

        # Parameters
        self.tradesPerDay = int(self.GetParameter("trades_per_day") or "3")
        if self.tradesPerDay not in (3,6,9):
            self.tradesPerDay = 3
        self.dailyTarget = float(self.GetParameter("daily_profit_target") or "535.71")
        self.dailyMaxDD = float(self.GetParameter("daily_max_drawdown") or "267.0")
        self.maxContracts = int(self.GetParameter("max_contracts") or "3")
        self.defaultContracts = int(self.GetParameter("default_contracts") or "1")
        
        # Target and Stop percentages
        self.tpPct = float(self.GetParameter("tp_pct") or "0.0015")  # 0.15%
        self.slPct = float(self.GetParameter("sl_pct") or "0.0002")  # 0.02%

        # Sentiment Analysis Parameters
        self.sentimentThreshold = float(self.GetParameter("sentiment_threshold") or "0.3")
        self.sentimentWeight = float(self.GetParameter("sentiment_weight") or "0.25")
        self.useSentimentFilter = bool(self.GetParameter("use_sentiment_filter") or True)
        
        # Multi-timeframe Analysis Parameters
        self.useMultiTimeframe = bool(self.GetParameter("use_multi_timeframe") or True)
        self.mtfWeight = float(self.GetParameter("mtf_weight") or "0.2")
        
        # Dynamic Position Sizing Parameters
        self.useDynamicSizing = bool(self.GetParameter("use_dynamic_sizing") or True)
        self.volatilityLookback = int(self.GetParameter("volatility_lookback") or "20")
        self.maxRiskPerTrade = float(self.GetParameter("max_risk_per_trade") or "0.02")  # 2%

        # Add Gold Futures (GC)
        future = self.AddFuture(Futures.Metals.Gold, Resolution.Minute)
        future.SetFilter(timedelta(0), timedelta(days=60))
        self.futureSymbol = None

        self.SetWarmUp(200, Resolution.Minute)
        self.pnlToday = 0
        self.tradesToday = 0
        self.currentDate = None
        
        # Track open orders for OCO management
        self.openOrders = {}
        self.lastTradePrice = None

        # Multi-timeframe consolidators
        self.consolidator1m = TradeBarConsolidator(timedelta(minutes=1))
        self.consolidator5m = TradeBarConsolidator(timedelta(minutes=5))
        self.consolidator15m = TradeBarConsolidator(timedelta(minutes=15))
        self.consolidator1h = TradeBarConsolidator(timedelta(hours=1))
        
        self.SubscriptionManager.AddConsolidator(future.Symbol, self.consolidator1m)
        self.SubscriptionManager.AddConsolidator(future.Symbol, self.consolidator5m)
        self.SubscriptionManager.AddConsolidator(future.Symbol, self.consolidator15m)
        self.SubscriptionManager.AddConsolidator(future.Symbol, self.consolidator1h)
        
        # Rolling windows for different timeframes
        self.bars1m = RollingWindow[TradeBar](100)
        self.bars5m = RollingWindow[TradeBar](50)
        self.bars15m = RollingWindow[TradeBar](30)
        self.bars1h = RollingWindow[TradeBar](24)
        
        self.consolidator1m.DataConsolidated += self.OnOneMinuteBar
        self.consolidator5m.DataConsolidated += self.OnFiveMinuteBar
        self.consolidator15m.DataConsolidated += self.OnFifteenMinuteBar
        self.consolidator1h.DataConsolidated += self.OnOneHourBar

        # Technical Indicators
        self.rsi = RelativeStrengthIndex(14)
        self.macd = MovingAverageConvergenceDivergence(12, 26, 9)
        self.atr = AverageTrueRange(14)
        self.ema20 = ExponentialMovingAverage(20)
        self.ema50 = ExponentialMovingAverage(50)
        
        # Volume analysis
        self.volAvg = SimpleMovingAverage(20)
        self.vwapSumPV = 0
        self.vwapSumV = 0

        # Track prior session H/L
        self.prevSessHigh = None
        self.prevSessLow = None
        
        # Sentiment data storage
        self.sentimentHistory = RollingWindow[SentimentData](50)
        self.lastSentimentUpdate = None
        
        # Performance tracking
        self.winStreak = 0
        self.lossStreak = 0
        self.totalTrades = 0
        self.winningTrades = 0
        
        # Volatility tracking for dynamic sizing
        self.volatilityWindow = RollingWindow[float](self.volatilityLookback)

        # Reset counters daily
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(0,1), self.ResetDaily)
        
        # Auto-flat at 15:30 NY
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(15,30), self.FlattenPositions)
        
        # Update sentiment every 15 minutes
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.Every(timedelta(minutes=15)), self.UpdateSentiment)
        
        # Schedule ML model retraining (weekly)
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday), self.TimeRules.At(2, 0), self.ScheduledMLRetrain)
        
        # Initialize predictive analytics engine
        self.initialize_predictive_engine()
        
        # Initialize advanced risk manager
        self.risk_manager = AdvancedRiskManager(self)
        self.Debug("🛡️ Advanced Risk Management System initialized")
        
        # Initialize Advanced Technical Indicators (will be initialized when symbol is available)
        self.advanced_tech = None
        self.technical_signal_summary = None
        self.rsi_divergence_trades = 0
        self.macd_signal_trades = 0
        self.ichimoku_trades = 0
        self.high_confidence_tech_trades = 0
        
        # Initialize Smart Exit Strategies
        trailing_config = TrailingStopConfig(
            initial_stop_atr_multiplier=2.0,
            trail_start_profit_atr=1.5,
            trail_step_atr=0.5,
            min_trail_distance_atr=1.0
        )
        
        partial_config = PartialProfitConfig(
            first_target_atr=2.0,
            first_target_percentage=0.3,
            second_target_atr=4.0,
            second_target_percentage=0.5,
            final_target_atr=6.0
        )
        
        time_config = TimeBasedExitConfig(
            london_session_exit_minutes=240,
            ny_session_exit_minutes=300,
            overlap_session_exit_minutes=180,
            max_trade_duration_hours=8,
            friday_exit_hour=15
        )
        
        self.exit_manager = SmartExitManager(trailing_config, partial_config, time_config)
        self.Debug("🎯 Smart Exit Strategies initialized")
        
        # Smart exit tracking variables
        self.trailing_stop_trades = 0
        self.partial_profit_trades = 0
        self.time_based_exit_trades = 0
        self.smart_exit_profit = 0.0
        
        # Initialize Reinforcement Learning Manager
        rl_config = QLearningConfig(
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon=0.2,  # Higher exploration initially
            epsilon_decay=0.995,
            epsilon_min=0.05,
            memory_size=5000,
            batch_size=32,
            update_frequency=50
        )
        
        self.rl_manager = ReinforcementLearningManager(self, rl_config)
        self.Debug("🧠 Reinforcement Learning System initialized")
        
        # RL tracking variables
        self.rl_trades = 0
        self.rl_profit = 0.0
        self.rl_recommendations_used = 0

        # Session windows (NY)
        self.ny = TimeZones.NewYork
        
        # Logging setup
        self.tradeLog = []
        
        self.Debug("Tesla369Gold Enhanced Strategy Initialized with AI Features")

    def OnSecuritiesChanged(self, changes):
        # Choose the nearest GC contract
        for sec in changes.AddedSecurities:
            if sec.Symbol.SecurityType == SecurityType.Future and sec.Symbol.ID.Symbol == "GC":
                if self.futureSymbol is None:
                    self.futureSymbol = sec.Symbol
                    self.Debug(f"Selected GC contract: {self.futureSymbol}")
                    
                    # Register indicators with the symbol
                    self.RegisterIndicator(self.futureSymbol, self.rsi, Resolution.Minute)
                    self.RegisterIndicator(self.futureSymbol, self.macd, Resolution.Minute)
                    self.RegisterIndicator(self.futureSymbol, self.atr, Resolution.Minute)
                    self.RegisterIndicator(self.futureSymbol, self.ema20, Resolution.Minute)
                    self.RegisterIndicator(self.futureSymbol, self.ema50, Resolution.Minute)
                    self.RegisterIndicator(self.futureSymbol, self.volAvg, Resolution.Minute)
                    
                    # Initialize advanced technical indicators with the symbol
                    self.advanced_tech = AdvancedTechnicalIndicators(self, self.futureSymbol)
                    self.Debug(f"📊 Advanced Technical Indicators initialized for {self.futureSymbol}")

    def UpdateSentiment(self):
        """Update sentiment analysis for Gold"""
        try:
            if not self.futureSymbol:
                return
                
            # Simulate sentiment analysis (in production, this would call real sentiment API)
            current_time = self.Time
            
            # Basic sentiment calculation based on technical indicators
            sentiment_score = self.CalculateBasicSentiment()
            
            # Create sentiment data
            sentiment_data = SentimentData(
                timestamp=current_time.strftime("%Y-%m-%d %H:%M:%S"),
                symbol="GC",
                sentiment_score=sentiment_score,
                confidence=0.7,  # Default confidence
                volume_confirmation=self.CheckVolumeConfirmation(),
                risk_level=self.AssessRiskLevel(sentiment_score),
                reasoning=f"Technical sentiment based on RSI: {self.rsi.Current.Value:.2f}, MACD: {self.macd.Current.Value:.4f}"
            )
            
            self.sentimentHistory.Add(sentiment_data)
            self.lastSentimentUpdate = current_time
            
            self.Debug(f"Sentiment Updated: Score={sentiment_score:.3f}, Risk={sentiment_data.risk_level}")
            
        except Exception as e:
            self.Debug(f"Error updating sentiment: {str(e)}")

    def CalculateBasicSentiment(self) -> float:
        """Calculate basic sentiment from technical indicators"""
        try:
            if not self.rsi.IsReady or not self.macd.IsReady:
                return 0.0
                
            sentiment_components = []
            
            # RSI component
            rsi_value = self.rsi.Current.Value
            if rsi_value > 70:
                rsi_sentiment = -0.5  # Overbought - bearish
            elif rsi_value < 30:
                rsi_sentiment = 0.5   # Oversold - bullish
            else:
                rsi_sentiment = (50 - rsi_value) / 50  # Normalized
            sentiment_components.append(rsi_sentiment)
            
            # MACD component
            macd_value = self.macd.Current.Value
            macd_signal = self.macd.Signal.Current.Value
            macd_sentiment = 0.5 if macd_value > macd_signal else -0.5
            sentiment_components.append(macd_sentiment)
            
            # EMA trend component
            if self.ema20.IsReady and self.ema50.IsReady:
                if self.ema20.Current.Value > self.ema50.Current.Value:
                    ema_sentiment = 0.3  # Bullish trend
                else:
                    ema_sentiment = -0.3  # Bearish trend
                sentiment_components.append(ema_sentiment)
            
            # Average sentiment
            final_sentiment = np.mean(sentiment_components)
            return max(-1.0, min(1.0, final_sentiment))  # Clamp to [-1, 1]
            
        except Exception as e:
            self.Debug(f"Error calculating sentiment: {str(e)}")
            return 0.0

    def CheckVolumeConfirmation(self) -> bool:
        """Check if current volume confirms the sentiment"""
        try:
            if not self.volAvg.IsReady:
                return False
                
            current_volume = self.Securities[self.futureSymbol].Volume if self.futureSymbol else 0
            avg_volume = self.volAvg.Current.Value
            
            return current_volume > avg_volume * 1.2  # 20% above average
            
        except Exception as e:
            self.Debug(f"Error checking volume confirmation: {str(e)}")
            return False

    def AssessRiskLevel(self, sentiment_score: float) -> str:
        """Assess risk level based on sentiment score"""
        abs_sentiment = abs(sentiment_score)
        
        if abs_sentiment > 0.7:
            return "high"
        elif abs_sentiment > 0.4:
            return "medium"
        else:
            return "low"

    def GetSentimentFilter(self) -> Tuple[bool, float, str]:
        """Get sentiment filter for trade decisions"""
        try:
            if not self.useSentimentFilter or self.sentimentHistory.Count == 0:
                return True, 1.0, "No sentiment filter applied"
                
            latest_sentiment = self.sentimentHistory[0]
            
            # Check if sentiment is strong enough
            if abs(latest_sentiment.sentiment_score) < self.sentimentThreshold:
                return False, 0.0, f"Sentiment too weak: {latest_sentiment.sentiment_score:.3f}"
            
            # Check risk level
            if latest_sentiment.risk_level == "high":
                risk_multiplier = 0.5  # Reduce position size
            elif latest_sentiment.risk_level == "medium":
                risk_multiplier = 0.75
            else:
                risk_multiplier = 1.0
            
            # Volume confirmation bonus
            if latest_sentiment.volume_confirmation:
                risk_multiplier *= 1.1
            
            return True, risk_multiplier, latest_sentiment.reasoning
            
        except Exception as e:
            self.Debug(f"Error in sentiment filter: {str(e)}")
            return True, 1.0, "Sentiment filter error"

    def CalculateDynamicPositionSize(self, signal_strength: float, sentiment_multiplier: float) -> int:
        """Calculate dynamic position size based on volatility and sentiment"""
        try:
            if not self.useDynamicSizing:
                return self.defaultContracts
                
            # Base position size
            base_size = self.defaultContracts
            
            # Volatility adjustment
            if self.atr.IsReady and self.volatilityWindow.Count > 0:
                current_atr = self.atr.Current.Value
                avg_volatility = np.mean([v for v in self.volatilityWindow])
                
                if avg_volatility > 0:
                    volatility_ratio = current_atr / avg_volatility
                    # Reduce size in high volatility
                    volatility_multiplier = 1.0 / max(1.0, volatility_ratio)
                else:
                    volatility_multiplier = 1.0
            else:
                volatility_multiplier = 1.0
            
            # Performance adjustment
            if self.winStreak >= 3:
                performance_multiplier = 1.2  # Increase size on winning streak
            elif self.lossStreak >= 2:
                performance_multiplier = 0.8  # Reduce size on losing streak
            else:
                performance_multiplier = 1.0
            
            # Calculate final size
            final_size = base_size * signal_strength * sentiment_multiplier * volatility_multiplier * performance_multiplier
            
            # Clamp to reasonable bounds
            final_size = max(1, min(self.maxContracts, int(round(final_size))))
            
            return final_size
            
        except Exception as e:
            self.Debug(f"Error calculating dynamic position size: {str(e)}")
            return self.defaultContracts

    def OnOneMinuteBar(self, sender, bar):
        """Handle 1-minute bar data"""
        self.bars1m.Add(bar)
        
        # Update volatility tracking
        if self.bars1m.Count >= 2:
            price_change = abs(bar.Close - self.bars1m[1].Close) / self.bars1m[1].Close
            self.volatilityWindow.Add(price_change)

    def OnFifteenMinuteBar(self, sender, bar):
        """Handle 15-minute bar data"""
        self.bars15m.Add(bar)

    def OnOneHourBar(self, sender, bar):
        """Handle 1-hour bar data"""
        self.bars1h.Add(bar)

    def ResetDaily(self):
        """Reset daily counters and update session levels"""
        self.pnlToday = 0
        self.tradesToday = 0
        self.currentDate = self.Time.date()
        self.openOrders = {}
        
        # Reset VWAP calculation
        self.vwapSumPV = 0
        self.vwapSumV = 0
        
        # Update previous session H/L using yesterday's data
        if self.bars5m.Count > 0:
            highs = [b.High for b in list(self.bars5m)]
            lows = [b.Low for b in list(self.bars5m)]
            self.prevSessHigh = max(highs) if highs else None
            self.prevSessLow = min(lows) if lows else None
            
        self.Debug(f"Daily reset - PrevHigh: {self.prevSessHigh}, PrevLow: {self.prevSessLow}")
        
    def FlattenPositions(self):
        """Auto-flat all positions at 15:30 NY"""
        if self.futureSymbol and self.Portfolio[self.futureSymbol].Quantity != 0:
            self.Liquidate(self.futureSymbol)
            self.Debug("Auto-flattened positions at 15:30 NY")
            
        # Cancel all open orders
        for ticket in self.openOrders.values():
            if ticket.Status == OrderStatus.Submitted or ticket.Status == OrderStatus.PartiallyFilled:
                ticket.Cancel()

    def OnFiveMinuteBar(self, sender, bar):
        """Enhanced 5-minute bar processing with AI features"""
        if self.IsWarmingUp or not self.futureSymbol:
            return
            
        self.bars5m.Add(bar)
        
        # Update ML predictions
        self.update_ml_predictions(self.futureSymbol, bar.Close)
        
        # Update risk metrics
        self.risk_manager.update_risk_metrics(self.Time, self.Portfolio.TotalPortfolioValue)
        
        # Update advanced technical indicators
        if self.advanced_tech:
            self.advanced_tech.update(bar)
            
            # Get comprehensive technical analysis
            if self.advanced_tech.is_ready():
                self.technical_signal_summary = self.advanced_tech.get_comprehensive_analysis()
        
        # Process smart exit strategies
        self.process_smart_exits(bar)
        
        # Update VWAP
        typical_price = (bar.High + bar.Low + bar.Close) / 3
        volume = bar.Volume
        self.vwapSumPV += typical_price * volume
        self.vwapSumV += volume
        vwap = self.vwapSumPV / self.vwapSumV if self.vwapSumV > 0 else bar.Close
        
        # Check daily limits
        if self.tradesToday >= self.tradesPerDay:
            return
            
        if abs(self.pnlToday) >= self.dailyTarget or self.pnlToday <= -self.dailyMaxDD:
            return
            
        # Check if in session window
        if not self.InSessionWindow():
            return
            
        # Get sentiment filter
        sentiment_allowed, sentiment_multiplier, sentiment_reason = self.GetSentimentFilter()
        if not sentiment_allowed:
            self.Debug(f"Trade blocked by sentiment: {sentiment_reason}")
            return
        
        # Enhanced signal analysis with multi-timeframe confluence, ML integration, and advanced technical indicators
        signal_strength, signal_direction = self.AnalyzeEnhancedSignalsWithML(bar, vwap)
        
        if signal_strength > 0.6:  # Minimum signal strength threshold
            # Calculate dynamic position size
            position_size = self.CalculateDynamicPositionSize(signal_strength, sentiment_multiplier)
            
            # Create signal data for enhanced trade execution
            signal_data = {
                'signal_strength': signal_strength,
                'direction': 1 if signal_direction == "BUY" else -1,
                'confidence': 0.8,  # Base confidence
                'risk_level': 'medium',
                'ml_info': {}
            }
            
            # Execute trade
            if signal_direction == "BUY":
                self.ExecuteEnhancedTrade("BUY", bar.Close, position_size, signal_strength, signal_data)
            elif signal_direction == "SELL":
                self.ExecuteEnhancedTrade("SELL", bar.Close, position_size, signal_strength, signal_data)

    def AnalyzeEnhancedSignalsWithML(self, bar, vwap) -> Tuple[float, str]:
        """Enhanced signal analysis with multiple confirmations and ML integration"""
        try:
            if self.bars5m.Count < 5:
                return 0.0, "HOLD"
            
            signal_components = []
            
            # Original volume spike logic
            volume_spike = bar.Volume > self.volAvg.Current.Value * 1.5 if self.volAvg.IsReady else False
            if volume_spike:
                signal_components.append(0.3)
            
            # VWAP confluence
            price_above_vwap = bar.Close > vwap
            vwap_distance = abs(bar.Close - vwap) / vwap
            if vwap_distance < 0.002:  # Close to VWAP
                signal_components.append(0.2)
            
            # RSI signals
            if self.rsi.IsReady:
                rsi_value = self.rsi.Current.Value
                if rsi_value < 30:  # Oversold
                    signal_components.append(0.4)
                elif rsi_value > 70:  # Overbought
                    signal_components.append(-0.4)
            
            # MACD signals
            if self.macd.IsReady:
                macd_value = self.macd.Current.Value
                macd_signal = self.macd.Signal.Current.Value
                if macd_value > macd_signal:
                    signal_components.append(0.3)
                else:
                    signal_components.append(-0.3)
            
            # EMA trend confirmation
            if self.ema20.IsReady and self.ema50.IsReady:
                if self.ema20.Current.Value > self.ema50.Current.Value:
                    signal_components.append(0.2)  # Bullish trend
                else:
                    signal_components.append(-0.2)  # Bearish trend
            
            # Multi-timeframe confluence
            if self.useMultiTimeframe:
                mtf_signal = self.GetMultiTimeframeSignal()
                signal_components.append(mtf_signal * self.mtfWeight)
            
            # Advanced technical indicators
            if self.technical_signal_summary:
                tech_signal = self.GetAdvancedTechnicalSignal()
                signal_components.append(tech_signal * 0.3)  # 30% weight for advanced tech
            
            # Calculate base signal
            total_signal = sum(signal_components)
            base_strength = min(1.0, abs(total_signal))
            signal_direction_num = 1 if total_signal > 0 else -1 if total_signal < 0 else 0
            
            # Apply ML filter if signal exists
            if signal_direction_num != 0 and base_strength > 0.3:
                enhanced_strength, ml_info = self.apply_ml_filter(
                    base_strength, self.futureSymbol, signal_direction_num
                )
                self.Debug(f"ML Enhancement: Base={base_strength:.3f}, Enhanced={enhanced_strength:.3f}, Confidence={ml_info.get('confidence', 0):.3f}")
            else:
                enhanced_strength = base_strength
            
            signal_direction = "BUY" if enhanced_strength > 0 and signal_direction_num > 0 else "SELL" if enhanced_strength > 0 and signal_direction_num < 0 else "HOLD"
            
            return enhanced_strength, signal_direction
            
        except Exception as e:
            self.Debug(f"Error in enhanced signal analysis with ML: {str(e)}")
            return 0.0, "HOLD"

    def GetMultiTimeframeSignal(self) -> float:
        """Get multi-timeframe confluence signal"""
        try:
            signals = []
            
            # 15-minute trend
            if self.bars15m.Count >= 3:
                recent_15m = list(self.bars15m)[:3]
                if all(bar.Close > recent_15m[i+1].Close for i, bar in enumerate(recent_15m[:-1])):
                    signals.append(0.5)  # Bullish 15m trend
                elif all(bar.Close < recent_15m[i+1].Close for i, bar in enumerate(recent_15m[:-1])):
                    signals.append(-0.5)  # Bearish 15m trend
            
            # 1-hour trend
            if self.bars1h.Count >= 2:
                if self.bars1h[0].Close > self.bars1h[1].Close:
                    signals.append(0.3)  # Bullish 1h
                else:
                    signals.append(-0.3)  # Bearish 1h
            
            return np.mean(signals) if signals else 0.0
            
        except Exception as e:
            self.Debug(f"Error in multi-timeframe analysis: {str(e)}")
            return 0.0

    def ExecuteEnhancedTrade(self, direction: str, price: float, contracts: int, signal_strength: float, signal_data=None):
        """Execute trade with enhanced risk management, dynamic stops, and ML integration"""
        try:
            if self.Portfolio[self.futureSymbol].Quantity != 0:
                return  # Already in position
            
            # Get ML info from signal data
            ml_info = signal_data.get('ml_info', {}) if signal_data else {}
            risk_level = signal_data.get('risk_level', 'medium') if signal_data else 'medium'
            
            # Calculate enhanced dynamic position size
            enhanced_size = self.calculate_enhanced_position_size(
                signal_strength, risk_level, price, ml_info
            )
            
            # Apply risk management position sizing
            risk_adjusted_contracts = self.risk_manager.get_risk_adjusted_position_size(
                enhanced_size, signal_strength
            )
            
            if risk_adjusted_contracts == 0:
                self.Debug(f"⚠️ Risk manager blocked trade due to risk limits")
                return
            
            # Use the smaller of calculated sizes for safety
            final_size = min(contracts, risk_adjusted_contracts)
            
            # Ensure position size limits
            final_size = max(1, min(self.maxContracts, final_size))
            
            # Dynamic stop loss based on ATR with ML enhancement
            if self.atr.IsReady:
                atr_value = self.atr.Current.Value
                dynamic_sl_pct = max(self.slPct, atr_value / price * 0.5)  # ATR-based stop
            else:
                atr_value = 0.01
                dynamic_sl_pct = self.slPct
            
            # Calculate dynamic stop-loss parameters using risk manager
            direction_int = 1 if direction == "BUY" else -1
            dynamic_stop = self.risk_manager.calculate_dynamic_stop_loss(
                self.futureSymbol, price, direction_int, atr_value
            )
            
            # Adjust stops based on dynamic risk management
            stop_multiplier = dynamic_stop.atr_multiplier
            profit_multiplier = stop_multiplier * 1.5  # 1.5:1 risk-reward base
            
            if ml_info.get('ml_applied', False):
                ml_pred = ml_info.get('ml_prediction', {})
                predicted_vol = ml_pred.get('volatility_prediction', atr_value)
                
                # Apply volatility adjustment from dynamic stop
                vol_adjustment = dynamic_stop.volatility_adjustment
                profit_multiplier *= vol_adjustment
                
                # Tighter stops for high-confidence predictions
                if ml_pred.get('confidence', 0) > 0.8:
                    stop_multiplier *= 0.9
                    profit_multiplier *= 1.1
            
            # Get RL recommendations before trade execution
            current_state = QState(
                price=price,
                rsi=self.rsi.Current.Value if self.rsi.IsReady else 50.0,
                macd=self.macd.Current.Value if self.macd.IsReady else 0.0,
                atr=atr_value,
                volume_ratio=1.0,  # Will be calculated from bar data when available
                volatility=self.current_volatility,
                session=self.GetCurrentSession(),
                time_of_day=self.Time.hour + self.Time.minute / 60.0
            )
            
            rl_action = self.rl_manager.get_recommendation(current_state)
            
            # Apply RL recommendations to trade parameters
            if rl_action:
                # Adjust position size based on RL confidence
                if hasattr(rl_action, 'position_multiplier'):
                    final_size = int(final_size * rl_action.position_multiplier)
                    final_size = max(1, min(final_size, self.maxContracts))
                    self.Debug(f"RL adjusted position size: {final_size} (multiplier: {rl_action.position_multiplier})")
                
                # Adjust stop loss based on RL recommendation
                if hasattr(rl_action, 'stop_multiplier'):
                    stop_multiplier *= rl_action.stop_multiplier
                    self.Debug(f"RL adjusted stop multiplier: {stop_multiplier}")
                
                # Adjust take profit based on RL recommendation
                if hasattr(rl_action, 'profit_multiplier'):
                    profit_multiplier *= rl_action.profit_multiplier
                    self.Debug(f"RL adjusted profit multiplier: {profit_multiplier}")
                
                self.rl_recommendations_used += 1
            
            # Apply maximum loss protection
            max_loss_per_contract = price * dynamic_stop.maximum_loss_pct
            max_stop_distance = max_loss_per_contract
            
            # Adjust target based on signal strength and ML with risk limits
            dynamic_tp_pct = self.tpPct * (1 + signal_strength * 0.5) * profit_multiplier / 4.0
            dynamic_sl_pct = min(dynamic_sl_pct * stop_multiplier / 2.5, max_stop_distance / price)
            
            # Final risk check before placing order
            position_risk = self.risk_manager.check_position_risk(self.futureSymbol)
            if position_risk and position_risk.heat_score > 0.15:  # 15% concentration limit
                self.Debug(f"⚠️ Position concentration too high, reducing size")
                final_size = max(1, int(final_size * 0.5))
            
            if direction == "BUY":
                ticket = self.MarketOrder(self.futureSymbol, final_size)
                if ticket:
                    self.AttachEnhancedTargets(ticket, price, dynamic_tp_pct, dynamic_sl_pct, "BUY")
            else:
                ticket = self.MarketOrder(self.futureSymbol, -final_size)
                if ticket:
                    self.AttachEnhancedTargets(ticket, price, dynamic_tp_pct, dynamic_sl_pct, "SELL")
            
            self.tradesToday += 1
            self.totalTrades += 1
            self.lastTradePrice = price
            
            # Enhanced trade logging with ML info and risk metrics
            risk_summary = self.risk_manager.get_current_risk_summary()
            
            trade_log = {
                "timestamp": self.Time.strftime("%Y-%m-%d %H:%M:%S"),
                "direction": direction,
                "price": price,
                "contracts": final_size,
                "original_contracts": contracts,
                "risk_adjusted_contracts": risk_adjusted_contracts,
                "signal_strength": signal_strength,
                "risk_level": risk_level,
                "dynamic_sl_pct": dynamic_sl_pct,
                "dynamic_tp_pct": dynamic_tp_pct,
                "sentiment_score": self.sentimentHistory[0].sentiment_score if self.sentimentHistory.Count > 0 else 0,
                "rsi": self.rsi.Current.Value if self.rsi.IsReady else 0,
                "macd": self.macd.Current.Value if self.macd.IsReady else 0,
                "atr": atr_value,
                "stop_multiplier": stop_multiplier,
                "profit_multiplier": profit_multiplier,
                "portfolio_var": risk_summary.get('var_1day', 0),
                "risk_adjusted": final_size != contracts
            }
            
            # Add ML info to log
            if ml_info.get('ml_applied', False):
                trade_log.update({
                    "ml_applied": True,
                    "ml_confidence": ml_info.get('ml_prediction', {}).get('confidence', 0),
                    "ml_price_prediction": ml_info.get('ml_prediction', {}).get('price', 0),
                    "ml_adjustment": ml_info.get('ml_adjustment', 0),
                    "predicted_move": ml_info.get('entry_timing', {}).get('predicted_move', 0)
                })
            else:
                trade_log["ml_applied"] = False
            
            self.tradeLog.append(trade_log)
            
            # Add position to smart exit manager for tracking
            if ticket and ticket.Status == OrderStatus.Submitted:
                session = self.GetCurrentSession()
                self.exit_manager.add_position(
                    symbol=str(self.futureSymbol),
                    entry_time=self.Time,
                    entry_price=price,
                    position_size=final_size,
                    direction=direction.lower(),
                    session=session
                )
                self.Debug(f"🎯 Position added to smart exit manager: {direction} {final_size} @ {price:.2f} ({session} session)")
            
            # Enhanced debug logging with risk metrics
            ml_status = "✨ ML-Enhanced" if ml_info.get('ml_applied', False) else "📊 Standard"
            ml_conf = ml_info.get('ml_prediction', {}).get('confidence', 0)
            
            self.Debug(f"🚀 {ml_status} Trade: {direction} {final_size} @ {price:.2f} "
                      f"(SL: {dynamic_sl_pct:.4f}, TP: {dynamic_tp_pct:.4f}, Signal: {signal_strength:.3f}, "
                      f"Risk: {risk_level}, ML_Conf: {ml_conf:.2f})")
            self.Debug(f"⚖️ Risk Metrics - ATR Mult: {dynamic_stop.atr_multiplier:.1f}x, Portfolio VaR: {risk_summary.get('var_1day', 0):.2%}")
            
            if final_size != contracts:
                self.Debug(f"📉 Position size adjusted: {contracts} → {final_size} (risk management)")
            
        except Exception as e:
            self.Debug(f"Error executing enhanced trade: {str(e)}")
    
    def GetCurrentSession(self) -> str:
        """Determine current trading session"""
        ny_time = self.Time.ConvertFromUtc(self.ny)
        hour = ny_time.hour
        
        # London session: 3:00 AM - 8:00 AM NY time
        if 3 <= hour < 8:
            return 'london'
        # London-NY overlap: 8:00 AM - 12:00 PM NY time
        elif 8 <= hour < 12:
            return 'overlap'
        # NY session: 12:00 PM - 4:00 PM NY time
        elif 12 <= hour < 16:
            return 'ny'
        else:
            return 'other'
    
    def process_smart_exits(self, bar):
        """Process smart exit strategies for all open positions"""
        try:
            if not self.exit_manager or self.Portfolio[self.futureSymbol].Quantity == 0:
                return
            
            current_price = bar.Close
            current_time = self.Time
            
            # Update exit manager with current market data
            self.exit_manager.update_market_data(current_price, current_time)
            
            # Check for exit signals
            exit_signals = self.exit_manager.check_exit_conditions(str(self.futureSymbol))
            
            for signal in exit_signals:
                self.execute_smart_exit(signal, current_price)
                
        except Exception as e:
            self.Debug(f"Error processing smart exits: {str(e)}")
    
    def execute_smart_exit(self, exit_signal, current_price: float):
        """Execute a smart exit signal"""
        try:
            position = self.Portfolio[self.futureSymbol]
            if position.Quantity == 0:
                return
            
            exit_size = exit_signal.exit_size
            if exit_signal.exit_type == 'partial':
                # Partial exit - close portion of position
                if position.Quantity > 0:
                    exit_size = min(exit_size, position.Quantity)
                    ticket = self.MarketOrder(self.futureSymbol, -exit_size)
                else:
                    exit_size = min(exit_size, abs(position.Quantity))
                    ticket = self.MarketOrder(self.futureSymbol, exit_size)
            else:
                # Full exit - close entire position
                ticket = self.Liquidate(self.futureSymbol)
            
            if ticket:
                # Update tracking variables
                if exit_signal.exit_type == 'trailing_stop':
                    self.trailing_stop_trades += 1
                elif exit_signal.exit_type == 'partial':
                    self.partial_profit_trades += 1
                elif exit_signal.exit_type == 'time_based':
                    self.time_based_exit_trades += 1
                
                # Calculate profit from this exit
                if position.Quantity != 0:
                    avg_price = position.AveragePrice
                    if position.Quantity > 0:  # Long position
                        profit = (current_price - avg_price) * exit_size
                    else:  # Short position
                        profit = (avg_price - current_price) * exit_size
                    
                    self.smart_exit_profit += profit
                
                # Log the smart exit
                self.Debug(f"🎯 Smart Exit: {exit_signal.exit_type.upper()} - "
                          f"Size: {exit_size}, Price: {current_price:.2f}, "
                          f"Reason: {exit_signal.reason}")
                
                # Execute the exit signal in the manager
                self.exit_manager.execute_exit_signal(exit_signal)
                
        except Exception as e:
            self.Debug(f"Error executing smart exit: {str(e)}")
 
     def AttachEnhancedTargets(self, ticket, entry_price: float, tp_pct: float, sl_pct: float, direction: str):
        """Attach enhanced OCO targets with dynamic levels"""
        try:
            if direction == "BUY":
                limit_price = entry_price * (1 + tp_pct)
                stop_price = entry_price * (1 - sl_pct)
                
                limit_ticket = self.LimitOrder(self.futureSymbol, -ticket.Quantity, limit_price)
                stop_ticket = self.StopMarketOrder(self.futureSymbol, -ticket.Quantity, stop_price)
            else:
                limit_price = entry_price * (1 - tp_pct)
                stop_price = entry_price * (1 + sl_pct)
                
                limit_ticket = self.LimitOrder(self.futureSymbol, -ticket.Quantity, limit_price)
                stop_ticket = self.StopMarketOrder(self.futureSymbol, -ticket.Quantity, stop_price)
            
            # Store OCO relationship
            if limit_ticket and stop_ticket:
                self.openOrders[f"limit_{ticket.OrderId}"] = limit_ticket
                self.openOrders[f"stop_{ticket.OrderId}"] = stop_ticket
                
                self.Debug(f"Enhanced targets attached: TP={limit_price:.2f}, SL={stop_price:.2f}")
                
        except Exception as e:
            self.Debug(f"Error attaching enhanced targets: {str(e)}")

    def InSessionWindow(self) -> bool:
        """Check if current time is within trading session"""
        ny_time = self.Time.ConvertFromUtc(self.ny)
        hour = ny_time.hour
        minute = ny_time.minute
        
        # NY session: 8:00 AM - 3:30 PM
        if 8 <= hour < 15:
            return True
        elif hour == 15 and minute < 30:
            return True
        
        return False

    def OnOrderEvent(self, orderEvent):
        """Enhanced order event handling with performance tracking"""
        try:
            if orderEvent.Status == OrderStatus.Filled:
                order = self.Transactions.GetOrderById(orderEvent.OrderId)
                
                if order.Type == OrderType.Market:
                    # Entry order filled
                    self.Debug(f"Entry filled: {order.Quantity} at {orderEvent.FillPrice}")
                else:
                    # Exit order filled
                    pnl = self.CalculateTradePnL(orderEvent)
                    self.pnlToday += pnl
                    
                    # Update performance tracking
                    if pnl > 0:
                        self.winningTrades += 1
                        self.winStreak += 1
                        self.lossStreak = 0
                    else:
                        self.winStreak = 0
                        self.lossStreak += 1
                    
                    # Cancel opposite OCO order
                    self.CancelOppositeOrder(orderEvent.OrderId)
                    
                    # Record trade outcome for RL system
                    try:
                        # Calculate reward based on trade outcome
                        reward = self.rl_manager.calculate_reward(
                            pnl=pnl,
                            entry_price=self.lastTradePrice or orderEvent.FillPrice,
                            exit_price=orderEvent.FillPrice,
                            position_size=abs(orderEvent.FillQuantity),
                            hold_time_minutes=1  # Simplified - would calculate actual hold time
                        )
                        
                        # Record the trade experience for RL learning
                        self.rl_manager.record_trade_outcome(
                            reward=reward,
                            final_pnl=pnl
                        )
                        
                        self.rl_trades_completed += 1
                        self.rl_total_profit += pnl
                        
                        self.Debug(f"RL Trade recorded: PnL=${pnl:.2f}, Reward={reward:.3f}, Total RL trades: {self.rl_trades_completed}")
                        
                    except Exception as rl_error:
                        self.Debug(f"Error recording RL trade outcome: {rl_error}")
                    
                    self.Debug(f"Exit filled: PnL=${pnl:.2f}, Win Rate: {self.winningTrades/self.totalTrades*100:.1f}%")
                    
        except Exception as e:
            self.Debug(f"Error in order event handling: {str(e)}")

    def CalculateTradePnL(self, orderEvent) -> float:
        """Calculate trade P&L"""
        try:
            # Simplified P&L calculation
            # In production, this would be more sophisticated
            return orderEvent.FillQuantity * (orderEvent.FillPrice - (self.lastTradePrice or orderEvent.FillPrice))
        except:
            return 0.0

    def CancelOppositeOrder(self, filled_order_id: int):
        """Cancel the opposite OCO order when one is filled"""
        try:
            orders_to_cancel = []
            for key, ticket in self.openOrders.items():
                if str(filled_order_id) in key:
                    # Find the opposite order
                    opposite_key = key.replace("limit_", "stop_") if "limit_" in key else key.replace("stop_", "limit_")
                    if opposite_key in self.openOrders:
                        opposite_ticket = self.openOrders[opposite_key]
                        if opposite_ticket.Status in [OrderStatus.Submitted, OrderStatus.PartiallyFilled]:
                            opposite_ticket.Cancel()
                        orders_to_cancel.append(opposite_key)
                    orders_to_cancel.append(key)
            
            # Clean up canceled orders
            for key in orders_to_cancel:
                if key in self.openOrders:
                    del self.openOrders[key]
                    
        except Exception as e:
            self.Debug(f"Error canceling opposite order: {str(e)}")

    def assess_risk_level_with_ml(self, confluence, sentiment_filter, ml_info):
        """Assess risk level based on multiple factors including ML predictions"""
        risk_score = 0
        
        # Confluence risk
        if confluence.get('confidence', 0) < 0.6:
            risk_score += 1
        
        # Sentiment risk
        if sentiment_filter.get('use_sentiment', False):
            if abs(sentiment_filter.get('sentiment_score', 0)) < 0.3:
                risk_score += 1
        
        # ML prediction risk
        if ml_info and ml_info.get('ml_applied', False):
            ml_pred = ml_info.get('ml_prediction', {})
            if ml_pred.get('confidence', 0) < 0.6:
                risk_score += 1
            
            # Check for conflicting signals
            entry_timing = ml_info.get('entry_timing', {})
            if entry_timing and entry_timing.get('risk_score', 0.5) > 0.7:
                risk_score += 1
        
        # Volatility risk
        if hasattr(self, 'current_volatility'):
            if self.current_volatility > 0.03:  # 3% volatility
                risk_score += 1
        
        if risk_score <= 1:
            return 'low'
        elif risk_score <= 2:
            return 'medium'
        else:
            return 'high'

    def calculate_enhanced_position_size(self, signal_strength, risk_level, current_price, ml_info=None):
        """Calculate position size based on volatility, performance, sentiment, and ML predictions"""
        try:
            base_size = self.defaultContracts
            
            # Volatility adjustment
            if hasattr(self, 'current_volatility'):
                vol_multiplier = max(0.5, min(2.0, 0.02 / max(0.01, self.current_volatility)))
                base_size *= vol_multiplier
            
            # Performance adjustment
            if hasattr(self, 'pnlToday'):
                if self.pnlToday > 0:
                    base_size *= 1.1  # Increase size when winning
                elif self.pnlToday < -self.dailyMaxDD * 0.5:
                    base_size *= 0.7  # Reduce size when losing
            
            # Signal strength adjustment
            strength_multiplier = max(0.5, min(1.5, signal_strength))
            base_size *= strength_multiplier
            
            # ML confidence adjustment
            if ml_info and ml_info.get('ml_applied', False):
                ml_pred = ml_info.get('ml_prediction', {})
                ml_confidence = ml_pred.get('confidence', 0.5)
                
                # Boost size for high-confidence ML predictions
                if ml_confidence > 0.8:
                    base_size *= 1.15
                elif ml_confidence < 0.5:
                    base_size *= 0.85
                
                # Consider predicted move magnitude
                entry_timing = ml_info.get('entry_timing', {})
                if entry_timing:
                    predicted_move = abs(entry_timing.get('predicted_move', 0))
                    if predicted_move > 0.01:  # > 1% expected move
                        base_size *= min(1.3, 1 + predicted_move * 10)
            
            # Risk level adjustment
            risk_multipliers = {'low': 1.2, 'medium': 1.0, 'high': 0.6}
            base_size *= risk_multipliers.get(risk_level, 1.0)
            
            # Kelly Criterion approximation (simplified)
            if hasattr(self, 'winningTrades') and hasattr(self, 'totalTrades') and self.totalTrades > 10:
                win_rate = self.winningTrades / self.totalTrades
                if win_rate > 0.5:  # Only apply Kelly when winning
                    kelly_fraction = min(0.25, (2 * win_rate - 1) * 0.5)  # Simplified Kelly
                    base_size *= (1 + kelly_fraction)
            
            # Ensure minimum and maximum bounds
            final_size = max(1, min(self.maxContracts, int(base_size)))
            
            return final_size
            
        except Exception as e:
            self.Debug(f"Error calculating enhanced position size: {e}")
            return self.defaultContracts
    
    def GetAdvancedTechnicalSignal(self) -> float:
        """Get signal from advanced technical indicators"""
        try:
            if not self.technical_signal_summary:
                return 0.0
                
            signal_strength = 0.0
            
            # RSI Divergence signals
            rsi_div = self.technical_signal_summary.rsi_divergence
            if rsi_div and rsi_div.type != 'none':
                if rsi_div.type == 'bullish':
                    signal_strength += 0.4 * rsi_div.strength
                elif rsi_div.type == 'bearish':
                    signal_strength -= 0.4 * rsi_div.strength
                self.rsi_divergence_trades += 1
            
            # MACD Analysis signals
            macd_analysis = self.technical_signal_summary.macd_analysis
            if macd_analysis:
                macd_signal = 0.0
                if macd_analysis.signal_cross == 'bullish':
                    macd_signal += 0.5
                elif macd_analysis.signal_cross == 'bearish':
                    macd_signal -= 0.5
                
                if macd_analysis.zero_line_cross == 'bullish':
                    macd_signal += 0.3
                elif macd_analysis.zero_line_cross == 'bearish':
                    macd_signal -= 0.3
                
                if abs(macd_signal) > 0.2:
                    signal_strength += 0.3 * macd_signal
                    self.macd_signal_trades += 1
            
            # Ichimoku signals
            ichimoku = self.technical_signal_summary.ichimoku_analysis
            if ichimoku and ichimoku.overall_bias != 'neutral':
                if ichimoku.overall_bias == 'bullish':
                    signal_strength += 0.3 * ichimoku.strength
                elif ichimoku.overall_bias == 'bearish':
                    signal_strength -= 0.3 * ichimoku.strength
                self.ichimoku_trades += 1
            
            # High confidence technical signal tracking
            if abs(signal_strength) > 0.7:
                self.high_confidence_tech_trades += 1
            
            return max(-1.0, min(1.0, signal_strength))
            
        except Exception as e:
            self.Debug(f"❌ Error getting advanced technical signal: {e}")
            return 0.0
    
    def ScheduledMLRetrain(self):
         """Scheduled ML model retraining"""
         try:
             if self.use_ml_predictions and self.should_retrain_ml_models():
                 self.Debug("🔄 Starting scheduled ML model retraining...")
                 self.retrain_ml_models(self.futureSymbol)
                 
                 # Update performance tracking
                 if not hasattr(self, 'ml_retrain_count'):
                     self.ml_retrain_count = 0
                 self.ml_retrain_count += 1
                 
                 self.Debug(f"✅ Completed ML retraining #{self.ml_retrain_count}")
             else:
                 self.Debug("ℹ️ ML retraining not needed at this time")
                 
         except Exception as e:
             self.Debug(f"❌ Scheduled ML retraining failed: {e}")
 
     def OnEndOfAlgorithm(self):
        """Generate comprehensive final summary with enhanced metrics and risk analysis"""
        try:
            total_trades = len(self.tradeLog)
            if total_trades == 0:
                self.Debug("📊 No trades executed during backtest period")
                return
            
            # Calculate basic performance metrics
            winning_trades = [t for t in self.tradeLog if t.get('pnl', 0) > 0]
            losing_trades = [t for t in self.tradeLog if t.get('pnl', 0) < 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            total_pnl = sum(t.get('pnl', 0) for t in self.tradeLog)
            avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
            profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades and avg_loss != 0 else float('inf')
            
            # Enhanced metrics with sentiment and ML analysis
            sentiment_trades = [t for t in self.tradeLog if t.get('sentiment_applied', False)]
            ml_trades = [t for t in self.tradeLog if t.get('ml_applied', False)]
            high_confidence_ml_trades = [t for t in ml_trades if t.get('ml_confidence', 0) > 0.7]
            risk_adjusted_trades = [t for t in self.tradeLog if t.get('risk_adjusted', False)]
            
            # Multi-timeframe analysis metrics
            mtf_trades = [t for t in self.tradeLog if t.get('mtf_confluence', 0) >= 2]
            
            # Calculate average confidence scores
            avg_ml_confidence = sum(t.get('ml_confidence', 0) for t in ml_trades) / len(ml_trades) if ml_trades else 0
            avg_sentiment_score = sum(t.get('sentiment_score', 0) for t in sentiment_trades) / len(sentiment_trades) if sentiment_trades else 0
            
            # Performance by enhancement type
            ml_pnl = sum(t.get('pnl', 0) for t in ml_trades)
            sentiment_pnl = sum(t.get('pnl', 0) for t in sentiment_trades)
            mtf_pnl = sum(t.get('pnl', 0) for t in mtf_trades)
            risk_adjusted_pnl = sum(t.get('pnl', 0) for t in risk_adjusted_trades)
            
            # Risk Management Analysis
            risk_summary = self.risk_manager.get_current_risk_summary()
            avg_portfolio_var = sum(t.get('portfolio_var', 0) for t in self.tradeLog) / total_trades if total_trades > 0 else 0
            
            # Dynamic stop-loss analysis
            avg_stop_multiplier = sum(t.get('stop_multiplier', 2.0) for t in self.tradeLog) / total_trades if total_trades > 0 else 2.0
            avg_profit_multiplier = sum(t.get('profit_multiplier', 3.0) for t in self.tradeLog) / total_trades if total_trades > 0 else 3.0
            
            # Generate comprehensive summary
            self.Debug("\n" + "="*80)
            self.Debug("📊 TESLA 3-6-9 GOLD ENHANCED STRATEGY - FINAL PERFORMANCE SUMMARY")
            self.Debug("="*80)
            
            # Basic Performance
            self.Debug(f"📈 BASIC PERFORMANCE:")
            self.Debug(f"   Total Trades: {total_trades}")
            self.Debug(f"   Win Rate: {win_rate:.2%} ({len(winning_trades)}W / {len(losing_trades)}L)")
            self.Debug(f"   Total P&L: ${total_pnl:,.2f}")
            self.Debug(f"   Average Win: ${avg_win:,.2f}")
            self.Debug(f"   Average Loss: ${avg_loss:,.2f}")
            self.Debug(f"   Profit Factor: {profit_factor:.2f}")
            
            # Enhanced Features Performance
            self.Debug(f"\n🤖 ENHANCED FEATURES PERFORMANCE:")
            self.Debug(f"   ML-Enhanced Trades: {len(ml_trades)} ({len(ml_trades)/total_trades:.1%})")
            self.Debug(f"   ML Average Confidence: {avg_ml_confidence:.2%}")
            self.Debug(f"   High-Confidence ML Trades: {len(high_confidence_ml_trades)}")
            self.Debug(f"   ML-Enhanced P&L: ${ml_pnl:,.2f}")
            
            self.Debug(f"\n💭 SENTIMENT ANALYSIS:")
            self.Debug(f"   Sentiment-Filtered Trades: {len(sentiment_trades)} ({len(sentiment_trades)/total_trades:.1%})")
            self.Debug(f"   Average Sentiment Score: {avg_sentiment_score:.2f}")
            self.Debug(f"   Sentiment-Enhanced P&L: ${sentiment_pnl:,.2f}")
            
            self.Debug(f"\n⏰ MULTI-TIMEFRAME ANALYSIS:")
            self.Debug(f"   Multi-Timeframe Confluence Trades: {len(mtf_trades)} ({len(mtf_trades)/total_trades:.1%})")
            self.Debug(f"   MTF-Enhanced P&L: ${mtf_pnl:,.2f}")
            
            # Advanced Risk Management Analysis
            self.Debug(f"\n🛡️ ADVANCED RISK MANAGEMENT:")
            self.Debug(f"   Risk-Adjusted Trades: {len(risk_adjusted_trades)} ({len(risk_adjusted_trades)/total_trades:.1%})")
            self.Debug(f"   Risk-Adjusted P&L: ${risk_adjusted_pnl:,.2f}")
            self.Debug(f"   Average Portfolio VaR: {avg_portfolio_var:.2%}")
            self.Debug(f"   Current Risk Score: {risk_summary.get('risk_score', 0):.2f}/1.0")
            self.Debug(f"   Average Stop Multiplier: {avg_stop_multiplier:.1f}x ATR")
            self.Debug(f"   Average Profit Multiplier: {avg_profit_multiplier:.1f}x ATR")
            
            if 'volatility' in risk_summary:
                self.Debug(f"   Portfolio Volatility: {risk_summary['volatility']:.2%}")
            if 'sharpe_ratio' in risk_summary:
                self.Debug(f"   Sharpe Ratio: {risk_summary['sharpe_ratio']:.2f}")
            if 'max_drawdown' in risk_summary:
                self.Debug(f"   Maximum Drawdown: {risk_summary['max_drawdown']:.2%}")
            
            # Risk Alerts Summary
            active_alerts = risk_summary.get('active_alerts', 0)
            if active_alerts > 0:
                self.Debug(f"   ⚠️ Active Risk Alerts: {active_alerts}")
            
            # Advanced Technical Indicators Metrics
            self.Debug(f"\n🔧 ADVANCED TECHNICAL INDICATORS:")
            self.Debug(f"   RSI Divergence Trades: {self.rsi_divergence_trades}")
            self.Debug(f"   MACD Signal Trades: {self.macd_signal_trades}")
            self.Debug(f"   Ichimoku Trades: {self.ichimoku_trades}")
            self.Debug(f"   High Confidence Tech Trades: {self.high_confidence_tech_trades}")
            
            if self.technical_signal_summary:
                self.Debug(f"   Current ATR Volatility Regime: {self.technical_signal_summary.atr_filter.volatility_regime}")
                self.Debug(f"   Current Technical Signal: {self.technical_signal_summary.combined_signal:.2f}")
                self.Debug(f"   Technical Confidence: {self.technical_signal_summary.confidence:.2%}")
            
            # Smart Exit Strategies Metrics
            self.Debug(f"\n🎯 SMART EXIT STRATEGIES:")
            self.Debug(f"   Trailing Stop Exits: {self.trailing_stop_trades}")
            self.Debug(f"   Partial Profit Exits: {self.partial_profit_trades}")
            self.Debug(f"   Time-Based Exits: {self.time_based_exit_trades}")
            self.Debug(f"   Smart Exit Profit: ${self.smart_exit_profit:,.2f}")
            
            if hasattr(self, 'exit_manager') and self.exit_manager:
                exit_stats = self.exit_manager.get_exit_statistics()
                self.Debug(f"   Total Exit Signals: {exit_stats.get('total_exits', 0)}")
                self.Debug(f"   Average Exit Profit: ${exit_stats.get('avg_exit_profit', 0):,.2f}")
                self.Debug(f"   Best Exit Profit: ${exit_stats.get('best_exit_profit', 0):,.2f}")
                
                # Current position status
                position_status = self.exit_manager.get_position_status(str(self.futureSymbol))
                if position_status:
                    self.Debug(f"   Current Position Trailing Stop: ${position_status.get('trailing_stop_price', 0):.2f}")
                    self.Debug(f"   Next Partial Profit Level: ${position_status.get('next_partial_level', 0):.2f}")
            
            # Reinforcement Learning Metrics
            self.Debug(f"\n🤖 REINFORCEMENT LEARNING:")
            self.Debug(f"   RL Recommendations Used: {self.rl_recommendations_used}")
            self.Debug(f"   RL Trades Completed: {self.rl_trades_completed}")
            self.Debug(f"   RL Total Profit: ${self.rl_total_profit:,.2f}")
            
            if hasattr(self, 'rl_manager') and self.rl_manager:
                rl_stats = self.rl_manager.get_learning_statistics()
                self.Debug(f"   Q-Table Size: {rl_stats.get('q_table_size', 0)}")
                self.Debug(f"   Total Experiences: {rl_stats.get('total_experiences', 0)}")
                self.Debug(f"   Current Epsilon: {rl_stats.get('current_epsilon', 0):.3f}")
                self.Debug(f"   Average Q-Value: {rl_stats.get('avg_q_value', 0):.3f}")
                self.Debug(f"   Learning Rate: {rl_stats.get('learning_rate', 0):.3f}")
                
                # RL Performance metrics
                if self.rl_trades_completed > 0:
                    rl_avg_profit = self.rl_total_profit / self.rl_trades_completed
                    rl_win_rate = rl_stats.get('win_rate', 0)
                    self.Debug(f"   RL Average Profit per Trade: ${rl_avg_profit:,.2f}")
                    self.Debug(f"   RL Win Rate: {rl_win_rate:.1%}")
                    
                # Model persistence info
                model_info = rl_stats.get('model_info', {})
                if model_info:
                    self.Debug(f"   Model Last Updated: {model_info.get('last_update', 'Never')}")
                    self.Debug(f"   Model Version: {model_info.get('version', 'N/A')}")
                    self.Debug(f"   Model Performance Score: {model_info.get('performance_score', 0):.3f}")
            
            # Session Analysis
            london_trades = [t for t in self.tradeLog if 'London' in t.get('session', '')]
            ny_trades = [t for t in self.tradeLog if 'NY' in t.get('session', '')]
            
            self.Debug(f"\n🌍 SESSION ANALYSIS:")
            self.Debug(f"   London Session: {len(london_trades)} trades, P&L: ${sum(t.get('pnl', 0) for t in london_trades):,.2f}")
            self.Debug(f"   NY Session: {len(ny_trades)} trades, P&L: ${sum(t.get('pnl', 0) for t in ny_trades):,.2f}")
            
            # Risk Metrics
            if hasattr(self, 'maxDailyDrawdown') and self.maxDailyDrawdown > 0:
                self.Debug(f"\n⚠️ DAILY RISK LIMITS:")
                self.Debug(f"   Maximum Daily Drawdown: ${self.maxDailyDrawdown:,.2f}")
                self.Debug(f"   Daily Profit Target: ${self.dailyProfitTarget:,.2f}")
                self.Debug(f"   Max Trades Per Day: {self.maxTradesPerDay}")
            
            # ML Model Performance (if available)
            if hasattr(self, 'ml_retrain_count') and self.ml_retrain_count > 0:
                self.Debug(f"\n🧠 ML MODEL PERFORMANCE:")
                self.Debug(f"   Model Retrains: {self.ml_retrain_count}")
                self.Debug(f"   Last Retrain: {getattr(self, 'last_retrain_time', 'N/A')}")
            
            self.Debug("="*80)
            
        except Exception as e:
            self.Debug(f"Error generating final summary: {e}")