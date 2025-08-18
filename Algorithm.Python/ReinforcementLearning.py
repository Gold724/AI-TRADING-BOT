from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta

@dataclass
class QState:
    """Represents a state in the Q-learning environment"""
    rsi_level: str  # 'oversold', 'neutral', 'overbought'
    macd_signal: str  # 'bullish', 'neutral', 'bearish'
    volatility_regime: str  # 'low', 'medium', 'high'
    session: str  # 'london', 'overlap', 'ny', 'other'
    sentiment: str  # 'positive', 'neutral', 'negative'
    trend: str  # 'uptrend', 'sideways', 'downtrend'
    volume_profile: str  # 'high', 'normal', 'low'
    
    def to_key(self) -> str:
        """Convert state to string key for Q-table"""
        return f"{self.rsi_level}_{self.macd_signal}_{self.volatility_regime}_{self.session}_{self.sentiment}_{self.trend}_{self.volume_profile}"

@dataclass
class QAction:
    """Represents an action in the Q-learning environment"""
    action_type: str  # 'buy', 'sell', 'hold'
    position_size: str  # 'small', 'medium', 'large'
    stop_loss_mult: str  # 'tight', 'normal', 'wide'
    take_profit_mult: str  # 'conservative', 'normal', 'aggressive'
    
    def to_key(self) -> str:
        """Convert action to string key for Q-table"""
        return f"{self.action_type}_{self.position_size}_{self.stop_loss_mult}_{self.take_profit_mult}"

@dataclass
class QExperience:
    """Represents an experience tuple for Q-learning"""
    state: QState
    action: QAction
    reward: float
    next_state: QState
    done: bool
    timestamp: datetime

@dataclass
class QLearningConfig:
    """Configuration for Q-learning parameters"""
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon: float = 0.1  # Exploration rate
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    memory_size: int = 10000
    batch_size: int = 32
    update_frequency: int = 100  # Update Q-table every N experiences
    reward_lookback_hours: int = 24  # Hours to look back for reward calculation

