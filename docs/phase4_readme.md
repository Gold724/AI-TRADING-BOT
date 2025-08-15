# TRAE Phase 4: Reinforcement Learning & Market Regime Awareness

This document provides an overview of Phase 4 implementation, which introduces reinforcement learning and market regime detection capabilities to the TRAE system.

## Overview

Phase 4 enhances TRAE with:

1. **Market Regime Detection** - Automatically identifies bullish, bearish, and sideways market conditions
2. **Reinforcement Learning** - Learns from trade outcomes to optimize strategy selection
3. **Contextual Trading** - Adapts strategies based on current market regime

## Components

### ReinforcementAgent

The core component is the `ReinforcementAgent` class in `reinforcement_agent.py`, which provides:

- Market regime detection using EMA crossovers and ATR analysis
- Q-learning based reinforcement learning for strategy optimization
- Strategy recommendations based on current market conditions
- Performance tracking and feedback loops

### Configuration

Settings are stored in `reinforcement_config.json` with these key parameters:

- Learning rates and exploration parameters
- Reward and penalty thresholds
- EMA and ATR periods for regime detection
- Strategy mappings for different market regimes

### Integration with SentinelDecider

The `SentinelDecider` class has been updated to:

- Initialize a reinforcement agent when enabled
- Update market regime during decision making
- Apply reinforcement learning adjustments to trade confidence
- Record trade results for learning

## Usage

### Enabling Features

Features can be enabled through the phase-4.md prompt with these parameters:

```yaml
parameters:
  regime_awareness: true
  reinforcement_learning: true
  reward_threshold: +1.2 profit factor
  penalty_threshold: -0.8 profit factor
```

### Market Regime Rules

The system classifies market regimes as:

- **Bullish:** 50 EMA above 200 EMA + rising ATR
- **Bearish:** 50 EMA below 200 EMA + rising ATR
- **Sideways:** ATR below threshold, EMAs close

### Strategy Adaptation

Strategies are automatically adjusted based on the detected regime:

- **Bull Markets:** Breakout and momentum strategies
- **Bear Markets:** Pullback and mean reversion strategies
- **Sideways Markets:** Scalping and high RRR micro-trades

## Monitoring

The system generates these logs for monitoring:

- `/logs/market_regime.log` - Records regime changes
- `/logs/rl_agent_decisions.json` - Tracks reinforcement learning decisions
- `/data/regime_labels.json` - Stores historical regime labels

## Testing

Use `test_reinforcement.py` to verify:

- Market regime detection accuracy
- Reinforcement learning functionality
- Integration with the SentinelDecider

## Success Metrics

Phase 4 completion is measured by:

- Regime detection accuracy > 75%
- Adaptive switch latency < 5 minutes
- At least 2 strategies optimized per week
- System win rate above 60%
- Drawdown < 5% on regime switches