# agents/governor_agent.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import os
import json
import numpy as np

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('governor_agent')

class GovernorAgent(BaseAgent):
    """Resolves conflicts between agents and maintains balance in the system"""
    
    def __init__(self, agent_id: str = "governor", config: Dict[str, Any] = None):
        """Initialize the Governor agent
        
        Args:
            agent_id (str, optional): Unique identifier for this agent. Defaults to "governor".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id=agent_id, role="governance", config=config)
        
        # Initialize with default config if none provided
        if config is None:
            config = {}
        
        # Configuration parameters
        self.conflict_threshold = config.get("conflict_threshold", 0.5)  # Threshold for conflict detection
        self.anomaly_threshold = config.get("anomaly_threshold", 0.8)  # Threshold for anomaly detection
        self.intervention_cooldown = config.get("intervention_cooldown", 10)  # Trades between interventions
        
        # Internal state
        self.agent_votes: Dict[str, List[Dict[str, Any]]] = {}  # Recent votes by agent
        self.conflicts: List[Dict[str, Any]] = []  # Recent conflicts
        self.interventions: List[Dict[str, Any]] = []  # Recent interventions
        self.trades_since_intervention = 0
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a trade action based on the provided context
        
        Args:
            context (Dict[str, Any]): Trading context including market data, signals, etc.
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Extract relevant data from context
        agent_proposals = context.get("agent_proposals", {})
        anomaly_scores = context.get("anomaly_scores", {})
        strategy = context.get("strategy", "unknown")
        
        # Update internal state with new proposals
        if agent_proposals:
            self.update_agent_votes(agent_proposals)
        
        # Default proposal
        proposal = {
            "action": "defer",
            "confidence": 50,
            "reason": "No conflicts or anomalies detected",
            "timestamp": datetime.now().isoformat(),
            "intervention": None
        }
        
        # Check for anomalies
        max_anomaly = max(anomaly_scores.values()) if anomaly_scores else 0.0
        if max_anomaly >= self.anomaly_threshold:
            # Critical anomaly detected - halt trading
            proposal["action"] = "halt"
            proposal["confidence"] = 90
            proposal["reason"] = f"Critical anomaly detected (score: {max_anomaly:.2f}). Halting trading."
            proposal["intervention"] = {
                "type": "anomaly_halt",
                "anomaly_score": max_anomaly,
                "affected_agents": [agent for agent, score in anomaly_scores.items() if score >= self.anomaly_threshold]
            }
            
            # Log the intervention
            self.log_intervention(proposal["intervention"], strategy)
            
            # Reset intervention cooldown
            self.trades_since_intervention = 0
            
            return proposal
        
        # Check for conflicts between agents
        if agent_proposals and len(agent_proposals) >= 2:
            conflict = self.detect_conflict(agent_proposals)
            
            if conflict and conflict["severity"] >= self.conflict_threshold:
                # Significant conflict detected
                if self.trades_since_intervention >= self.intervention_cooldown:
                    # Resolve the conflict
                    resolution = self.resolve_conflict(conflict, agent_proposals)
                    
                    proposal["action"] = resolution["action"]
                    proposal["confidence"] = resolution["confidence"]
                    proposal["reason"] = f"Conflict detected and resolved: {resolution['reason']}"
                    proposal["intervention"] = {
                        "type": "conflict_resolution",
                        "conflict": conflict,
                        "resolution": resolution
                    }
                    
                    # Log the intervention
                    self.log_intervention(proposal["intervention"], strategy)
                    
                    # Reset intervention cooldown
                    self.trades_since_intervention = 0
                else:
                    # Conflict detected but in cooldown period
                    proposal["action"] = "defer"
                    proposal["confidence"] = 60
                    proposal["reason"] = f"Conflict detected but in cooldown period ({self.trades_since_intervention}/{self.intervention_cooldown} trades)"
            else:
                # No significant conflict
                proposal["action"] = "defer"
                proposal["confidence"] = 55
                proposal["reason"] = "No significant conflicts detected"
                self.trades_since_intervention += 1
        
        return proposal
    
    def update_agent_votes(self, agent_proposals: Dict[str, Dict[str, Any]]) -> None:
        """Update internal record of agent votes
        
        Args:
            agent_proposals (Dict[str, Dict[str, Any]]): Proposals from different agents
        """
        for agent_id, proposal in agent_proposals.items():
            if agent_id not in self.agent_votes:
                self.agent_votes[agent_id] = []
            
            # Add timestamp if not present
            if "timestamp" not in proposal:
                proposal["timestamp"] = datetime.now().isoformat()
            
            # Add to agent votes history
            self.agent_votes[agent_id].append(proposal)
            
            # Keep only recent votes (last 20)
            if len(self.agent_votes[agent_id]) > 20:
                self.agent_votes[agent_id] = self.agent_votes[agent_id][-20:]
    
    def detect_conflict(self, agent_proposals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Detect conflicts between agent proposals
        
        Args:
            agent_proposals (Dict[str, Dict[str, Any]]): Proposals from different agents
            
        Returns:
            Dict[str, Any]: Conflict information or None if no conflict
        """
        # Group proposals by action
        action_groups = {}
        for agent_id, proposal in agent_proposals.items():
            action = proposal.get("action", "unknown")
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append((agent_id, proposal))
        
        # Check if there's disagreement
        if len(action_groups) <= 1:
            return None  # All agents agree
        
        # Find the two largest groups
        sorted_groups = sorted(action_groups.items(), key=lambda x: len(x[1]), reverse=True)
        primary_action, primary_group = sorted_groups[0]
        secondary_action, secondary_group = sorted_groups[1] if len(sorted_groups) > 1 else (None, [])
        
        # Calculate conflict severity based on group sizes and confidence
        total_agents = len(agent_proposals)
        primary_size = len(primary_group)
        secondary_size = len(secondary_group) if secondary_group else 0
        
        # Calculate weighted confidence for each group
        primary_confidence = sum(p[1].get("confidence", 50) for p in primary_group) / primary_size if primary_size > 0 else 0
        secondary_confidence = sum(p[1].get("confidence", 50) for p in secondary_group) / secondary_size if secondary_size > 0 else 0
        
        # Calculate conflict severity (0.0 to 1.0)
        # Higher when groups are similar in size and confidence
        size_ratio = min(primary_size, secondary_size) / max(primary_size, secondary_size) if max(primary_size, secondary_size) > 0 else 0
        confidence_ratio = min(primary_confidence, secondary_confidence) / max(primary_confidence, secondary_confidence) if max(primary_confidence, secondary_confidence) > 0 else 0
        
        severity = (size_ratio * 0.7) + (confidence_ratio * 0.3)
        
        # Create conflict record
        conflict = {
            "timestamp": datetime.now().isoformat(),
            "primary_action": primary_action,
            "primary_agents": [p[0] for p in primary_group],
            "primary_confidence": primary_confidence,
            "secondary_action": secondary_action,
            "secondary_agents": [p[0] for p in secondary_group],
            "secondary_confidence": secondary_confidence,
            "severity": severity
        }
        
        # Add to conflicts history
        self.conflicts.append(conflict)
        
        # Keep only recent conflicts (last 50)
        if len(self.conflicts) > 50:
            self.conflicts = self.conflicts[-50:]
        
        # Log conflict if significant
        if severity >= self.conflict_threshold:
            self.log_conflict(conflict)
        
        return conflict
    
    def resolve_conflict(self, conflict: Dict[str, Any], agent_proposals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflict between agent proposals
        
        Args:
            conflict (Dict[str, Any]): Conflict information
            agent_proposals (Dict[str, Dict[str, Any]]): Proposals from different agents
            
        Returns:
            Dict[str, Any]: Resolution decision
        """
        # Extract conflict information
        primary_action = conflict["primary_action"]
        primary_confidence = conflict["primary_confidence"]
        secondary_action = conflict["secondary_action"]
        secondary_confidence = conflict["secondary_confidence"]
        severity = conflict["severity"]
        
        # Default resolution
        resolution = {
            "action": "hold",
            "confidence": 60,
            "reason": "Default conflict resolution"
        }
        
        # Check for critical actions
        if "halt" in [primary_action, secondary_action]:
            # Always prioritize halt actions for safety
            resolution["action"] = "halt"
            resolution["confidence"] = 85
            resolution["reason"] = "Safety-first: prioritizing halt action due to agent conflict"
            return resolution
        
        # Check for high severity conflicts
        if severity > 0.8:
            # For very severe conflicts, defer to human or take conservative action
            resolution["action"] = "defer_to_human"
            resolution["confidence"] = 90
            resolution["reason"] = f"Critical conflict severity ({severity:.2f}): deferring to human operator"
            return resolution
        
        # Check agent specialization and historical performance
        specialized_votes = {}
        for agent_id, proposal in agent_proposals.items():
            action = proposal.get("action", "unknown")
            confidence = proposal.get("confidence", 50)
            
            # Check if this agent has specialized knowledge for this context
            is_specialized = proposal.get("is_specialized", False)
            
            if is_specialized:
                if action not in specialized_votes:
                    specialized_votes[action] = []
                specialized_votes[action].append((agent_id, confidence))
        
        # If we have specialized votes, prioritize them
        if specialized_votes:
            # Find action with highest combined confidence from specialized agents
            best_action = max(specialized_votes.items(), 
                             key=lambda x: sum(conf for _, conf in x[1]))[0]
            
            resolution["action"] = best_action
            resolution["confidence"] = 75
            resolution["reason"] = f"Prioritizing specialized agents' recommendation: {best_action}"
            return resolution
        
        # Otherwise, use weighted voting based on confidence and historical performance
        action_scores = {}
        for agent_id, proposal in agent_proposals.items():
            action = proposal.get("action", "unknown")
            confidence = proposal.get("confidence", 50)
            
            # Get agent's historical performance weight
            performance_weight = self.get_agent_performance_weight(agent_id)
            
            # Calculate weighted score
            weighted_score = confidence * performance_weight
            
            if action not in action_scores:
                action_scores[action] = 0
            action_scores[action] += weighted_score
        
        # Select action with highest score
        if action_scores:
            best_action = max(action_scores.items(), key=lambda x: x[1])[0]
            
            resolution["action"] = best_action
            resolution["confidence"] = 70
            resolution["reason"] = f"Weighted voting resolution: {best_action} has highest combined score"
        
        return resolution
    
    def get_agent_performance_weight(self, agent_id: str) -> float:
        """Get performance-based weight for an agent
        
        Args:
            agent_id (str): Agent identifier
            
        Returns:
            float: Performance weight (0.5 to 1.5)
        """
        # Default weight
        default_weight = 1.0
        
        # Check if we have vote history for this agent
        if agent_id not in self.agent_votes or len(self.agent_votes[agent_id]) < 5:
            return default_weight
        
        # Calculate recent accuracy
        recent_votes = self.agent_votes[agent_id][-5:]
        correct_count = sum(1 for vote in recent_votes if vote.get("was_correct", False))
        accuracy = correct_count / len(recent_votes)
        
        # Scale weight based on accuracy
        # 0% accuracy -> 0.5 weight
        # 50% accuracy -> 1.0 weight
        # 100% accuracy -> 1.5 weight
        return 0.5 + accuracy
    
    def log_conflict(self, conflict: Dict[str, Any]) -> None:
        """Log conflict to file
        
        Args:
            conflict (Dict[str, Any]): Conflict information
        """
        try:
            import os
            import json
            
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Append to log file
            with open("logs/agent_conflicts.log", "a") as f:
                f.write(json.dumps(conflict) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging conflict: {e}")
    
    def log_intervention(self, intervention: Dict[str, Any], strategy: str) -> None:
        """Log intervention to file
        
        Args:
            intervention (Dict[str, Any]): Intervention information
            strategy (str): Strategy name
        """
        try:
            import os
            import json
            
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Add additional information
            intervention["timestamp"] = datetime.now().isoformat()
            intervention["strategy"] = strategy
            intervention["agent_id"] = self.agent_id
            
            # Append to interventions history
            self.interventions.append(intervention)
            
            # Keep only recent interventions (last 100)
            if len(self.interventions) > 100:
                self.interventions = self.interventions[-100:]
            
            # Append to log file
            with open("logs/governor_interventions.json", "a") as f:
                f.write(json.dumps(intervention) + "\n")
                
            # Update weekly summary
            self.update_governance_summary()
                
        except Exception as e:
            logger.error(f"Error logging intervention: {e}")
    
    def update_governance_summary(self) -> None:
        """Update weekly governance summary"""
        try:
            import os
            import json
            from datetime import datetime, timedelta
            
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Get current week number
            current_date = datetime.now()
            week_number = current_date.isocalendar()[1]
            year = current_date.year
            
            # Summary file path
            summary_path = "data/governance_summary.json"
            
            # Load existing summary if available
            summary = {}
            if os.path.exists(summary_path):
                with open(summary_path, "r") as f:
                    summary = json.load(f)
            
            # Create key for current week
            week_key = f"{year}-W{week_number:02d}"
            
            if week_key not in summary:
                summary[week_key] = {
                    "start_date": (current_date - timedelta(days=current_date.weekday())).isoformat(),
                    "end_date": (current_date + timedelta(days=6-current_date.weekday())).isoformat(),
                    "conflicts": {
                        "total": 0,
                        "resolved": 0,
                        "by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0}
                    },
                    "anomalies": {
                        "total": 0,
                        "by_score": {"low": 0, "medium": 0, "high": 0, "critical": 0}
                    },
                    "interventions": {
                        "total": 0,
                        "by_type": {}
                    },
                    "strategies": {}
                }
            
            # Update summary with latest intervention
            if self.interventions:
                latest = self.interventions[-1]
                
                # Update intervention counts
                summary[week_key]["interventions"]["total"] += 1
                
                intervention_type = latest.get("type", "unknown")
                if intervention_type not in summary[week_key]["interventions"]["by_type"]:
                    summary[week_key]["interventions"]["by_type"][intervention_type] = 0
                summary[week_key]["interventions"]["by_type"][intervention_type] += 1
                
                # Update strategy-specific stats
                strategy = latest.get("strategy", "unknown")
                if strategy not in summary[week_key]["strategies"]:
                    summary[week_key]["strategies"][strategy] = {
                        "interventions": 0,
                        "conflicts": 0,
                        "anomalies": 0
                    }
                
                summary[week_key]["strategies"][strategy]["interventions"] += 1
                
                # Update conflict stats if this was a conflict resolution
                if intervention_type == "conflict_resolution" and "conflict" in latest:
                    conflict = latest["conflict"]
                    severity = conflict.get("severity", 0.0)
                    
                    summary[week_key]["conflicts"]["total"] += 1
                    summary[week_key]["conflicts"]["resolved"] += 1
                    summary[week_key]["strategies"][strategy]["conflicts"] += 1
                    
                    # Categorize severity
                    severity_category = "low"
                    if severity >= 0.8:
                        severity_category = "critical"
                    elif severity >= 0.6:
                        severity_category = "high"
                    elif severity >= 0.4:
                        severity_category = "medium"
                    
                    summary[week_key]["conflicts"]["by_severity"][severity_category] += 1
                
                # Update anomaly stats if this was an anomaly intervention
                if intervention_type == "anomaly_halt" and "anomaly_score" in latest:
                    anomaly_score = latest["anomaly_score"]
                    
                    summary[week_key]["anomalies"]["total"] += 1
                    summary[week_key]["strategies"][strategy]["anomalies"] += 1
                    
                    # Categorize anomaly score
                    score_category = "low"
                    if anomaly_score >= 0.8:
                        score_category = "critical"
                    elif anomaly_score >= 0.6:
                        score_category = "high"
                    elif anomaly_score >= 0.4:
                        score_category = "medium"
                    
                    summary[week_key]["anomalies"]["by_score"][score_category] += 1
            
            # Save updated summary
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating governance summary: {e}")
    
    def is_specialized_for(self, context: Dict[str, Any]) -> bool:
        """Check if this agent is specialized for the given context
        
        Args:
            context (Dict[str, Any]): Trading context
            
        Returns:
            bool: True if agent is specialized for this context, False otherwise
        """
        # Governor specializes in conflict resolution and governance
        return "agent_proposals" in context or "anomaly_scores" in context