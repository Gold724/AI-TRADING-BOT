# test_multi_agent.py

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SentinelDecider
from sentinel_decider import SentinelDecider, DeciderMode

class TestMultiAgentSystem(unittest.TestCase):
    
    def setUp(self):
        # Create a mock phase-5.md file for testing
        self.create_test_phase_file()
        
        # Create a mock agents_registry.yml file
        self.create_test_registry_file()
        
        # Set environment variable to use our test file
        os.environ["TRAE_PHASE_PROMPT"] = "trae_prompts/phase-5.md"
        
        # Initialize the decider with phase 5
        self.decider = SentinelDecider(phase=5)
    
    def tearDown(self):
        # Clean up test files
        if os.path.exists("trae_prompts/phase-5.md"):
            os.remove("trae_prompts/phase-5.md")
        
        if os.path.exists("config/agents_registry.yml"):
            os.remove("config/agents_registry.yml")
    
    def create_test_phase_file(self):
        """Create a test phase-5.md file"""
        # Ensure directory exists
        os.makedirs("trae_prompts", exist_ok=True)
        
        content = """
# TRAE Phase 5: Strategic Optimization via Multi-Agent Collaboration

## Goals

- Implement decentralized multi-agent decision framework
- Introduce strategy voting with weighted confidence scores
- Add anomaly guardrails to filter high-risk decisions
- Assign specialized roles to agents for contextual intelligence
- Establish emergent governance based on performance

## System Instructions

### Sentinel Decider Activation

```
trigger: sentinel_decider.py
mode: multi_agent
parameters:
  voting_method: weighted_majority
  veto_enabled: true
  governance_mode: dynamic_reputation
  agent_registry_path: config/agents_registry.yml
```

### Risk Policies

- Maximum drawdown per agent: 3%
- Global system drawdown limit: 5%
- Minimum quorum for trade approval: 66%
- Trade veto allowed by: news_guard, risk_auditor

### News Sensitivity Thresholds

- High impact news: all agents pause proposals
- Medium news: confidence scores reduced by 50%
- Low news: warning flag only
"""
        
        with open("trae_prompts/phase-5.md", "w") as f:
            f.write(content)
    
    def create_test_registry_file(self):
        """Create a test agents_registry.yml file"""
        # Ensure directory exists
        os.makedirs("config", exist_ok=True)
        
        content = """
# Multi-Agent Collaboration Framework Configuration

# Global settings
global:
  voting_method: weighted_majority  # simple_majority, weighted_majority, confidence_weighted
  veto_rights: true                 # Whether agents can veto trades
  governance_mode: dynamic_reputation  # static, dynamic_reputation, performance_based
  quorum: 66                        # Percentage of agents required for decision
  decision_time_ms: 5000            # Maximum time for decision in milliseconds

# Agent definitions
agents:
  trend_analyst:
    role: strategy
    description: Analyzes market trends using technical indicators
    weight: 1.0
    veto_rights: false
    specializations: [trend, momentum, volatility]
    performance_metrics:
      accuracy: 0.0
      profit_factor: 0.0
      trades_count: 0
  
  news_guard:
    role: guard
    description: Monitors news events and blocks trades during high impact news
    weight: 1.2
    veto_rights: true
    specializations: [news, events, announcements]
    performance_metrics:
      accuracy: 0.0
      profit_factor: 0.0
      trades_count: 0
  
  risk_auditor:
    role: guard
    description: Evaluates trade risk and ensures compliance with risk policies
    weight: 1.5
    veto_rights: true
    specializations: [risk, exposure, drawdown]
    performance_metrics:
      accuracy: 0.0
      profit_factor: 0.0
      trades_count: 0
"""
        
        with open("config/agents_registry.yml", "w") as f:
            f.write(content)
    
    def test_decider_initialization(self):
        """Test that the decider initializes in multi-agent mode"""
        self.assertTrue(self.decider.multi_agent_mode)
        self.assertEqual(self.decider.mode, DeciderMode.MULTI_AGENT)
        self.assertIsNotNone(self.decider.voting_system)
    
    def test_voting_system_configuration(self):
        """Test that the voting system is configured correctly"""
        self.assertEqual(self.decider.voting_system.voting_method, "weighted_majority")
        self.assertTrue(self.decider.voting_system.veto_enabled)
        self.assertEqual(self.decider.voting_system.governance_mode, "dynamic_reputation")
        self.assertEqual(len(self.decider.voting_system.agents), 3)  # 3 agents defined in registry
    
    @patch('agents.voting_system.VotingSystem.decide_trade')
    def test_decide_trade_multi_agent(self, mock_decide_trade):
        """Test that decide_trade uses the voting system in multi-agent mode"""
        # Mock the voting system's decide_trade method
        mock_decide_trade.return_value = {
            "action": "buy",
            "confidence": 85,
            "reason": "Majority of agents voted to buy",
            "timestamp": datetime.now().isoformat(),
            "voting_method": "weighted_majority",
            "votes": [
                {"agent": "trend_analyst", "vote": "buy", "confidence": 90},
                {"agent": "news_guard", "vote": "hold", "confidence": 60},
                {"agent": "risk_auditor", "vote": "buy", "confidence": 75}
            ]
        }
        
        # Create a signal
        signal = {
            "market_data": {"price": 100, "volume": 1000},
            "strategy": "trend_following",
            "type": "entry",
            "indicators": {"rsi": 65, "macd": 0.5}
        }
        
        # Get decision
        decision = self.decider.decide_trade(signal)
        
        # Verify the decision
        self.assertEqual(decision["action"], "buy")
        self.assertEqual(decision["confidence"], 85)
        self.assertEqual(decision["voting_method"], "weighted_majority")
        self.assertEqual(len(decision["votes"]), 3)
        
        # Verify that the voting system was called with the correct context
        mock_decide_trade.assert_called_once()
        context = mock_decide_trade.call_args[0][0]
        self.assertEqual(context["market_data"], signal["market_data"])
        self.assertEqual(context["strategy"], signal["strategy"])
        self.assertEqual(context["indicators"], signal["indicators"])

    def test_fallback_to_standard_mode(self):
        """Test that the decider falls back to standard mode if voting system fails"""
        # Create a signal
        signal = {
            "market_data": {"price": 100, "volume": 1000},
            "strategy": "trend_following",
            "type": "entry"
        }
        
        # Break the voting system
        self.decider.voting_system = None
        
        # Get decision
        decision = self.decider.decide_trade(signal)
        
        # Verify the decision uses standard mode
        self.assertIn("action", decision)
        self.assertIn("confidence", decision)
        self.assertIn("reasoning", decision)
        self.assertIn("timestamp", decision)
        self.assertNotIn("voting_method", decision)  # This is only in multi-agent mode
        self.assertNotIn("votes", decision)  # This is only in multi-agent mode

if __name__ == "__main__":
    unittest.main()