class QLearningAgent:
    """Q-Learning agent for trading strategy optimization"""
    
    def __init__(self, config: QLearningConfig):
        self.config = config
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.experience_buffer: deque = deque(maxlen=config.memory_size)
        self.state_action_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Performance tracking
        self.total_rewards = 0.0
        self.episode_rewards: List[float] = []
        self.learning_steps = 0
        self.exploration_steps = 0
        self.exploitation_steps = 0
        
        # Action spaces
        self.action_types = ['buy', 'sell', 'hold']
        self.position_sizes = ['small', 'medium', 'large']
        self.stop_loss_mults = ['tight', 'normal', 'wide']
        self.take_profit_mults = ['conservative', 'normal', 'aggressive']
        
        # State discretization thresholds
        self.rsi_thresholds = {'oversold': 30, 'overbought': 70}
        self.volatility_thresholds = {'low': 0.01, 'high': 0.03}
        
    def discretize_state(self, market_data: Dict[str, Any]) -> QState:
        """Convert continuous market data to discrete state"""
        # RSI level
        rsi = market_data.get('rsi', 50)
        if rsi < self.rsi_thresholds['oversold']:
            rsi_level = 'oversold'
        elif rsi > self.rsi_thresholds['overbought']:
            rsi_level = 'overbought'
        else:
            rsi_level = 'neutral'
        
        # MACD signal
        macd = market_data.get('macd', 0)
        macd_signal = market_data.get('macd_signal', 0)
        if macd > macd_signal:
            macd_signal_state = 'bullish'
        elif macd < macd_signal:
            macd_signal_state = 'bearish'
        else:
            macd_signal_state = 'neutral'
        
        # Volatility regime
        volatility = market_data.get('volatility', 0.02)
        if volatility < self.volatility_thresholds['low']:
            volatility_regime = 'low'
        elif volatility > self.volatility_thresholds['high']:
            volatility_regime = 'high'
        else:
            volatility_regime = 'medium'
        
        # Session
        session = market_data.get('session', 'other')
        
        # Sentiment
        sentiment_score = market_data.get('sentiment_score', 0)
        if sentiment_score > 0.1:
            sentiment = 'positive'
        elif sentiment_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Trend
        ema_20 = market_data.get('ema_20', 0)
        ema_50 = market_data.get('ema_50', 0)
        current_price = market_data.get('price', 0)
        
        if current_price > ema_20 > ema_50:
            trend = 'uptrend'
        elif current_price < ema_20 < ema_50:
            trend = 'downtrend'
        else:
            trend = 'sideways'
        
        # Volume profile
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            volume_profile = 'high'
        elif volume_ratio < 0.7:
            volume_profile = 'low'
        else:
            volume_profile = 'normal'
        
        return QState(
            rsi_level=rsi_level,
            macd_signal=macd_signal_state,
            volatility_regime=volatility_regime,
            session=session,
            sentiment=sentiment,
            trend=trend,
            volume_profile=volume_profile
        )
    
    def get_action(self, state: QState, exploration: bool = True) -> QAction:
        """Get action using epsilon-greedy policy"""
        state_key = state.to_key()
        
        # Exploration vs exploitation
        if exploration and np.random.random() < self.config.epsilon:
            # Random action (exploration)
            action = QAction(
                action_type=np.random.choice(self.action_types),
                position_size=np.random.choice(self.position_sizes),
                stop_loss_mult=np.random.choice(self.stop_loss_mults),
                take_profit_mult=np.random.choice(self.take_profit_mults)
            )
            self.exploration_steps += 1
        else:
            # Best action based on Q-values (exploitation)
            action = self._get_best_action(state_key)
            self.exploitation_steps += 1
        
        # Update state-action counts
        action_key = action.to_key()
        self.state_action_counts[state_key][action_key] += 1
        
        return action
    
    def _get_best_action(self, state_key: str) -> QAction:
        """Get the action with highest Q-value for given state"""
        if state_key not in self.q_table or not self.q_table[state_key]:
            # If no Q-values exist, return random action
            return QAction(
                action_type=np.random.choice(self.action_types),
                position_size=np.random.choice(self.position_sizes),
                stop_loss_mult=np.random.choice(self.stop_loss_mults),
                take_profit_mult=np.random.choice(self.take_profit_mults)
            )
        
        # Find action with maximum Q-value
        best_action_key = max(self.q_table[state_key], key=self.q_table[state_key].get)
        
        # Parse action key back to QAction
        parts = best_action_key.split('_')
        return QAction(
            action_type=parts[0],
            position_size=parts[1],
            stop_loss_mult=parts[2],
            take_profit_mult=parts[3]
        )
    
    def add_experience(self, experience: QExperience):
        """Add experience to replay buffer"""
        self.experience_buffer.append(experience)
        self.total_rewards += experience.reward
        
        # Update Q-table if enough experiences
        if len(self.experience_buffer) >= self.config.batch_size and \
           len(self.experience_buffer) % self.config.update_frequency == 0:
            self._update_q_table()
    
    def _update_q_table(self):
        """Update Q-table using batch of experiences"""
        # Sample batch from experience buffer
        batch_size = min(self.config.batch_size, len(self.experience_buffer))
        batch_indices = np.random.choice(len(self.experience_buffer), batch_size, replace=False)
        batch = [self.experience_buffer[i] for i in batch_indices]
        
        for experience in batch:
            state_key = experience.state.to_key()
            action_key = experience.action.to_key()
            next_state_key = experience.next_state.to_key()
            
            # Current Q-value
            current_q = self.q_table[state_key][action_key]
            
            # Calculate target Q-value
            if experience.done:
                target_q = experience.reward
            else:
                # Find maximum Q-value for next state
                next_state_q_values = self.q_table[next_state_key]
                max_next_q = max(next_state_q_values.values()) if next_state_q_values else 0
                target_q = experience.reward + self.config.discount_factor * max_next_q
            
            # Update Q-value using learning rate
            self.q_table[state_key][action_key] = current_q + self.config.learning_rate * (target_q - current_q)
        
        # Decay epsilon
        self.config.epsilon = max(self.config.epsilon_min, self.config.epsilon * self.config.epsilon_decay)
        self.learning_steps += 1
    
    def calculate_reward(self, trade_result: Dict[str, Any]) -> float:
        """Calculate reward based on trade outcome"""
        pnl = trade_result.get('pnl', 0)
        duration_hours = trade_result.get('duration_hours', 1)
        max_drawdown = trade_result.get('max_drawdown', 0)
        
        # Base reward from P&L
        reward = pnl / 100.0  # Normalize by typical profit target
        
        # Penalty for long duration trades
        if duration_hours > 4:
            reward *= 0.9
        
        # Penalty for high drawdown
        if max_drawdown > 0.02:  # 2% drawdown
            reward *= 0.8
        
        # Bonus for quick profitable trades
        if pnl > 0 and duration_hours < 2:
            reward *= 1.2
        
        return reward
    
    def get_adaptive_parameters(self, state: QState) -> Dict[str, float]:
        """Get adaptive trading parameters based on learned Q-values"""
        state_key = state.to_key()
        
        if state_key not in self.q_table or not self.q_table[state_key]:
            # Return default parameters if no learning data
            return {
                'position_size_multiplier': 1.0,
                'stop_loss_multiplier': 2.0,
                'take_profit_multiplier': 3.0,
                'confidence': 0.5
            }
        
        # Get best action for current state
        best_action = self._get_best_action(state_key)
        best_q_value = self.q_table[state_key][best_action.to_key()]
        
        # Convert action to parameters
        size_mult = {'small': 0.5, 'medium': 1.0, 'large': 1.5}[best_action.position_size]
        sl_mult = {'tight': 1.5, 'normal': 2.0, 'wide': 3.0}[best_action.stop_loss_mult]
        tp_mult = {'conservative': 2.0, 'normal': 3.0, 'aggressive': 4.0}[best_action.take_profit_mult]
        
        # Confidence based on Q-value and visit count
        visit_count = self.state_action_counts[state_key][best_action.to_key()]
        confidence = min(1.0, (abs(best_q_value) + visit_count / 100.0) / 2.0)
        
        return {
            'position_size_multiplier': size_mult,
            'stop_loss_multiplier': sl_mult,
            'take_profit_multiplier': tp_mult,
            'confidence': confidence,
            'recommended_action': best_action.action_type
        }
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning performance statistics"""
        total_steps = self.exploration_steps + self.exploitation_steps
        exploration_rate = self.exploration_steps / total_steps if total_steps > 0 else 0
        
        return {
            'total_experiences': len(self.experience_buffer),
            'learning_steps': self.learning_steps,
            'exploration_steps': self.exploration_steps,
            'exploitation_steps': self.exploitation_steps,
            'exploration_rate': exploration_rate,
            'current_epsilon': self.config.epsilon,
            'total_rewards': self.total_rewards,
            'average_reward': self.total_rewards / len(self.experience_buffer) if self.experience_buffer else 0,
            'q_table_size': len(self.q_table),
            'unique_states': len(self.q_table),
            'total_state_actions': sum(len(actions) for actions in self.q_table.values())
        }
    
    def save_model(self, filepath: str):
        """Save Q-table and learning statistics to file"""
        model_data = {
            'q_table': {state: dict(actions) for state, actions in self.q_table.items()},
            'config': {
                'learning_rate': self.config.learning_rate,
                'discount_factor': self.config.discount_factor,
                'epsilon': self.config.epsilon,
                'epsilon_decay': self.config.epsilon_decay,
                'epsilon_min': self.config.epsilon_min
            },
            'statistics': self.get_learning_statistics(),
            'state_action_counts': {state: dict(actions) for state, actions in self.state_action_counts.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self, filepath: str):
        """Load Q-table and learning statistics from file"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            # Load Q-table
            self.q_table = defaultdict(lambda: defaultdict(float))
            for state, actions in model_data.get('q_table', {}).items():
                for action, q_value in actions.items():
                    self.q_table[state][action] = q_value
            
            # Load state-action counts
            self.state_action_counts = defaultdict(lambda: defaultdict(int))
            for state, actions in model_data.get('state_action_counts', {}).items():
                for action, count in actions.items():
                    self.state_action_counts[state][action] = count
            
            # Load config
            config_data = model_data.get('config', {})
            self.config.epsilon = config_data.get('epsilon', self.config.epsilon)
            
            # Load statistics
            stats = model_data.get('statistics', {})
            self.total_rewards = stats.get('total_rewards', 0)
            self.learning_steps = stats.get('learning_steps', 0)
            self.exploration_steps = stats.get('exploration_steps', 0)
            self.exploitation_steps = stats.get('exploitation_steps', 0)
            
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

