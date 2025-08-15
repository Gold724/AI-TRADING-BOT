# AI Strategy Evolution System (SE-Layer)

## Overview

The AI Strategy Evolution System (SE-Layer) is a self-learning feedback loop that enables TRAE to learn from past trades, news impact, win rates, and market environment to self-optimize future trading strategies. This system makes TRAE capable of continuous improvement even when you're not actively monitoring it.

## Components

### 1. 🧠 `strategy_brain.py` - TRAE's Memory + Strategy Evolver

The Strategy Brain serves as the central memory system for TRAE, storing and analyzing:

- Past trade signals, outcomes, news context, and risk levels
- Which strategy + environment combinations worked best
- Learning what not to do again
- When to reintroduce old strategies that may now work again

The Strategy Brain maintains strategy statistics including win rates, confidence levels, and status (active, cooldown, paused).

### 2. 🧬 `reinforce_trader.py` - Lightweight Reinforcement Learner

Implements a Q-learning based reinforcement learning system that learns optimal trading actions based on:

- **State**: [strategy, pair, time, confidence, news level]
- **Actions**: [trade, skip, reduce risk, switch strategy]
- **Reward Function**: profit per trade

Over time, the reinforcement learner tries different combinations and learns which actions maximize profit in different market conditions.

### 3. 📰 `sentiment_sensor.py` - Real-Time News & Sentiment Filter

Gathers and analyzes sentiment data from multiple sources:

- Economic calendar events (like Forex Factory)
- Social media sentiment for major currencies
- Market volatility indicators

Scores sentiment as bullish/bearish and detects high volatility alerts, which are then injected into the decision confidence before trade execution.

### 4. 🧾 `strategy_history.json` - Historical AI Feedback Loop

Stores detailed records of every trade and strategy execution, including:

- Trade details (symbol, strategy, direction, entry/exit prices)
- Confidence levels and news context
- Results (win/loss, pips, profit)
- Market conditions and time of day

This historical data serves as the foundation for the AI's learning process.

### 5. 🎛️ `strategy_optimizer.py` - Weekly AI-Based Weight Adjuster

Analyzes trading history and performance metrics to optimize strategy weights and parameters:

- Reads `strategy_history.json` and weekly win rates
- Analyzes sentiment patterns and market conditions
- Suggests strategy adjustments (e.g., "Increase OTE use by 10%")
- Recommends pair-specific adjustments (e.g., "Avoid GBP pairs before UK open")
- Provides risk management suggestions (e.g., "Lower risk 1 hour before NFP")

## Integration with Existing System

The AI Strategy Evolution System integrates with the following existing components:

| Existing Component | New Functionality |
|-------------------|-------------------|
| `sentinel_decider.py` | Receives updated confidence from `strategy_brain.py` |
| `risk_control.py` | Reads AI-recommended risk per pair |
| `news_guard.py` | Injects live news + sentiment score |
| `weekly_report.py` | Outputs strategy evolution status |

## Main Integration File

### `ai_evolution_system.py`

This file serves as the main integration point for all components of the AI Strategy Evolution System. It provides a unified interface for the Sentinel trading system to leverage the AI-powered strategy evolution capabilities.

Key functionalities include:

- Evaluating trade opportunities with AI-enhanced confidence scores
- Recording trade results for continuous learning
- Running weekly strategy optimization
- Providing sentiment summaries and upcoming event notifications

## Usage Example

The `ai_integration_example.py` file demonstrates how to integrate the AI Strategy Evolution System with the existing trading components:

```python
# Initialize the AI Evolution System
ai_system = AIEvolutionSystem()

# Evaluate a trade opportunity
evaluation = ai_system.evaluate_trade_opportunity(
    strategy="OTE",
    pair="EURUSD",
    confidence=75,
    market_condition="trending",
    time_of_day="london_open"
)

# Use the AI-adjusted confidence in the SentinelDecider
if evaluation['proceed_with_trade']:
    sentinel_decision = sentinel_decider.decide(
        strategy=trade_signal["strategy"],
        pair=trade_signal["pair"],
        confidence=evaluation["final_confidence"]  # Use AI-adjusted confidence
    )
    
    # Adjust risk based on AI recommendation
    risk_params = risk_controller.adjust_risk(
        pair=trade_signal["pair"],
        confidence=evaluation["final_confidence"],
        news_impact="high" if evaluation["risk_level"] == "reduced" else "normal"
    )
    
    # Execute trade...
    
    # Record trade result for learning
    ai_system.record_trade_result(trade_result)
```

## TRAE AI Evolution Layer Prompt

To activate the AI Evolution Layer, use the following prompt with TRAE:

```
# TRAE AI Evolution Layer
You are now evolving TRAE into a self-learning system.

1. Load strategy_history.json from the past 7 days.
2. Update win/loss per strategy and pair.
3. Adjust risk levels in sentinel_config.yml based on performance.
4. Modify active strategy weights.
5. Inject live sentiment score from sentiment_sensor.py.
6. Export new strategy_brain.json for the next trading day.
```

## Benefits

The AI Strategy Evolution System provides the following benefits:

- 🔁 Self-learning feedback loop
- 🧠 Memory-aware trade decisions
- 📉 Risk minimized before danger
- 💰 Profit focused when confident
- 🌍 Sentiment and news aware
- 🧘 No overtrading. No fear. Just clarity.