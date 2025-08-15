# governance_engine.py

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
import yaml

class GovernanceRole(Enum):
    """Enum for different governance roles"""
    STRATEGIST = "strategist"
    RISK_GOVERNOR = "risk_governor"
    PERFORMANCE_AUDITOR = "performance_auditor"
    PHASE_ORACLE = "phase_oracle"

class VoteType(Enum):
    """Enum for different types of votes"""
    STRATEGY_CHANGE = "strategy_change"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    PHASE_TRANSITION = "phase_transition"
    EMERGENCY_OVERRIDE = "emergency_override"
    ROLLBACK = "rollback"

class VoteStatus(Enum):
    """Enum for vote status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class GovernanceEngine:
    """Governance Engine for TRAE Phase 9
    
    This class implements the governance and sovereignty layer for TRAE,
    enabling role-based delegation, voting on strategies, tracking rule changes,
    and protecting critical protocol elements.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Governance Engine
        
        Args:
            config (Dict[str, Any], optional): Configuration for the engine. Defaults to None.
        """
        # Create logs directory and governance subdirectory if they don't exist
        os.makedirs("logs/governance", exist_ok=True)
        os.makedirs("config_backups", exist_ok=True)
        
        # Set up logging for governance
        self.logger = logging.getLogger('governance_engine')
        file_handler = logging.FileHandler('logs/governance/governance.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Set default configuration
        self.config = {
            "enabled": True,
            "enable_voting": True,
            "roles_enabled": True,
            "safeguard_core": True,
            "quorum_threshold": 3,
            "votes_file": "logs/governance/votes.json",
            "role_actions_file": "logs/governance/role_actions.json",
            "protocol_changes_file": "logs/governance/protocol_changes.json",
            "immutable_configs": [
                "config/core_security.yml",
                "config/risk_limits.yml"
            ],
            "emergency_loss_threshold": 0.05,  # 5% loss triggers emergency mode
            "backup_frequency_days": 7  # Weekly backups
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Initialize roles
        self.roles = {
            GovernanceRole.STRATEGIST: self._initialize_role(GovernanceRole.STRATEGIST),
            GovernanceRole.RISK_GOVERNOR: self._initialize_role(GovernanceRole.RISK_GOVERNOR),
            GovernanceRole.PERFORMANCE_AUDITOR: self._initialize_role(GovernanceRole.PERFORMANCE_AUDITOR),
            GovernanceRole.PHASE_ORACLE: self._initialize_role(GovernanceRole.PHASE_ORACLE)
        }
        
        # Initialize governance log files if they don't exist
        self._initialize_log_files()
        
        # Create initial config backup
        self._create_config_backup()
        
        self.logger.info("Initialized governance engine")
    
    def _initialize_role(self, role: GovernanceRole) -> Dict[str, Any]:
        """Initialize a governance role with its properties
        
        Args:
            role (GovernanceRole): The role to initialize
            
        Returns:
            Dict[str, Any]: The initialized role properties
        """
        role_config = {
            "name": role.value,
            "active": True,
            "permissions": [],
            "last_action": None,
            "action_count": 0
        }
        
        # Set role-specific permissions
        if role == GovernanceRole.STRATEGIST:
            role_config["permissions"] = ["propose_strategy", "adjust_parameters"]
        elif role == GovernanceRole.RISK_GOVERNOR:
            role_config["permissions"] = ["veto_trade", "set_risk_limits", "emergency_override"]
        elif role == GovernanceRole.PERFORMANCE_AUDITOR:
            role_config["permissions"] = ["review_trades", "log_errors", "propose_improvements"]
        elif role == GovernanceRole.PHASE_ORACLE:
            role_config["permissions"] = ["initiate_phase_transition", "rollback_phase"]
        
        return role_config
    
    def _initialize_log_files(self) -> None:
        """Initialize governance log files if they don't exist"""
        # Votes log
        if not os.path.exists(self.config["votes_file"]):
            with open(self.config["votes_file"], "w") as f:
                json.dump({
                    "total_votes": 0,
                    "approved_votes": 0,
                    "rejected_votes": 0,
                    "votes": []
                }, f, indent=4)
        
        # Role actions log
        if not os.path.exists(self.config["role_actions_file"]):
            with open(self.config["role_actions_file"], "w") as f:
                json.dump({
                    "total_actions": 0,
                    "actions_by_role": {
                        role.value: 0 for role in GovernanceRole
                    },
                    "actions": []
                }, f, indent=4)
        
        # Protocol changes log
        if not os.path.exists(self.config["protocol_changes_file"]):
            with open(self.config["protocol_changes_file"], "w") as f:
                json.dump({
                    "total_changes": 0,
                    "changes": []
                }, f, indent=4)
    
    def _create_config_backup(self) -> None:
        """Create a backup of critical configuration files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"config_backups/{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup all config files
            if os.path.exists("config"):
                for root, _, files in os.walk("config"):
                    for file in files:
                        if file.endswith(".yml") or file.endswith(".json"):
                            src_path = os.path.join(root, file)
                            rel_path = os.path.relpath(src_path, "config")
                            dst_path = os.path.join(backup_dir, rel_path)
                            
                            # Create subdirectories if needed
                            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                            
                            # Copy file
                            with open(src_path, "r") as src, open(dst_path, "w") as dst:
                                dst.write(src.read())
            
            self.logger.info(f"Created config backup at {backup_dir}")
            
            # Log the backup as a protocol change
            self.log_protocol_change({
                "type": "config_backup",
                "backup_path": backup_dir,
                "reason": "Scheduled backup"
            })
            
        except Exception as e:
            self.logger.error(f"Error creating config backup: {e}")
    
    def initiate_vote(self, vote_type: VoteType, proposal: Dict[str, Any], 
                      initiator_role: GovernanceRole) -> str:
        """Initiate a new governance vote
        
        Args:
            vote_type (VoteType): The type of vote
            proposal (Dict[str, Any]): The proposal details
            initiator_role (GovernanceRole): The role initiating the vote
            
        Returns:
            str: The vote ID
        """
        if not self.config["enable_voting"]:
            self.logger.warning("Voting is disabled in configuration")
            return None
        
        try:
            # Generate vote ID
            vote_id = f"{vote_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create vote object
            vote = {
                "id": vote_id,
                "type": vote_type.value,
                "proposal": proposal,
                "initiator": initiator_role.value,
                "status": VoteStatus.PENDING.value,
                "created_at": datetime.now().isoformat(),
                "votes": {
                    initiator_role.value: True  # Initiator automatically votes yes
                },
                "quorum_required": self._get_quorum_requirement(vote_type),
                "result": None,
                "executed_at": None,
                "reason": None
            }
            
            # Log the vote
            self._log_vote(vote)
            
            # Log the role action
            self.log_role_action(initiator_role, "initiate_vote", {
                "vote_id": vote_id,
                "vote_type": vote_type.value
            })
            
            self.logger.info(f"Initiated {vote_type.value} vote with ID {vote_id}")
            
            # Check if emergency override
            if vote_type == VoteType.EMERGENCY_OVERRIDE and self._is_emergency_condition():
                self.logger.warning("Emergency condition detected, auto-approving vote")
                self.cast_vote(vote_id, GovernanceRole.RISK_GOVERNOR, True, "Emergency auto-approval")
                self.execute_vote(vote_id)
            
            return vote_id
            
        except Exception as e:
            self.logger.error(f"Error initiating vote: {e}")
            return None
    
    def cast_vote(self, vote_id: str, role: GovernanceRole, 
                  approve: bool, reason: str = None) -> bool:
        """Cast a vote on a governance proposal
        
        Args:
            vote_id (str): The vote ID
            role (GovernanceRole): The role casting the vote
            approve (bool): Whether to approve the proposal
            reason (str, optional): Reason for the vote. Defaults to None.
            
        Returns:
            bool: Whether the vote was successfully cast
        """
        try:
            # Load current votes
            votes_data = self._load_json_file(self.config["votes_file"])
            
            # Find the vote
            vote_found = False
            for vote in votes_data["votes"]:
                if vote["id"] == vote_id:
                    # Check if vote is still pending
                    if vote["status"] != VoteStatus.PENDING.value:
                        self.logger.warning(f"Vote {vote_id} is not pending (status: {vote['status']})")
                        return False
                    
                    # Cast the vote
                    vote["votes"][role.value] = approve
                    vote_found = True
                    
                    # Check if quorum is reached
                    votes_cast = len(vote["votes"])
                    approvals = sum(1 for v in vote["votes"].values() if v)
                    
                    if votes_cast >= vote["quorum_required"]:
                        # Determine result
                        if approvals >= vote["quorum_required"]:
                            vote["status"] = VoteStatus.APPROVED.value
                            vote["result"] = "approved"
                            votes_data["approved_votes"] += 1
                        else:
                            vote["status"] = VoteStatus.REJECTED.value
                            vote["result"] = "rejected"
                            votes_data["rejected_votes"] += 1
                        
                        vote["executed_at"] = datetime.now().isoformat()
                    
                    break
            
            if not vote_found:
                self.logger.warning(f"Vote {vote_id} not found")
                return False
            
            # Save updated votes
            with open(self.config["votes_file"], "w") as f:
                json.dump(votes_data, f, indent=4)
            
            # Log the role action
            self.log_role_action(role, "cast_vote", {
                "vote_id": vote_id,
                "approve": approve,
                "reason": reason
            })
            
            self.logger.info(f"Role {role.value} cast vote ({approve}) on {vote_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error casting vote: {e}")
            return False
    
    def execute_vote(self, vote_id: str) -> bool:
        """Execute an approved vote
        
        Args:
            vote_id (str): The vote ID
            
        Returns:
            bool: Whether the vote was successfully executed
        """
        try:
            # Load current votes
            votes_data = self._load_json_file(self.config["votes_file"])
            
            # Find the vote
            vote_found = False
            vote_to_execute = None
            
            for vote in votes_data["votes"]:
                if vote["id"] == vote_id:
                    vote_found = True
                    vote_to_execute = vote
                    
                    # Check if vote is approved
                    if vote["status"] != VoteStatus.APPROVED.value:
                        self.logger.warning(f"Vote {vote_id} is not approved (status: {vote['status']})")
                        return False
                    
                    break
            
            if not vote_found or not vote_to_execute:
                self.logger.warning(f"Vote {vote_id} not found")
                return False
            
            # Execute based on vote type
            vote_type = vote_to_execute["type"]
            proposal = vote_to_execute["proposal"]
            
            if vote_type == VoteType.STRATEGY_CHANGE.value:
                success = self._execute_strategy_change(proposal)
            elif vote_type == VoteType.PARAMETER_ADJUSTMENT.value:
                success = self._execute_parameter_adjustment(proposal)
            elif vote_type == VoteType.PHASE_TRANSITION.value:
                success = self._execute_phase_transition(proposal)
            elif vote_type == VoteType.EMERGENCY_OVERRIDE.value:
                success = self._execute_emergency_override(proposal)
            elif vote_type == VoteType.ROLLBACK.value:
                success = self._execute_rollback(proposal)
            else:
                self.logger.warning(f"Unknown vote type: {vote_type}")
                success = False
            
            # Update vote status
            for vote in votes_data["votes"]:
                if vote["id"] == vote_id:
                    vote["executed"] = success
                    vote["executed_at"] = datetime.now().isoformat()
                    break
            
            # Save updated votes
            with open(self.config["votes_file"], "w") as f:
                json.dump(votes_data, f, indent=4)
            
            self.logger.info(f"Executed vote {vote_id} with result: {success}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing vote: {e}")
            return False
    
    def log_role_action(self, role: GovernanceRole, action: str, 
                        details: Dict[str, Any] = None) -> bool:
        """Log an action taken by a governance role
        
        Args:
            role (GovernanceRole): The role taking the action
            action (str): The action taken
            details (Dict[str, Any], optional): Additional details. Defaults to None.
            
        Returns:
            bool: Whether the action was successfully logged
        """
        try:
            # Load current actions
            actions_data = self._load_json_file(self.config["role_actions_file"])
            
            # Create action entry
            action_entry = {
                "role": role.value,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
            
            # Update counts
            actions_data["total_actions"] += 1
            actions_data["actions_by_role"][role.value] += 1
            
            # Add action to log
            actions_data["actions"].append(action_entry)
            
            # Save updated actions
            with open(self.config["role_actions_file"], "w") as f:
                json.dump(actions_data, f, indent=4)
            
            # Update role's last action
            self.roles[role]["last_action"] = datetime.now().isoformat()
            self.roles[role]["action_count"] += 1
            
            self.logger.info(f"Logged {action} by {role.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging role action: {e}")
            return False
    
    def log_protocol_change(self, change: Dict[str, Any]) -> bool:
        """Log a change to the protocol
        
        Args:
            change (Dict[str, Any]): Details of the change
            
        Returns:
            bool: Whether the change was successfully logged
        """
        try:
            # Load current changes
            changes_data = self._load_json_file(self.config["protocol_changes_file"])
            
            # Create change entry
            change_entry = {
                "timestamp": datetime.now().isoformat(),
                **change
            }
            
            # Update count
            changes_data["total_changes"] += 1
            
            # Add change to log
            changes_data["changes"].append(change_entry)
            
            # Save updated changes
            with open(self.config["protocol_changes_file"], "w") as f:
                json.dump(changes_data, f, indent=4)
            
            self.logger.info(f"Logged protocol change: {change.get('type', 'unknown')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging protocol change: {e}")
            return False
    
    def is_config_immutable(self, config_path: str) -> bool:
        """Check if a configuration file is marked as immutable
        
        Args:
            config_path (str): Path to the configuration file
            
        Returns:
            bool: Whether the configuration is immutable
        """
        if not self.config["safeguard_core"]:
            return False
        
        return config_path in self.config["immutable_configs"]
    
    def can_modify_config(self, config_path: str, role: GovernanceRole = None) -> bool:
        """Check if a configuration file can be modified
        
        Args:
            config_path (str): Path to the configuration file
            role (GovernanceRole, optional): The role attempting modification. Defaults to None.
            
        Returns:
            bool: Whether the configuration can be modified
        """
        # If safeguarding is disabled, allow all modifications
        if not self.config["safeguard_core"]:
            return True
        
        # Check if config is immutable
        if self.is_config_immutable(config_path):
            # Only allow modification if there's an approved vote
            # This is a simplified check - in a real system, you'd check for a specific vote
            return False
        
        return True
    
    def _get_quorum_requirement(self, vote_type: VoteType) -> int:
        """Get the quorum requirement for a vote type
        
        Args:
            vote_type (VoteType): The type of vote
            
        Returns:
            int: The quorum requirement
        """
        if vote_type == VoteType.PHASE_TRANSITION:
            # Phase transitions require PhaseOracle + 1 role
            return 2
        elif vote_type == VoteType.EMERGENCY_OVERRIDE:
            # Emergency overrides require only RiskGovernor
            return 1
        else:
            # Default quorum from config
            return self.config["quorum_threshold"]
    
    def _is_emergency_condition(self) -> bool:
        """Check if emergency conditions are met
        
        Returns:
            bool: Whether emergency conditions are met
        """
        # In a real implementation, this would check actual trading metrics
        # For now, we'll just return False
        return False
    
    def _log_vote(self, vote: Dict[str, Any]) -> None:
        """Log a vote to the votes file
        
        Args:
            vote (Dict[str, Any]): The vote to log
        """
        try:
            # Load current votes
            votes_data = self._load_json_file(self.config["votes_file"])
            
            # Update count
            votes_data["total_votes"] += 1
            
            # Add vote to log
            votes_data["votes"].append(vote)
            
            # Save updated votes
            with open(self.config["votes_file"], "w") as f:
                json.dump(votes_data, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error logging vote: {e}")
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load a JSON file and return its contents as a dictionary
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            Dict: The file contents as a dictionary
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading JSON file {file_path}: {e}")
            return {}
    
    def _execute_strategy_change(self, proposal: Dict[str, Any]) -> bool:
        """Execute a strategy change proposal
        
        Args:
            proposal (Dict[str, Any]): The proposal details
            
        Returns:
            bool: Whether the change was successfully executed
        """
        try:
            # In a real implementation, this would modify strategy files or parameters
            strategy_name = proposal.get("strategy_name")
            changes = proposal.get("changes", {})
            
            self.logger.info(f"Executing strategy change for {strategy_name}")
            
            # Log the protocol change
            self.log_protocol_change({
                "type": "strategy_change",
                "strategy": strategy_name,
                "changes": changes
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing strategy change: {e}")
            return False
    
    def _execute_parameter_adjustment(self, proposal: Dict[str, Any]) -> bool:
        """Execute a parameter adjustment proposal
        
        Args:
            proposal (Dict[str, Any]): The proposal details
            
        Returns:
            bool: Whether the adjustment was successfully executed
        """
        try:
            # In a real implementation, this would modify configuration files
            config_file = proposal.get("config_file")
            parameters = proposal.get("parameters", {})
            
            # Check if config is immutable
            if self.is_config_immutable(config_file):
                self.logger.warning(f"Cannot modify immutable config {config_file}")
                return False
            
            self.logger.info(f"Executing parameter adjustment for {config_file}")
            
            # Log the protocol change
            self.log_protocol_change({
                "type": "parameter_adjustment",
                "config_file": config_file,
                "parameters": parameters
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing parameter adjustment: {e}")
            return False
    
    def _execute_phase_transition(self, proposal: Dict[str, Any]) -> bool:
        """Execute a phase transition proposal
        
        Args:
            proposal (Dict[str, Any]): The proposal details
            
        Returns:
            bool: Whether the transition was successfully executed
        """
        try:
            # In a real implementation, this would update the current phase
            new_phase = proposal.get("new_phase")
            reason = proposal.get("reason")
            
            self.logger.info(f"Executing phase transition to {new_phase}")
            
            # Log the protocol change
            self.log_protocol_change({
                "type": "phase_transition",
                "new_phase": new_phase,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing phase transition: {e}")
            return False
    
    def _execute_emergency_override(self, proposal: Dict[str, Any]) -> bool:
        """Execute an emergency override proposal
        
        Args:
            proposal (Dict[str, Any]): The proposal details
            
        Returns:
            bool: Whether the override was successfully executed
        """
        try:
            # In a real implementation, this would implement emergency measures
            action = proposal.get("action")
            reason = proposal.get("reason")
            
            self.logger.warning(f"Executing emergency override: {action}")
            
            # Log the protocol change
            self.log_protocol_change({
                "type": "emergency_override",
                "action": action,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing emergency override: {e}")
            return False
    
    def _execute_rollback(self, proposal: Dict[str, Any]) -> bool:
        """Execute a rollback proposal
        
        Args:
            proposal (Dict[str, Any]): The proposal details
            
        Returns:
            bool: Whether the rollback was successfully executed
        """
        try:
            # In a real implementation, this would restore from a backup
            backup_path = proposal.get("backup_path")
            reason = proposal.get("reason")
            
            self.logger.warning(f"Executing rollback to {backup_path}")
            
            # Log the protocol change
            self.log_protocol_change({
                "type": "rollback",
                "backup_path": backup_path,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing rollback: {e}")
            return False
    
    def check_trade_requires_approval(self, context: Dict[str, Any]) -> bool:
        """Check if a trade requires governance approval
        
        Args:
            context (Dict[str, Any]): The trading context
            
        Returns:
            bool: Whether the trade requires approval
        """
        try:
            # Extract relevant information from context
            strategy = context.get("strategy", "unknown")
            confidence = context.get("confidence", 0)
            position_size = context.get("position_size", 0)
            
            # Check if strategy is in high-risk list
            if strategy in self.config.get("high_risk_strategies", ["experimental", "high_frequency"]):
                self.logger.info(f"Trade requires approval: high-risk strategy {strategy}")
                return True
            
            # Check if position size exceeds threshold
            position_threshold = self.config.get("position_size_threshold", 0.05)
            if position_size > position_threshold:
                self.logger.info(f"Trade requires approval: position size {position_size} exceeds threshold {position_threshold}")
                return True
            
            # Check if confidence is below threshold
            confidence_threshold = self.config.get("confidence_threshold", 75)
            if confidence < confidence_threshold:
                self.logger.info(f"Trade requires approval: confidence {confidence} below threshold {confidence_threshold}")
                return True
            
            # Check if strategy is not in whitelist
            strategy_whitelist = self.config.get("strategy_whitelist", [])
            if strategy_whitelist and strategy not in strategy_whitelist:
                self.logger.info(f"Trade requires approval: strategy {strategy} not in whitelist")
                return True
            
            # No approval required
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if trade requires approval: {e}")
            # Default to requiring approval on error
            return True
    
    def initiate_vote(self, vote_type: VoteType, description: str, context: Dict[str, Any], proposed_by: GovernanceRole) -> str:
        """Initiate a vote for governance decision
        
        Args:
            vote_type (VoteType): The type of vote
            description (str): Description of the vote
            context (Dict[str, Any]): The context for the vote
            proposed_by (GovernanceRole): The role proposing the vote
            
        Returns:
            str: The vote ID
        """
        try:
            # Generate vote ID
            vote_id = f"{vote_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{proposed_by.value}"
            
            # Create vote object
            vote = {
                "id": vote_id,
                "type": vote_type.value,
                "description": description,
                "context": context,
                "proposed_by": proposed_by.value,
                "status": VoteStatus.PENDING.value,
                "created_at": datetime.now().isoformat(),
                "votes": {
                    proposed_by.value: True  # Proposer automatically votes yes
                },
                "decision": None,
                "quorum_required": self._get_quorum_requirement(vote_type),
                "roles_voted": [proposed_by.value]
            }
            
            # Load current votes
            votes_data = self._load_json_file(self.config["votes_file"])
            
            # Add vote to log
            if "votes" not in votes_data:
                votes_data["votes"] = []
            votes_data["votes"].append(vote)
            
            # Update count
            if "total_votes" not in votes_data:
                votes_data["total_votes"] = 0
            votes_data["total_votes"] += 1
            
            # Save updated votes
            with open(self.config["votes_file"], "w") as f:
                json.dump(votes_data, f, indent=4)
            
            # Log the role action
            self.log_role_action(proposed_by, "initiate_vote", {
                "vote_id": vote_id,
                "vote_type": vote_type.value,
                "description": description
            })
            
            self.logger.info(f"Initiated {vote_type.value} vote with ID {vote_id}")
            
            # Auto-cast votes from other roles based on context
            self._auto_cast_votes(vote_id, vote_type, context)
            
            return vote_id
            
        except Exception as e:
            self.logger.error(f"Error initiating vote: {e}")
            return None
    
    def check_vote_status(self, vote_id: str) -> Dict[str, Any]:
        """Check the status of a vote
        
        Args:
            vote_id (str): The vote ID
            
        Returns:
            Dict[str, Any]: The vote status
        """
        try:
            # Load current votes
            votes_data = self._load_json_file(self.config["votes_file"])
            
            # Find the vote
            for vote in votes_data.get("votes", []):
                if vote["id"] == vote_id:
                    # Return vote status
                    return {
                        "status": vote["status"],
                        "roles_voted": vote.get("roles_voted", []),
                        "decision": vote.get("decision", {})
                    }
            
            # Vote not found
            return {
                "status": "not_found",
                "roles_voted": [],
                "decision": {}
            }
            
        except Exception as e:
            self.logger.error(f"Error checking vote status: {e}")
            return {
                "status": "error",
                "roles_voted": [],
                "decision": {}
            }
    
    def assess_risk(self, decision: Dict[str, Any], context: Dict[str, Any], role: GovernanceRole) -> Dict[str, Any]:
        """Assess the risk of a trading decision
        
        Args:
            decision (Dict[str, Any]): The trading decision
            context (Dict[str, Any]): The trading context
            role (GovernanceRole): The role assessing risk
            
        Returns:
            Dict[str, Any]: The risk assessment
        """
        try:
            # Extract relevant information
            action = decision.get("action", "hold")
            confidence = decision.get("confidence", 0)
            market_data = context.get("market_data", {})
            account_info = context.get("account_info", {})
            
            # Calculate risk score (1-10 scale)
            risk_score = 5  # Default medium risk
            
            # Adjust based on action
            if action == "buy":
                risk_score += 2
            elif action == "sell":
                risk_score += 1
            
            # Adjust based on confidence
            if confidence < 50:
                risk_score += 2
            elif confidence > 80:
                risk_score -= 1
            
            # Adjust based on market volatility if available
            volatility = market_data.get("volatility", 0)
            if volatility > 0.05:  # 5% volatility
                risk_score += 2
            
            # Adjust based on account balance vs position size
            balance = account_info.get("balance", 0)
            position_size = account_info.get("position_size", 0)
            if balance > 0 and position_size > 0:
                position_ratio = position_size / balance
                if position_ratio > 0.2:  # 20% of account
                    risk_score += 2
            
            # Check against risk thresholds
            max_risk_score = self.config.get("max_risk_score", 7)
            approved = risk_score <= max_risk_score
            
            # Log the risk assessment
            self.log_role_action(role, "risk_assessment", {
                "action": action,
                "risk_score": risk_score,
                "approved": approved,
                "max_risk_score": max_risk_score
            })
            
            return {
                "approved": approved,
                "risk_score": risk_score,
                "reason": f"Risk score {risk_score}/{max_risk_score}" + (" - Too risky" if not approved else "")
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing risk: {e}")
            return {
                "approved": False,
                "risk_score": 10,  # Maximum risk on error
                "reason": f"Error in risk assessment: {e}"
            }
    
    def _auto_cast_votes(self, vote_id: str, vote_type: VoteType, context: Dict[str, Any]) -> None:
        """Automatically cast votes from other roles based on context
        
        Args:
            vote_id (str): The vote ID
            vote_type (VoteType): The type of vote
            context (Dict[str, Any]): The context for the vote
        """
        try:
            # For trade approvals, auto-cast votes based on role responsibilities
            if vote_type == VoteType.STRATEGY_CHANGE:
                # Risk Governor auto-votes based on risk assessment
                decision = context.get("decision", {})
                risk_assessment = self.assess_risk(decision, context, GovernanceRole.RISK_GOVERNOR)
                
                # Cast vote based on risk assessment
                if risk_assessment["approved"]:
                    self.cast_vote(vote_id, GovernanceRole.RISK_GOVERNOR, True, "Acceptable risk level")
                else:
                    self.cast_vote(vote_id, GovernanceRole.RISK_GOVERNOR, False, risk_assessment["reason"])
                
                # Performance Auditor auto-votes based on strategy performance
                strategy = context.get("strategy", "unknown")
                # In a real implementation, this would check actual performance metrics
                # For now, we'll just approve known strategies
                if strategy in ["momentum", "mean_reversion", "breakout"]:
                    self.cast_vote(vote_id, GovernanceRole.PERFORMANCE_AUDITOR, True, "Strategy has good performance history")
            
            # For phase transitions, PhaseOracle always votes
            elif vote_type == VoteType.PHASE_TRANSITION:
                # In a real implementation, this would evaluate system readiness
                self.cast_vote(vote_id, GovernanceRole.PHASE_ORACLE, True, "System ready for phase transition")
            
        except Exception as e:
            self.logger.error(f"Error auto-casting votes: {e}")