class ReinforcementLearningManager:
    """Manager class for integrating RL with trading strategy"""
    
    def __init__(self, algorithm, config: Optional[QLearningConfig] = None):
        self.algorithm = algorithm
        self.config = config or QLearningConfig()
        self.agent = QLearningAgent(self.config)
        
        # Trade tracking
        self.active_trades: Dict[str, Dict] = {}
        self.completed_trades: List[Dict] = []
        
        # Performance tracking
        self.rl_trades = 0
        self.rl_profit = 0.0
        self.last_state: Optional[QState] = None
        self.last_action: Optional[QAction] = None
        
        # Model persistence
        self.model_save_frequency = 100  # Save every N trades
        self.model_filepath = "q_learning_model.json"
        
        # Load existing model if available
        self.agent.load_model(self.model_filepath)
    
    def get_rl_recommendation(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get RL-based trading recommendation"""
        try:
            # Discretize current market state
            current_state = self.agent.discretize_state(market_data)
            
            # Get recommended action
            recommended_action = self.agent.get_action(current_state, exploration=True)
            
            # Get adaptive parameters
            adaptive_params = self.agent.get_adaptive_parameters(current_state)
            
            # Store state and action for experience creation
            self.last_state = current_state
            self.last_action = recommended_action
            
            return {
                'recommended_action': adaptive_params['recommended_action'],
                'position_size_multiplier': adaptive_params['position_size_multiplier'],
                'stop_loss_multiplier': adaptive_params['stop_loss_multiplier'],
                'take_profit_multiplier': adaptive_params['take_profit_multiplier'],
                'confidence': adaptive_params['confidence'],
                'rl_applied': True,
                'state': current_state.to_key(),
                'action': recommended_action.to_key()
            }
            
        except Exception as e:
            self.algorithm.Debug(f"Error in RL recommendation: {str(e)}")
            return {
                'recommended_action': 'hold',
                'position_size_multiplier': 1.0,
                'stop_loss_multiplier': 2.0,
                'take_profit_multiplier': 3.0,
                'confidence': 0.5,
                'rl_applied': False
            }
    
    def record_trade_start(self, trade_id: str, entry_data: Dict[str, Any]):
        """Record the start of a trade for RL tracking"""
        self.active_trades[trade_id] = {
            'entry_time': entry_data.get('timestamp'),
            'entry_price': entry_data.get('price'),
            'position_size': entry_data.get('position_size'),
            'direction': entry_data.get('direction'),
            'state': self.last_state,
            'action': self.last_action,
            'max_profit': 0.0,
            'max_drawdown': 0.0
        }
    
    def update_trade_progress(self, trade_id: str, current_price: float):
        """Update trade progress for drawdown/profit tracking"""
        if trade_id not in self.active_trades:
            return
        
        trade = self.active_trades[trade_id]
        entry_price = trade['entry_price']
        direction = trade['direction']
        
        if direction.lower() == 'buy':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        trade['max_profit'] = max(trade['max_profit'], pnl_pct)
        trade['max_drawdown'] = min(trade['max_drawdown'], pnl_pct)
    
    def record_trade_end(self, trade_id: str, exit_data: Dict[str, Any]):
        """Record the end of a trade and create RL experience"""
        if trade_id not in self.active_trades:
            return
        
        trade = self.active_trades[trade_id]
        
        # Calculate trade metrics
        entry_time = trade['entry_time']
        exit_time = exit_data.get('timestamp')
        duration = (exit_time - entry_time).total_seconds() / 3600  # Hours
        
        pnl = exit_data.get('pnl', 0)
        
        trade_result = {
            'pnl': pnl,
            'duration_hours': duration,
            'max_drawdown': abs(trade['max_drawdown']),
            'max_profit': trade['max_profit']
        }
        
        # Calculate reward
        reward = self.agent.calculate_reward(trade_result)
        
        # Create experience if we have state and action
        if trade['state'] and trade['action']:
            # Get current state for next_state
            current_market_data = self._get_current_market_data()
            next_state = self.agent.discretize_state(current_market_data)
            
            experience = QExperience(
                state=trade['state'],
                action=trade['action'],
                reward=reward,
                next_state=next_state,
                done=True,
                timestamp=exit_time
            )
            
            self.agent.add_experience(experience)
        
        # Update tracking
        self.rl_trades += 1
        self.rl_profit += pnl
        
        # Move to completed trades
        trade.update(trade_result)
        trade['reward'] = reward
        self.completed_trades.append(trade)
        del self.active_trades[trade_id]
        
        # Save model periodically
        if self.rl_trades % self.model_save_frequency == 0:
            self.agent.save_model(self.model_filepath)
            self.algorithm.Debug(f"🧠 RL Model saved after {self.rl_trades} trades")
    
    def _get_current_market_data(self) -> Dict[str, Any]:
        """Get current market data for state creation"""
        try:
            return {
                'rsi': self.algorithm.rsi.Current.Value if self.algorithm.rsi.IsReady else 50,
                'macd': self.algorithm.macd.Current.Value if self.algorithm.macd.IsReady else 0,
                'macd_signal': self.algorithm.macd.Signal.Current.Value if self.algorithm.macd.IsReady else 0,
                'volatility': self.algorithm.atr.Current.Value / self.algorithm.Securities[self.algorithm.futureSymbol].Price if self.algorithm.atr.IsReady else 0.02,
                'session': self.algorithm.GetCurrentSession() if hasattr(self.algorithm, 'GetCurrentSession') else 'other',
                'sentiment_score': self.algorithm.sentimentHistory[0].sentiment_score if self.algorithm.sentimentHistory.Count > 0 else 0,
                'ema_20': self.algorithm.ema20.Current.Value if self.algorithm.ema20.IsReady else 0,
                'ema_50': self.algorithm.ema50.Current.Value if self.algorithm.ema50.IsReady else 0,
                'price': self.algorithm.Securities[self.algorithm.futureSymbol].Price,
                'volume_ratio': self.algorithm.volAvg.Current.Value / self.algorithm.volAvg.Samples if self.algorithm.volAvg.IsReady and self.algorithm.volAvg.Samples > 0 else 1.0
            }
        except Exception as e:
            self.algorithm.Debug(f"Error getting market data: {str(e)}")
            return {}
    
    def get_rl_statistics(self) -> Dict[str, Any]:
        """Get RL performance statistics"""
        learning_stats = self.agent.get_learning_statistics()
        
        return {
            'rl_trades': self.rl_trades,
            'rl_profit': self.rl_profit,
            'avg_rl_profit': self.rl_profit / self.rl_trades if self.rl_trades > 0 else 0,
            'active_trades': len(self.active_trades),
            'completed_trades': len(self.completed_trades),
            'learning_statistics': learning_stats
        }