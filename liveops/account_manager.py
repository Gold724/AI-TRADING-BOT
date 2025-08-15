import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class AccountManager:
    """Account manager for managing multiple trading accounts.
    
    This class handles the management of multiple trading accounts across different
    brokers, including account configuration, status tracking, and restrictions.
    """
    
    def __init__(self, config_path: str = None, data_dir: str = "data"):
        """Initialize the account manager.
        
        Args:
            config_path (str, optional): Path to accounts config. Defaults to None.
            data_dir (str, optional): Directory for data files. Defaults to "data".
        """
        self.logger = logging.getLogger("trae.account_manager")
        self.data_dir = data_dir
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize accounts
        self.accounts = {}
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.config = json.load(f)
                    
                    # Initialize accounts from config
                    if "accounts" in self.config:
                        for account_config in self.config["accounts"]:
                            account_id = account_config.get("account_id")
                            if account_id:
                                self.accounts[account_id] = account_config
            except Exception as e:
                self.logger.error(f"Error loading account manager config: {e}")
        
        # Load accounts from data file if it exists
        accounts_file = os.path.join(data_dir, "accounts.json")
        if os.path.exists(accounts_file):
            try:
                with open(accounts_file, "r") as f:
                    stored_accounts = json.load(f)
                    
                    # Update accounts with stored data
                    for account_id, account_data in stored_accounts.items():
                        if account_id in self.accounts:
                            # Update existing account with stored data
                            self.accounts[account_id].update(account_data)
                        else:
                            # Add new account from stored data
                            self.accounts[account_id] = account_data
            except Exception as e:
                self.logger.error(f"Error loading accounts data: {e}")
        
        # Initialize account status
        for account_id in self.accounts:
            if "status" not in self.accounts[account_id]:
                self.accounts[account_id]["status"] = "active"
            if "open_positions" not in self.accounts[account_id]:
                self.accounts[account_id]["open_positions"] = []
            if "current_daily_loss" not in self.accounts[account_id]:
                self.accounts[account_id]["current_daily_loss"] = 0.0
        
        # Save accounts to data file
        self._save_accounts()
        
        self.logger.info(f"Account manager initialized with {len(self.accounts)} accounts")
    
    def get_active_accounts(self) -> List[Dict[str, Any]]:
        """Get all active accounts.
        
        Returns:
            List[Dict[str, Any]]: List of active accounts
        """
        active_accounts = []
        for account_id, account in self.accounts.items():
            if account.get("status") == "active":
                # Create a copy of the account with its ID
                account_copy = account.copy()
                account_copy["account_id"] = account_id
                active_accounts.append(account_copy)
        
        return active_accounts
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID.
        
        Args:
            account_id (str): Account ID
            
        Returns:
            Optional[Dict[str, Any]]: Account data or None if not found
        """
        if account_id in self.accounts:
            account_copy = self.accounts[account_id].copy()
            account_copy["account_id"] = account_id
            return account_copy
        return None
    
    def update_account_status(self, account_id: str, status: str) -> bool:
        """Update account status.
        
        Args:
            account_id (str): Account ID
            status (str): New status ("active", "inactive", "locked")
            
        Returns:
            bool: True if successful, False otherwise
        """
        if account_id not in self.accounts:
            self.logger.warning(f"Account {account_id} not found")
            return False
        
        # Update status
        self.accounts[account_id]["status"] = status
        
        # Log the status change
        self.logger.info(f"Account {account_id} status changed to {status}")
        
        # Save accounts to data file
        self._save_accounts()
        
        return True
    
    def update_account_balance(self, account_id: str, balance: float) -> bool:
        """Update account balance.
        
        Args:
            account_id (str): Account ID
            balance (float): New balance
            
        Returns:
            bool: True if successful, False otherwise
        """
        if account_id not in self.accounts:
            self.logger.warning(f"Account {account_id} not found")
            return False
        
        # Get previous balance
        previous_balance = self.accounts[account_id].get("balance", 0.0)
        
        # Update balance
        self.accounts[account_id]["balance"] = balance
        
        # Calculate profit/loss
        profit_loss = balance - previous_balance
        
        # Update daily loss if negative
        if profit_loss < 0:
            current_daily_loss = self.accounts[account_id].get("current_daily_loss", 0.0)
            self.accounts[account_id]["current_daily_loss"] = current_daily_loss + abs(profit_loss)
            
            # Check if daily loss limit is reached
            daily_loss_limit = self.accounts[account_id].get("daily_loss_limit", float('inf'))
            if self.accounts[account_id]["current_daily_loss"] >= daily_loss_limit:
                # Lock account if daily loss limit is reached
                self.accounts[account_id]["status"] = "locked"
                self.logger.warning(f"Account {account_id} locked due to daily loss limit reached")
        
        # Log the balance update
        self.logger.info(f"Account {account_id} balance updated to {balance} (P/L: {profit_loss})")
        
        # Save accounts to data file
        self._save_accounts()
        
        return True
    
    def update_open_positions(self, account_id: str, positions: List[Dict[str, Any]]) -> bool:
        """Update account open positions.
        
        Args:
            account_id (str): Account ID
            positions (List[Dict[str, Any]]): List of open positions
            
        Returns:
            bool: True if successful, False otherwise
        """
        if account_id not in self.accounts:
            self.logger.warning(f"Account {account_id} not found")
            return False
        
        # Update open positions
        self.accounts[account_id]["open_positions"] = positions
        
        # Log the positions update
        self.logger.info(f"Account {account_id} open positions updated ({len(positions)} positions)")
        
        # Save accounts to data file
        self._save_accounts()
        
        return True
    
    def add_account(self, account_id: str, broker: str, account_config: Dict[str, Any]) -> bool:
        """Add a new account.
        
        Args:
            account_id (str): Account ID
            broker (str): Broker name
            account_config (Dict[str, Any]): Account configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        if account_id in self.accounts:
            self.logger.warning(f"Account {account_id} already exists")
            return False
        
        # Create new account
        account = account_config.copy()
        account["broker"] = broker
        account["status"] = "active"
        account["open_positions"] = []
        account["current_daily_loss"] = 0.0
        account["created_at"] = datetime.now().isoformat()
        
        # Add account
        self.accounts[account_id] = account
        
        # Log the account addition
        self.logger.info(f"Account {account_id} added for broker {broker}")
        
        # Save accounts to data file
        self._save_accounts()
        
        return True
    
    def remove_account(self, account_id: str) -> bool:
        """Remove an account.
        
        Args:
            account_id (str): Account ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if account_id not in self.accounts:
            self.logger.warning(f"Account {account_id} not found")
            return False
        
        # Remove account
        del self.accounts[account_id]
        
        # Log the account removal
        self.logger.info(f"Account {account_id} removed")
        
        # Save accounts to data file
        self._save_accounts()
        
        return True
    
    def reset_daily_loss(self, account_id: str = None) -> bool:
        """Reset daily loss for an account or all accounts.
        
        Args:
            account_id (str, optional): Account ID. Defaults to None (all accounts).
            
        Returns:
            bool: True if successful, False otherwise
        """
        if account_id:
            # Reset daily loss for specific account
            if account_id not in self.accounts:
                self.logger.warning(f"Account {account_id} not found")
                return False
            
            self.accounts[account_id]["current_daily_loss"] = 0.0
            
            # Unlock account if it was locked due to daily loss limit
            if self.accounts[account_id]["status"] == "locked":
                self.accounts[account_id]["status"] = "active"
            
            self.logger.info(f"Daily loss reset for account {account_id}")
        else:
            # Reset daily loss for all accounts
            for acc_id in self.accounts:
                self.accounts[acc_id]["current_daily_loss"] = 0.0
                
                # Unlock account if it was locked due to daily loss limit
                if self.accounts[acc_id]["status"] == "locked":
                    self.accounts[acc_id]["status"] = "active"
            
            self.logger.info("Daily loss reset for all accounts")
        
        # Save accounts to data file
        self._save_accounts()
        
        return True
    
    def _save_accounts(self) -> None:
        """Save accounts to data file."""
        try:
            accounts_file = os.path.join(self.data_dir, "accounts.json")
            
            with open(accounts_file, "w") as f:
                json.dump(self.accounts, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving accounts data: {e}")