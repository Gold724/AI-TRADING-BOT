# TRAE Phase 7: Adaptive Liquidity Routing & Intent Prediction

## Goals

- Dynamically route trades based on real-time liquidity conditions
- Predict short-term market intent using microstructure features
- Adjust execution tactics to reduce slippage and latency
- Integrate AI awareness of spread widening, spoofing, and exhaustion candles

## System Instructions

### Sentinel Decider Activation

```
trigger: sentinel_decider.py
mode: flow-conscious
parameters:
  liquidity_routing: enabled
  intent_prediction: active
  spread_watch: true
  latency_limit_ms: 120
```

### Liquidity Routing Logic

- Check order book depth across platforms (Exness, Bulenox, Binance)
- Re-route orders if:
  - Spread widens > 2x median
  - Last trade volume drops below 25th percentile
  - Execution latency > 120ms
- Prefer venues with:
  - Narrow spreads
  - High tick volume
  - Consistent fill rates

### Intent Prediction Engine

- Analyze microstructure signals:
  - Hidden orders
  - Rapid bid/ask flips
  - Clustered order book imbalances
  - Short-term divergence from VWAP
- Classify intent as:
  - Institutional Absorption
  - Spoofing / Fake Walls
  - Genuine Momentum
  - Exhaustion or Trap

- Tag current trade context with inferred intent
- Adjust execution style:
  - Reduce size in spoof zones
  - Accelerate fills during absorption
  - Cancel trades in exhaustion signals

## Guardrails

- Auto-throttle execution speed if:
  - >3 failed fills in 5 minutes
  - Latency spikes > 200ms
- Send Slack alert on execution reroute
- Log anomalies in `/logs/liquidity_routing.log`

## Monitoring & Logging

- `/logs/liquidity_routing.log`
- `/logs/intent_signals.json`
- `/data/routing_metrics.json`
- Slack channel: #execution-routing-alerts

## Success Metrics

- Average fill quality improvement ≥ 15%
- Slippage reduced by ≥ 25% vs baseline
- Trade reroute accuracy ≥ 80%
- Average intent classification confidence ≥ 70%
- Latency <= 120ms on 90%+ of trades

## Phase Completion Criteria

- Adaptive routing active for 2 consecutive weeks
- Intent prediction classifies >300 signals with ≥ 70% confidence
- Demonstrated slippage reduction over 100+ trades
- Routing reroutes at least 50 trades with valid justification
- Zero crashes or timeout-related failures