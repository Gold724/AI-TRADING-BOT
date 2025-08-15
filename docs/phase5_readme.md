# TRAE Phase 5: Strategic Optimization via Multi-Agent Collaboration

## Overview

Phase 5 introduces a decentralized multi-agent decision framework to the TRAE system, enabling more robust and contextually aware trading decisions. This phase builds upon the reinforcement learning and market regime detection capabilities from Phase 4, adding a collaborative voting system where specialized agents contribute their expertise to form consensus-based decisions.

## Key Components

### 1. Multi-Agent Architecture

- **Agent Registry**: Centralized configuration in `config/agents_registry.yml` defining agent roles, weights, and specializations
- **Base Agent Interface**: Common interface in `agents/base_agent.py` that all specialized agents implement
- **Specialized Agents**: Role-specific agents with unique analysis capabilities:
  - `TrendAnalyst`: Technical indicator analysis and trend detection
  - `NewsGuard`: News event monitoring and impact assessment
  - `RiskAuditor`: Risk policy enforcement and trade vetting
  - `RegimeDetector`: Market regime identification and strategy adaptation

### 2. Voting System

- **Voting Methods**: Multiple consensus algorithms including simple majority, weighted majority, and confidence-weighted voting
- **Veto Mechanism**: Guard agents can block high-risk trades that violate safety policies
- **Governance**: Dynamic adjustment of agent influence based on performance history

### 3. Decision Framework

- **Contextual Analysis**: Each agent evaluates trade proposals within their domain of expertise
- **Confidence Scoring**: Agents assign confidence levels to their recommendations
- **Consensus Building**: Weighted aggregation of agent votes to determine final action
- **Performance Tracking**: Continuous evaluation of agent effectiveness to adjust influence

## Usage

The multi-agent system is activated through the `sentinel_decider.py` module in multi-agent mode:

```python
from sentinel_decider import SentinelDecider

# Initialize with Phase 5
decider = SentinelDecider(phase=5)

# Create a signal
signal = {
    "market_data": {...},
    "strategy": "trend_following",
    "type": "entry",
    "indicators": {...},
    "news": {...},
    "account_info": {...}
}

# Get collaborative decision
decision = decider.decide_trade(signal)

# Access decision details
print(f"Action: {decision['action']}")
print(f"Confidence: {decision['confidence']}%")
print(f"Reasoning: {decision['reasoning']}")
print(f"Voting method: {decision['voting_method']}")

# Review individual agent votes
for vote in decision['votes']:
    print(f"Agent: {vote['agent']}, Vote: {vote['vote']}, Confidence: {vote['confidence']}%")
```

## Monitoring

The multi-agent system generates detailed logs for monitoring and analysis:

- **Agent Outputs**: Individual agent recommendations in `/logs/agent_outputs.json`
- **Voting Results**: Consensus decisions in `/logs/vote_results.json`
- **Performance Metrics**: Agent accuracy and influence tracking in `/logs/agent_performance.json`

## Testing

A comprehensive test suite is available in `test_multi_agent.py` to verify the functionality of the multi-agent system:

```bash
python test_multi_agent.py
```

The tests validate:
- Proper initialization of the multi-agent system
- Correct configuration of the voting system
- Accurate collection and processing of agent votes
- Appropriate fallback to standard mode if the voting system fails

## Success Metrics

The multi-agent system is designed to meet the following performance targets:

- **Decision Speed**: < 5 seconds per trade decision
- **Strategy Overlap Detection**: > 90% accuracy in identifying conflicting strategies
- **Logging Coverage**: > 90% of trades have complete voting logs
- **Risk Reduction**: 10% reduction in drawdown compared to Phase 4
- **Agent Diversity**: Minimum of 3 functional agents with specialized roles

## Future Enhancements

- **Dynamic Agent Creation**: Runtime generation of new specialized agents
- **Hierarchical Decision Making**: Multi-level voting for complex decisions
- **Cross-Agent Learning**: Knowledge sharing between agents to improve collective intelligence
- **External Data Integration**: Expanded data sources for more informed agent decisions