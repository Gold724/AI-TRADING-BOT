# TRAE Phase 4: Reinforcement Learning & Market Regime Awareness

## Goals

- Integrate a simple reinforcement learning model for strategy feedback
- Detect and adapt to market regimes (bull, bear, range)
- Adjust strategy mix dynamically based on regime
- Reward/punish strategies based on performance in each regime

## System Instructions

### Sentinel Decider Activation

```
trigger: sentinel_decider.py
mode: adaptive
parameters:
  regime_awareness: true
  reinforcement_learning: true
  reward_threshold: +1.2 profit factor
  penalty_threshold: -0.8 profit factor
```

## Market Regime Detection

- Use 50/200 EMA cross and ATR thresholds to classify regimes:
  - **Bullish:** 50 EMA above 200 EMA + rising ATR
  - **Bearish:** 50 EMA below 200 EMA + rising ATR
  - **Sideways:** ATR below threshold, EMAs close

- Regime reevaluation interval: every 2 hours

- Log regime changes in `/logs/market_regime.log`

## Reinforcement Learning Rewards

- **Reward signal:** Profit Factor > 1.2 for 20 trades
- **Penalty signal:** Profit Factor < 0.8 for 20 trades
- Reward: Increase strategy weight or usage frequency
- Penalty: Decrease priority or flag for mutation

## Success Metrics

- Regime detection accuracy > 75%
- Adaptive switch latency < 5 minutes after regime change
- At least 2 strategies optimized per week via reward signals
- Maintain system win rate above 60%
- Keep drawdown < 5% on regime switch

## Technical Implementation

### RL Agent Architecture (lightweight Q-learning)

- States: Current regime, win/loss streak, volatility index
- Actions: Increase, reduce, or pause strategy use
- Rewards: Based on strategy ROI, drawdown control

### Strategy-Context Mapping

- Bull: Use breakout and momentum strategies
- Bear: Use pullback and mean reversion
- Sideways: Use scalping and high RRR micro-trades

## Monitoring Requirements

- Save RL decisions in `/logs/rl_agent_decisions.json`
- Save regime labels in `/data/regime_labels.json`
- Alert via Slack when regime changes
- Log reward-punishment stats weekly

## Phase Completion Criteria

- Regime detection triggers adaptive behavior for 2 consecutive weeks
- RL engine optimizes 3+ strategies
- TRAE maintains profitability and stability across regime switches
- Prompt-based regime/strategy mapping is consistent with logs