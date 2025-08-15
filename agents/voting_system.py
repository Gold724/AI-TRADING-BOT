# voting_system.py

from typing import Dict, Any, List, Optional, Type
import logging
from datetime import datetime
import os
import yaml
import json
from enum import Enum
import importlib

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('voting_system')

class VotingMethod(Enum):
    """Enum for different voting methods"""
    SIMPLE_MAJORITY = "simple_majority"
    WEIGHTED_MAJORITY = "weighted_majority"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    PERFORMANCE_WEIGHTED = "performance_weighted"

class GovernanceMode(Enum):
    """Enum for different governance modes"""
    STATIC = "static"
    DYNAMIC_REPUTATION = "dynamic_reputation"
    PERFORMANCE_BASED = "performance_based"

class VotingSystem:
    """Multi-agent voting system for trade decisions"""
    
    def __init__(self, config_path: str = "config/agents_registry.yml"):
        """Initialize the voting system
        
        Args:
            config_path (str, optional): Path to agent registry config. Defaults to "config/agents_registry.yml".
        """
        self.config_path = config_path
        self.agents: Dict[str, BaseAgent] = {}
        self.voting_method = VotingMethod.WEIGHTED_MAJORITY
        self.governance_mode = GovernanceMode.DYNAMIC_REPUTATION
        self.veto_enabled = True
        self.quorum_threshold = 0.66  # 66% required for decision
        self.decision_timeout = 5  # seconds
        
        # Load configuration
        self._load_config()
        
        # Initialize log directories
        os.makedirs("logs", exist_ok=True)
        
        # Track voting history
        self.vote_history: List[Dict[str, Any]] = []
    
    def _load_config(self) -> None:
        """Load agent registry and system configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load global settings
            global_settings = config.get('global_settings', {})
            
            # Set voting method
            voting_method = global_settings.get('voting_method', 'weighted_majority')
            try:
                self.voting_method = VotingMethod(voting_method)
            except ValueError:
                logger.warning(f"Invalid voting method '{voting_method}', using default")
            
            # Set governance mode
            governance_mode = global_settings.get('governance_mode', 'dynamic_reputation')
            try:
                self.governance_mode = GovernanceMode(governance_mode)
            except ValueError:
                logger.warning(f"Invalid governance mode '{governance_mode}', using default")
            
            # Set other parameters
            self.veto_enabled = global_settings.get('veto_enabled', True)
            self.quorum_threshold = global_settings.get('quorum_threshold', 0.66)
            self.decision_timeout = global_settings.get('decision_timeout', 5)
            
            # Load agents
            agents_config = config.get('agents', {})
            self._initialize_agents(agents_config)
            
            logger.info(f"Loaded configuration with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Use default configuration
            self._initialize_default_agents()
    
    def _initialize_agents(self, agents_config: Dict[str, Dict[str, Any]]) -> None:
        """Initialize agents from configuration
        
        Args:
            agents_config (Dict[str, Dict[str, Any]]): Agent configuration dictionary
        """
        for agent_id, agent_config in agents_config.items():
            try:
                # Get agent class name and module
                agent_type = agent_config.get('type', 'BaseAgent')
                agent_module = agent_config.get('module', f'agents.{agent_type.lower()}')
                
                # Import the module dynamically
                module = importlib.import_module(agent_module)
                
                # Get the agent class
                agent_class = getattr(module, agent_type)
                
                # Initialize the agent
                agent = agent_class(agent_id=agent_id, config=agent_config)
                
                # Add to agents dictionary
                self.agents[agent_id] = agent
                
                logger.info(f"Initialized agent: {agent_id} ({agent_type})")
                
            except Exception as e:
                logger.error(f"Error initializing agent {agent_id}: {e}")
    
    def _initialize_default_agents(self) -> None:
        """Initialize default agents if configuration loading fails"""
        try:
            # Import agent classes
            from agents.trend_analyst import TrendAnalyst
            from agents.risk_auditor import RiskAuditor
            from agents.news_guard import NewsGuard
            from agents.regime_detector import RegimeDetector
            
            # Create default agents
            self.agents["trend_analyst"] = TrendAnalyst()
            self.agents["risk_auditor"] = RiskAuditor()
            self.agents["news_guard"] = NewsGuard()
            self.agents["regime_detector"] = RegimeDetector()
            
            logger.info("Initialized default agents")
            
        except Exception as e:
            logger.error(f"Error initializing default agents: {e}")
    
    def collect_votes(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect trade proposals from all agents
        
        Args:
            context (Dict[str, Any]): Trading context with market data
            
        Returns:
            List[Dict[str, Any]]: List of trade proposals from agents
        """
        proposals = []
        
        for agent_id, agent in self.agents.items():
            try:
                # Check if agent is specialized for this context
                if not agent.is_specialized_for(context):
                    continue
                
                # Get trade proposal
                proposal = agent.propose_trade(context)
                
                # Ensure proposal has required fields
                if not all(k in proposal for k in ["action", "confidence", "reason"]):
                    logger.warning(f"Agent {agent_id} returned incomplete proposal")
                    continue
                
                # Add agent ID if not present
                if "agent_id" not in proposal:
                    proposal["agent_id"] = agent_id
                
                # Add timestamp if not present
                if "timestamp" not in proposal:
                    proposal["timestamp"] = datetime.now().isoformat()
                
                proposals.append(proposal)
                
            except Exception as e:
                logger.error(f"Error getting proposal from agent {agent_id}: {e}")
        
        return proposals
    
    def decide_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make a trade decision based on agent votes
        
        Args:
            context (Dict[str, Any]): Trading context with market data
            
        Returns:
            Dict[str, Any]: Final trade decision
        """
        # Collect votes from all agents
        proposals = self.collect_votes(context)
        
        # Log proposals
        self._log_agent_outputs(proposals)
        
        # Check for vetoes if enabled
        if self.veto_enabled:
            vetoes = [p for p in proposals if p.get("veto", False)]
            if vetoes:
                decision = self._handle_vetoes(vetoes, proposals)
                self._log_vote_result(decision, proposals)
                return decision
        
        # Check if we have enough votes for quorum
        if len(proposals) < 1:
            decision = {
                "action": "hold",
                "confidence": 0,
                "reason": "No agent proposals received",
                "timestamp": datetime.now().isoformat(),
                "voting_method": self.voting_method.value,
                "quorum_reached": False,
                "votes": []
            }
            self._log_vote_result(decision, proposals)
            return decision
        
        # Calculate quorum
        quorum = len(proposals) / len(self.agents)
        quorum_reached = quorum >= self.quorum_threshold
        
        # Resolve votes based on voting method
        if self.voting_method == VotingMethod.SIMPLE_MAJORITY:
            decision = self._simple_majority_vote(proposals)
        elif self.voting_method == VotingMethod.WEIGHTED_MAJORITY:
            decision = self._weighted_majority_vote(proposals)
        elif self.voting_method == VotingMethod.CONFIDENCE_WEIGHTED:
            decision = self._confidence_weighted_vote(proposals)
        elif self.voting_method == VotingMethod.PERFORMANCE_WEIGHTED:
            decision = self._performance_weighted_vote(proposals)
        else:
            # Default to weighted majority
            decision = self._weighted_majority_vote(proposals)
        
        # Add metadata to decision
        decision["timestamp"] = datetime.now().isoformat()
        decision["voting_method"] = self.voting_method.value
        decision["quorum_reached"] = quorum_reached
        decision["votes"] = [{
            "agent_id": p["agent_id"],
            "action": p["action"],
            "confidence": p["confidence"]
        } for p in proposals]
        
        # If quorum not reached, override with hold
        if not quorum_reached:
            decision["action"] = "hold"
            decision["reason"] = f"Quorum not reached ({quorum:.0%} < {self.quorum_threshold:.0%})"
        
        # Log vote result
        self._log_vote_result(decision, proposals)
        
        # Update agent performance if governance is dynamic
        if self.governance_mode != GovernanceMode.STATIC:
            self._update_agent_performance(proposals, decision)
        
        return decision
    
    def _simple_majority_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve votes using simple majority
        
        Args:
            proposals (List[Dict[str, Any]]): List of trade proposals
            
        Returns:
            Dict[str, Any]: Resolved decision
        """
        # Count votes for each action
        action_counts = {"buy": 0, "sell": 0, "hold": 0}
        
        for proposal in proposals:
            action = proposal["action"].lower()
            if action in action_counts:
                action_counts[action] += 1
        
        # Find action with most votes
        max_votes = 0
        winning_action = "hold"  # Default
        
        for action, count in action_counts.items():
            if count > max_votes:
                max_votes = count
                winning_action = action
        
        # Calculate confidence based on vote distribution
        total_votes = sum(action_counts.values())
        confidence = (max_votes / total_votes) * 100 if total_votes > 0 else 0
        
        # Collect reasons from winning proposals
        winning_reasons = [p["reason"] for p in proposals if p["action"].lower() == winning_action]
        reason = "; ".join(winning_reasons) if winning_reasons else "Majority vote"
        
        return {
            "action": winning_action,
            "confidence": confidence,
            "reason": reason
        }
    
    def _weighted_majority_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve votes using weighted majority
        
        Args:
            proposals (List[Dict[str, Any]]): List of trade proposals
            
        Returns:
            Dict[str, Any]: Resolved decision
        """
        # Initialize weighted votes for each action
        action_weights = {"buy": 0, "sell": 0, "hold": 0}
        
        for proposal in proposals:
            action = proposal["action"].lower()
            if action not in action_weights:
                continue
            
            agent_id = proposal["agent_id"]
            agent = self.agents.get(agent_id)
            
            if agent:
                # Get agent's effective weight
                weight = agent.get_effective_weight()
                action_weights[action] += weight
        
        # Find action with highest weighted votes
        max_weight = 0
        winning_action = "hold"  # Default
        
        for action, weight in action_weights.items():
            if weight > max_weight:
                max_weight = weight
                winning_action = action
        
        # Calculate confidence based on weight distribution
        total_weight = sum(action_weights.values())
        confidence = (max_weight / total_weight) * 100 if total_weight > 0 else 0
        
        # Collect reasons from winning proposals
        winning_reasons = [p["reason"] for p in proposals if p["action"].lower() == winning_action]
        reason = "; ".join(winning_reasons) if winning_reasons else "Weighted majority vote"
        
        return {
            "action": winning_action,
            "confidence": confidence,
            "reason": reason
        }
    
    def _confidence_weighted_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve votes using confidence-weighted voting
        
        Args:
            proposals (List[Dict[str, Any]]): List of trade proposals
            
        Returns:
            Dict[str, Any]: Resolved decision
        """
        # Initialize confidence-weighted votes for each action
        action_scores = {"buy": 0, "sell": 0, "hold": 0}
        
        for proposal in proposals:
            action = proposal["action"].lower()
            if action not in action_scores:
                continue
            
            # Get confidence score
            confidence = proposal["confidence"]
            action_scores[action] += confidence
        
        # Find action with highest confidence score
        max_score = 0
        winning_action = "hold"  # Default
        
        for action, score in action_scores.items():
            if score > max_score:
                max_score = score
                winning_action = action
        
        # Calculate overall confidence
        total_score = sum(action_scores.values())
        confidence = (max_score / total_score) * 100 if total_score > 0 else 0
        
        # Collect reasons from winning proposals, prioritizing high confidence
        winning_proposals = [p for p in proposals if p["action"].lower() == winning_action]
        winning_proposals.sort(key=lambda p: p["confidence"], reverse=True)
        
        top_reasons = [p["reason"] for p in winning_proposals[:3]]  # Top 3 reasons
        reason = "; ".join(top_reasons) if top_reasons else "Confidence-weighted vote"
        
        return {
            "action": winning_action,
            "confidence": confidence,
            "reason": reason
        }
    
    def _performance_weighted_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve votes using performance-weighted voting
        
        Args:
            proposals (List[Dict[str, Any]]): List of trade proposals
            
        Returns:
            Dict[str, Any]: Resolved decision
        """
        # Initialize performance-weighted votes for each action
        action_scores = {"buy": 0, "sell": 0, "hold": 0}
        
        for proposal in proposals:
            action = proposal["action"].lower()
            if action not in action_scores:
                continue
            
            agent_id = proposal["agent_id"]
            agent = self.agents.get(agent_id)
            
            if agent:
                # Get agent's performance score
                performance = agent.get_performance_score()
                confidence = proposal["confidence"]
                
                # Weight by both performance and confidence
                action_scores[action] += performance * confidence
        
        # Find action with highest score
        max_score = 0
        winning_action = "hold"  # Default
        
        for action, score in action_scores.items():
            if score > max_score:
                max_score = score
                winning_action = action
        
        # Calculate overall confidence
        total_score = sum(action_scores.values())
        confidence = (max_score / total_score) * 100 if total_score > 0 else 0
        
        # Get top performing agents for the winning action
        winning_proposals = [p for p in proposals if p["action"].lower() == winning_action]
        winning_proposals.sort(
            key=lambda p: self.agents.get(p["agent_id"]).get_performance_score() 
                if p["agent_id"] in self.agents else 0, 
            reverse=True
        )
        
        top_reasons = [p["reason"] for p in winning_proposals[:3]]  # Top 3 reasons
        reason = "; ".join(top_reasons) if top_reasons else "Performance-weighted vote"
        
        return {
            "action": winning_action,
            "confidence": confidence,
            "reason": reason
        }
    
    def _handle_vetoes(self, vetoes: List[Dict[str, Any]], proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle veto votes
        
        Args:
            vetoes (List[Dict[str, Any]]): List of veto proposals
            proposals (List[Dict[str, Any]]): All proposals
            
        Returns:
            Dict[str, Any]: Decision with veto applied
        """
        # Sort vetoes by agent priority
        vetoes.sort(
            key=lambda v: self.agents.get(v["agent_id"]).get_effective_weight() 
                if v["agent_id"] in self.agents else 0,
            reverse=True
        )
        
        # Take the highest priority veto
        top_veto = vetoes[0]
        
        return {
            "action": "hold",  # Vetoes always result in hold
            "confidence": top_veto["confidence"],
            "reason": f"VETO: {top_veto['reason']}",
            "timestamp": datetime.now().isoformat(),
            "voting_method": "veto",
            "quorum_reached": True,
            "veto_agent": top_veto["agent_id"],
            "votes": [{
                "agent_id": p["agent_id"],
                "action": p["action"],
                "confidence": p["confidence"]
            } for p in proposals]
        }
    
    def _update_agent_performance(self, proposals: List[Dict[str, Any]], decision: Dict[str, Any]) -> None:
        """Update agent performance based on voting results
        
        Args:
            proposals (List[Dict[str, Any]]): List of trade proposals
            decision (Dict[str, Any]): Final trade decision
        """
        # Only update if we have a valid decision
        if "action" not in decision or decision["action"] == "hold":
            return
        
        # Record vote in history for later performance evaluation
        vote_record = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision["action"],
            "proposals": proposals,
            "outcome": None  # Will be updated later with trade outcome
        }
        
        self.vote_history.append(vote_record)
        
        # Limit history size
        if len(self.vote_history) > 1000:
            self.vote_history = self.vote_history[-1000:]
    
    def update_trade_outcome(self, timestamp: str, outcome: Dict[str, Any]) -> None:
        """Update trade outcome and agent performance
        
        Args:
            timestamp (str): Timestamp of the trade decision
            outcome (Dict[str, Any]): Trade outcome information
        """
        # Find the vote record
        for vote in self.vote_history:
            if vote["timestamp"] == timestamp:
                # Update outcome
                vote["outcome"] = outcome
                
                # Update agent performance
                self._evaluate_agent_performance(vote)
                break
    
    def _evaluate_agent_performance(self, vote_record: Dict[str, Any]) -> None:
        """Evaluate agent performance based on trade outcome
        
        Args:
            vote_record (Dict[str, Any]): Vote record with outcome
        """
        if "outcome" not in vote_record or not vote_record["outcome"]:
            return
        
        outcome = vote_record["outcome"]
        decision = vote_record["decision"]
        proposals = vote_record["proposals"]
        
        # Calculate if the decision was correct
        correct = False
        if "profit" in outcome:
            profit = outcome["profit"]
            correct = (profit > 0 and decision == "buy") or (profit < 0 and decision == "sell")
        
        # Update each agent's performance
        for proposal in proposals:
            agent_id = proposal["agent_id"]
            if agent_id not in self.agents:
                continue
            
            agent = self.agents[agent_id]
            
            # Calculate agent's score for this decision
            agent_correct = proposal["action"] == decision if correct else proposal["action"] != decision
            confidence = proposal["confidence"] / 100.0  # Normalize to 0-1
            
            # Score is positive if agent was correct, negative if incorrect
            # Weighted by confidence (higher confidence = higher reward/penalty)
            score = confidence if agent_correct else -confidence
            
            # Update agent performance
            agent.update_performance(score)
    
    def _log_agent_outputs(self, proposals: List[Dict[str, Any]]) -> None:
        """Log agent outputs to file
        
        Args:
            proposals (List[Dict[str, Any]]): List of trade proposals
        """
        try:
            log_file = "logs/agent_outputs.json"
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "proposals": proposals
            }
            
            # Append to log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging agent outputs: {e}")
    
    def _log_vote_result(self, decision: Dict[str, Any], proposals: List[Dict[str, Any]]) -> None:
        """Log voting results to file
        
        Args:
            decision (Dict[str, Any]): Final trade decision
            proposals (List[Dict[str, Any]]): List of trade proposals
        """
        try:
            log_file = "logs/vote_results.json"
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "proposals": proposals
            }
            
            # Append to log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging vote results: {e}")
    
    def reload_config(self) -> None:
        """Reload agent registry configuration"""
        logger.info("Reloading agent registry configuration")
        self._load_config()