# 🚀 Scaling Operations Guide - AI Trading Sentinel

## Step 5: Add Multiple Trading Accounts for Production Scaling

### 🎯 Overview
Scale the AI Trading Sentinel to handle multiple trading accounts, competitions, and brokers simultaneously with:
- Multi-account architecture
- Parallel execution management
- Resource optimization
- Performance monitoring
- Risk distribution
- Automated account management

### 🏗️ Multi-Account Architecture

#### 1. Account Configuration Structure

```bash
# Create multi-account configuration
cat > multi_account_config.py << 'EOF'
#!/usr/bin/env python3
import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class AccountType(Enum):
    LIVE = "live"
    DEMO = "demo"
    COMPETITION = "competition"
    PAPER = "paper"

class BrokerType(Enum):
    BULENOX = "bulenox"
    BINANCE = "binance"
    BYBIT = "bybit"
    # Add more brokers as needed

@dataclass
class TradingAccount:
    account_id: str
    account_name: str
    broker: BrokerType
    account_type: AccountType
    credentials: Dict[str, str]
    initial_balance: float
    max_risk_per_trade: float
    max_daily_trades: int
    max_drawdown_percent: float
    enabled: bool = True
    priority: int = 1  # 1=highest, 5=lowest
    
    def __post_init__(self):
        self.validate_config()
    
    def validate_config(self):
        """Validate account configuration"""
        required_fields = ['account_id', 'account_name', 'broker', 'credentials']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Missing required field: {field}")
        
        if self.max_risk_per_trade <= 0 or self.max_risk_per_trade > 0.1:
            raise ValueError("Risk per trade must be between 0 and 10%")
        
        if self.max_drawdown_percent <= 0 or self.max_drawdown_percent > 0.2:
            raise ValueError("Max drawdown must be between 0 and 20%")

class MultiAccountManager:
    def __init__(self, config_file: str = "accounts_config.json"):
        self.config_file = config_file
        self.accounts: Dict[str, TradingAccount] = {}
        self.load_accounts()
    
    def load_accounts(self):
        """Load account configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for account_data in data.get('accounts', []):
                    account = TradingAccount(
                        account_id=account_data['account_id'],
                        account_name=account_data['account_name'],
                        broker=BrokerType(account_data['broker']),
                        account_type=AccountType(account_data['account_type']),
                        credentials=account_data['credentials'],
                        initial_balance=account_data['initial_balance'],
                        max_risk_per_trade=account_data['max_risk_per_trade'],
                        max_daily_trades=account_data['max_daily_trades'],
                        max_drawdown_percent=account_data['max_drawdown_percent'],
                        enabled=account_data.get('enabled', True),
                        priority=account_data.get('priority', 1)
                    )
                    self.accounts[account.account_id] = account
                    
            except Exception as e:
                print(f"Error loading accounts config: {e}")
                self.create_default_config()
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "accounts": [
                {
                    "account_id": "bulenox_main",
                    "account_name": "Bulenox Main Account",
                    "broker": "bulenox",
                    "account_type": "live",
                    "credentials": {
                        "username": "${BULENOX_USERNAME}",
                        "password": "${BULENOX_PASSWORD}"
                    },
                    "initial_balance": 10000.0,
                    "max_risk_per_trade": 0.02,
                    "max_daily_trades": 20,
                    "max_drawdown_percent": 0.05,
                    "enabled": True,
                    "priority": 1
                },
                {
                    "account_id": "bulenox_demo",
                    "account_name": "Bulenox Demo Account",
                    "broker": "bulenox",
                    "account_type": "demo",
                    "credentials": {
                        "username": "${BULENOX_DEMO_USERNAME}",
                        "password": "${BULENOX_DEMO_PASSWORD}"
                    },
                    "initial_balance": 50000.0,
                    "max_risk_per_trade": 0.05,
                    "max_daily_trades": 50,
                    "max_drawdown_percent": 0.1,
                    "enabled": True,
                    "priority": 2
                }
            ],
            "global_settings": {
                "max_concurrent_accounts": 3,
                "account_rotation_enabled": True,
                "risk_distribution_enabled": True,
                "performance_tracking_enabled": True
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"Created default configuration: {self.config_file}")
    
    def add_account(self, account: TradingAccount):
        """Add new trading account"""
        self.accounts[account.account_id] = account
        self.save_accounts()
    
    def remove_account(self, account_id: str):
        """Remove trading account"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            self.save_accounts()
    
    def get_active_accounts(self) -> List[TradingAccount]:
        """Get list of enabled accounts sorted by priority"""
        active = [acc for acc in self.accounts.values() if acc.enabled]
        return sorted(active, key=lambda x: x.priority)
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[TradingAccount]:
        """Get accounts by type"""
        return [acc for acc in self.accounts.values() if acc.account_type == account_type]
    
    def save_accounts(self):
        """Save accounts configuration to file"""
        data = {
            "accounts": [
                {
                    "account_id": acc.account_id,
                    "account_name": acc.account_name,
                    "broker": acc.broker.value,
                    "account_type": acc.account_type.value,
                    "credentials": acc.credentials,
                    "initial_balance": acc.initial_balance,
                    "max_risk_per_trade": acc.max_risk_per_trade,
                    "max_daily_trades": acc.max_daily_trades,
                    "max_drawdown_percent": acc.max_drawdown_percent,
                    "enabled": acc.enabled,
                    "priority": acc.priority
                }
                for acc in self.accounts.values()
            ]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

# Example usage
if __name__ == "__main__":
    manager = MultiAccountManager()
    
    # Add a competition account
    competition_account = TradingAccount(
        account_id="bulenox_comp_2024",
        account_name="Bulenox Competition 2024",
        broker=BrokerType.BULENOX,
        account_type=AccountType.COMPETITION,
        credentials={
            "username": "${BULENOX_COMP_USERNAME}",
            "password": "${BULENOX_COMP_PASSWORD}"
        },
        initial_balance=100000.0,
        max_risk_per_trade=0.1,  # Higher risk for competitions
        max_daily_trades=100,
        max_drawdown_percent=0.15,
        priority=1  # High priority for competitions
    )
    
    manager.add_account(competition_account)
    print(f"Active accounts: {len(manager.get_active_accounts())}")
EOF

chmod +x multi_account_config.py
```

#### 2. Parallel Execution Manager

```bash
cat > parallel_executor.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import concurrent.futures
import threading
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import psutil
from multi_account_config import MultiAccountManager, TradingAccount
from slack_notifier import SlackNotifier, AlertType

@dataclass
class ExecutionResult:
    account_id: str
    success: bool
    message: str
    execution_time: float
    timestamp: datetime
    data: Optional[Dict] = None

class ResourceMonitor:
    def __init__(self):
        self.max_cpu_percent = 80.0
        self.max_memory_percent = 85.0
        self.logger = logging.getLogger(__name__)
    
    def can_execute_more(self) -> bool:
        """Check if system can handle more parallel executions"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > self.max_cpu_percent:
            self.logger.warning(f"CPU usage too high: {cpu_percent:.1f}%")
            return False
        
        if memory_percent > self.max_memory_percent:
            self.logger.warning(f"Memory usage too high: {memory_percent:.1f}%")
            return False
        
        return True
    
    def get_optimal_workers(self, total_accounts: int) -> int:
        """Calculate optimal number of worker threads"""
        cpu_count = psutil.cpu_count()
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        
        # Conservative approach: 1 worker per 2 CPU cores, max based on memory
        max_workers_cpu = max(1, cpu_count // 2)
        max_workers_memory = max(1, int(available_memory_gb // 0.5))  # 500MB per worker
        
        optimal = min(max_workers_cpu, max_workers_memory, total_accounts)
        return max(1, optimal)

class ParallelExecutor:
    def __init__(self, max_workers: Optional[int] = None):
        self.account_manager = MultiAccountManager()
        self.resource_monitor = ResourceMonitor()
        self.slack = SlackNotifier()
        self.logger = self._setup_logging()
        
        active_accounts = self.account_manager.get_active_accounts()
        self.max_workers = max_workers or self.resource_monitor.get_optimal_workers(len(active_accounts))
        
        self.execution_results: Dict[str, List[ExecutionResult]] = {}
        self.account_locks: Dict[str, threading.Lock] = {}
        
        # Initialize locks for each account
        for account in active_accounts:
            self.account_locks[account.account_id] = threading.Lock()
    
    def _setup_logging(self):
        """Setup logging for parallel execution"""
        logger = logging.getLogger('ParallelExecutor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('parallel_execution.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def execute_on_account(self, account: TradingAccount, task_func: Callable, *args, **kwargs) -> ExecutionResult:
        """Execute task on specific account with proper locking"""
        start_time = time.time()
        
        # Acquire lock for this account
        with self.account_locks[account.account_id]:
            try:
                self.logger.info(f"Starting execution on account {account.account_id}")
                
                # Check resource availability
                if not self.resource_monitor.can_execute_more():
                    return ExecutionResult(
                        account_id=account.account_id,
                        success=False,
                        message="System resources insufficient",
                        execution_time=time.time() - start_time,
                        timestamp=datetime.now()
                    )
                
                # Execute the task
                result_data = task_func(account, *args, **kwargs)
                
                execution_time = time.time() - start_time
                result = ExecutionResult(
                    account_id=account.account_id,
                    success=True,
                    message="Execution completed successfully",
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    data=result_data
                )
                
                self.logger.info(f"Completed execution on account {account.account_id} in {execution_time:.2f}s")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Execution failed on account {account.account_id}: {str(e)}"
                self.logger.error(error_msg)
                
                # Send alert for critical failures
                self.slack.send_alert(
                    AlertType.SYSTEM,
                    f"Account execution failed: {account.account_name} - {str(e)}",
                    "danger"
                )
                
                return ExecutionResult(
                    account_id=account.account_id,
                    success=False,
                    message=error_msg,
                    execution_time=execution_time,
                    timestamp=datetime.now()
                )
    
    def execute_parallel(self, task_func: Callable, *args, **kwargs) -> Dict[str, ExecutionResult]:
        """Execute task on all active accounts in parallel"""
        active_accounts = self.account_manager.get_active_accounts()
        
        if not active_accounts:
            self.logger.warning("No active accounts found")
            return {}
        
        self.logger.info(f"Starting parallel execution on {len(active_accounts)} accounts with {self.max_workers} workers")
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks for each account
            future_to_account = {
                executor.submit(self.execute_on_account, account, task_func, *args, **kwargs): account
                for account in active_accounts
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per account
                    results[account.account_id] = result
                    
                    # Store result for history
                    if account.account_id not in self.execution_results:
                        self.execution_results[account.account_id] = []
                    self.execution_results[account.account_id].append(result)
                    
                except concurrent.futures.TimeoutError:
                    self.logger.error(f"Timeout executing on account {account.account_id}")
                    results[account.account_id] = ExecutionResult(
                        account_id=account.account_id,
                        success=False,
                        message="Execution timeout",
                        execution_time=300.0,
                        timestamp=datetime.now()
                    )
                except Exception as e:
                    self.logger.error(f"Unexpected error for account {account.account_id}: {e}")
                    results[account.account_id] = ExecutionResult(
                        account_id=account.account_id,
                        success=False,
                        message=f"Unexpected error: {str(e)}",
                        execution_time=0.0,
                        timestamp=datetime.now()
                    )
        
        # Send summary notification
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        self.slack.send_alert(
            AlertType.SYSTEM,
            f"Parallel execution completed: {successful}/{total} accounts successful",
            "good" if successful == total else "warning"
        )
        
        self.logger.info(f"Parallel execution completed: {successful}/{total} successful")
        return results
    
    def execute_by_priority(self, task_func: Callable, *args, **kwargs) -> Dict[str, ExecutionResult]:
        """Execute task on accounts in priority order (sequential)"""
        active_accounts = self.account_manager.get_active_accounts()  # Already sorted by priority
        results = {}
        
        for account in active_accounts:
            if not self.resource_monitor.can_execute_more():
                self.logger.warning("Stopping execution due to resource constraints")
                break
            
            result = self.execute_on_account(account, task_func, *args, **kwargs)
            results[account.account_id] = result
            
            # Store result for history
            if account.account_id not in self.execution_results:
                self.execution_results[account.account_id] = []
            self.execution_results[account.account_id].append(result)
            
            # Short delay between accounts
            time.sleep(1)
        
        return results
    
    def get_execution_summary(self) -> Dict:
        """Get summary of all executions"""
        summary = {
            'total_accounts': len(self.account_manager.get_active_accounts()),
            'accounts_with_results': len(self.execution_results),
            'total_executions': sum(len(results) for results in self.execution_results.values()),
            'success_rate': 0.0,
            'average_execution_time': 0.0,
            'account_summaries': {}
        }
        
        total_executions = 0
        successful_executions = 0
        total_time = 0.0
        
        for account_id, results in self.execution_results.items():
            account_successful = sum(1 for r in results if r.success)
            account_total = len(results)
            account_avg_time = sum(r.execution_time for r in results) / account_total if account_total > 0 else 0
            
            summary['account_summaries'][account_id] = {
                'total_executions': account_total,
                'successful_executions': account_successful,
                'success_rate': (account_successful / account_total * 100) if account_total > 0 else 0,
                'average_execution_time': account_avg_time,
                'last_execution': results[-1].timestamp.isoformat() if results else None
            }
            
            total_executions += account_total
            successful_executions += account_successful
            total_time += sum(r.execution_time for r in results)
        
        if total_executions > 0:
            summary['success_rate'] = (successful_executions / total_executions) * 100
            summary['average_execution_time'] = total_time / total_executions
        
        return summary

# Example trading task function
def sample_trading_task(account: TradingAccount, signal_data: Dict = None) -> Dict:
    """Sample trading task that can be executed on any account"""
    import random
    import time
    
    # Simulate some trading logic
    time.sleep(random.uniform(1, 3))  # Simulate variable execution time
    
    # Simulate trade result
    trade_result = {
        'symbol': 'EURUSD',
        'direction': random.choice(['BUY', 'SELL']),
        'amount': account.initial_balance * account.max_risk_per_trade,
        'success': random.choice([True, True, True, False]),  # 75% success rate
        'pnl': random.uniform(-50, 100)
    }
    
    return trade_result

# Test the parallel executor
if __name__ == "__main__":
    executor = ParallelExecutor()
    
    # Test parallel execution
    print("Testing parallel execution...")
    results = executor.execute_parallel(sample_trading_task)
    
    for account_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"{status} {account_id}: {result.message} ({result.execution_time:.2f}s)")
    
    # Print summary
    summary = executor.get_execution_summary()
    print(f"\nExecution Summary:")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Average Time: {summary['average_execution_time']:.2f}s")
EOF

chmod +x parallel_executor.py
```

#### 3. Account Performance Tracker

```bash
cat > account_performance.py << 'EOF'
#!/usr/bin/env python3
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from multi_account_config import MultiAccountManager, TradingAccount

@dataclass
class TradeRecord:
    account_id: str
    timestamp: datetime
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: Optional[float]
    status: str  # 'open', 'closed', 'cancelled'
    trade_id: str

@dataclass
class AccountMetrics:
    account_id: str
    period_start: datetime
    period_end: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    current_balance: float
    roi_percent: float

class PerformanceTracker:
    def __init__(self, db_path: str = "trading_performance.db"):
        self.db_path = db_path
        self.account_manager = MultiAccountManager()
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for performance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                pnl REAL,
                status TEXT NOT NULL,
                trade_id TEXT UNIQUE NOT NULL
            )
        """)
        
        # Create daily metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                date TEXT NOT NULL,
                trades_count INTEGER,
                total_pnl REAL,
                win_rate REAL,
                balance REAL,
                drawdown REAL,
                UNIQUE(account_id, date)
            )
        """)
        
        # Create account balances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                balance REAL NOT NULL,
                equity REAL,
                margin_used REAL,
                free_margin REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_trade(self, trade: TradeRecord):
        """Record a trade in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO trades 
                (account_id, timestamp, symbol, direction, entry_price, exit_price, quantity, pnl, status, trade_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.account_id,
                trade.timestamp.isoformat(),
                trade.symbol,
                trade.direction,
                trade.entry_price,
                trade.exit_price,
                trade.quantity,
                trade.pnl,
                trade.status,
                trade.trade_id
            ))
            conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Trade already exists: {trade.trade_id}")
        finally:
            conn.close()
    
    def update_account_balance(self, account_id: str, balance: float, equity: float = None, 
                             margin_used: float = None, free_margin: float = None):
        """Update account balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO account_balances (account_id, timestamp, balance, equity, margin_used, free_margin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            account_id,
            datetime.now().isoformat(),
            balance,
            equity or balance,
            margin_used or 0,
            free_margin or balance
        ))
        
        conn.commit()
        conn.close()
    
    def calculate_account_metrics(self, account_id: str, days: int = 30) -> AccountMetrics:
        """Calculate performance metrics for an account"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        
        # Get trades for the period
        trades_df = pd.read_sql_query("""
            SELECT * FROM trades 
            WHERE account_id = ? AND timestamp >= ? AND timestamp <= ? AND status = 'closed'
        """, conn, params=(account_id, start_date.isoformat(), end_date.isoformat()))
        
        # Get account info
        account = self.account_manager.accounts.get(account_id)
        initial_balance = account.initial_balance if account else 10000
        
        if trades_df.empty:
            return AccountMetrics(
                account_id=account_id,
                period_start=start_date,
                period_end=end_date,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                current_balance=initial_balance,
                roi_percent=0.0
            )
        
        # Calculate basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate drawdown
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        trades_df['running_max'] = trades_df['cumulative_pnl'].expanding().max()
        trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['running_max']
        max_drawdown = abs(trades_df['drawdown'].min()) if not trades_df.empty else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(trades_df) > 1:
            returns = trades_df['pnl'] / initial_balance
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        current_balance = initial_balance + total_pnl
        roi_percent = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
        
        conn.close()
        
        return AccountMetrics(
            account_id=account_id,
            period_start=start_date,
            period_end=end_date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            current_balance=current_balance,
            roi_percent=roi_percent
        )
    
    def get_all_account_metrics(self, days: int = 30) -> Dict[str, AccountMetrics]:
        """Get metrics for all accounts"""
        metrics = {}
        for account_id in self.account_manager.accounts.keys():
            metrics[account_id] = self.calculate_account_metrics(account_id, days)
        return metrics
    
    def generate_performance_report(self, days: int = 30) -> str:
        """Generate comprehensive performance report"""
        all_metrics = self.get_all_account_metrics(days)
        
        report = f"\n📊 PERFORMANCE REPORT - Last {days} Days\n"
        report += "=" * 50 + "\n\n"
        
        total_pnl = 0
        total_trades = 0
        
        for account_id, metrics in all_metrics.items():
            account = self.account_manager.accounts.get(account_id)
            account_name = account.account_name if account else account_id
            
            report += f"🏦 {account_name} ({account_id})\n"
            report += f"   Trades: {metrics.total_trades} | Win Rate: {metrics.win_rate:.1f}%\n"
            report += f"   P&L: ${metrics.total_pnl:.2f} | ROI: {metrics.roi_percent:.1f}%\n"
            report += f"   Balance: ${metrics.current_balance:.2f} | Max DD: ${metrics.max_drawdown:.2f}\n"
            report += f"   Profit Factor: {metrics.profit_factor:.2f} | Sharpe: {metrics.sharpe_ratio:.2f}\n\n"
            
            total_pnl += metrics.total_pnl
            total_trades += metrics.total_trades
        
        report += f"📈 PORTFOLIO SUMMARY\n"
        report += f"   Total P&L: ${total_pnl:.2f}\n"
        report += f"   Total Trades: {total_trades}\n"
        report += f"   Active Accounts: {len([m for m in all_metrics.values() if m.total_trades > 0])}\n"
        
        return report
    
    def export_to_csv(self, account_id: str = None, filename: str = None):
        """Export trading data to CSV"""
        conn = sqlite3.connect(self.db_path)
        
        if account_id:
            query = "SELECT * FROM trades WHERE account_id = ?"
            params = (account_id,)
            default_filename = f"trades_{account_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        else:
            query = "SELECT * FROM trades"
            params = ()
            default_filename = f"all_trades_{datetime.now().strftime('%Y%m%d')}.csv"
        
        df = pd.read_sql_query(query, conn, params=params)
        filename = filename or default_filename
        df.to_csv(filename, index=False)
        
        conn.close()
        print(f"Exported {len(df)} trades to {filename}")

# Example usage and testing
if __name__ == "__main__":
    tracker = PerformanceTracker()
    
    # Simulate some trades
    import random
    from datetime import datetime, timedelta
    
    accounts = ['bulenox_main', 'bulenox_demo']
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
    
    for i in range(50):
        account_id = random.choice(accounts)
        symbol = random.choice(symbols)
        direction = random.choice(['BUY', 'SELL'])
        pnl = random.uniform(-100, 200)
        
        trade = TradeRecord(
            account_id=account_id,
            timestamp=datetime.now() - timedelta(days=random.randint(0, 30)),
            symbol=symbol,
            direction=direction,
            entry_price=random.uniform(1.0, 1.5),
            exit_price=random.uniform(1.0, 1.5),
            quantity=1000,
            pnl=pnl,
            status='closed',
            trade_id=f"trade_{i}_{account_id}"
        )
        
        tracker.record_trade(trade)
    
    # Generate report
    report = tracker.generate_performance_report()
    print(report)
    
    # Export data
    tracker.export_to_csv()
EOF

chmod +x account_performance.py
```

### 🔄 Automated Account Management

#### 1. Account Health Monitor

```bash
cat > account_health_monitor.py << 'EOF'
#!/usr/bin/env python3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from multi_account_config import MultiAccountManager, TradingAccount
from account_performance import PerformanceTracker
from slack_notifier import SlackNotifier, AlertType
from email_notifier import EmailNotifier

class AccountHealthMonitor:
    def __init__(self):
        self.account_manager = MultiAccountManager()
        self.performance_tracker = PerformanceTracker()
        self.slack = SlackNotifier()
        self.email = EmailNotifier()
        self.logger = self._setup_logging()
        
        # Health thresholds
        self.thresholds = {
            'max_drawdown_warning': 0.03,  # 3%
            'max_drawdown_critical': 0.05,  # 5%
            'min_win_rate_warning': 0.4,   # 40%
            'min_win_rate_critical': 0.3,  # 30%
            'max_daily_loss': 0.02,        # 2% of balance
            'min_trades_per_day': 1,
            'max_trades_per_day': 100
        }
        
        self.last_check_time = datetime.now()
        self.account_warnings = {}  # Track warning counts
    
    def _setup_logging(self):
        """Setup logging for account health monitoring"""
        logger = logging.getLogger('AccountHealthMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('account_health.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def check_account_health(self, account: TradingAccount) -> Dict[str, any]:
        """Check health of a specific account"""
        account_id = account.account_id
        
        # Get recent performance metrics
        metrics_7d = self.performance_tracker.calculate_account_metrics(account_id, 7)
        metrics_30d = self.performance_tracker.calculate_account_metrics(account_id, 30)
        
        health_status = {
            'account_id': account_id,
            'account_name': account.account_name,
            'overall_health': 'healthy',
            'warnings': [],
            'critical_issues': [],
            'metrics_7d': metrics_7d,
            'metrics_30d': metrics_30d,
            'recommendations': []
        }
        
        # Check drawdown
        if metrics_7d.max_drawdown > self.thresholds['max_drawdown_critical']:
            health_status['critical_issues'].append(f"Critical drawdown: {metrics_7d.max_drawdown:.1%}")
            health_status['overall_health'] = 'critical'
        elif metrics_7d.max_drawdown > self.thresholds['max_drawdown_warning']:
            health_status['warnings'].append(f"High drawdown: {metrics_7d.max_drawdown:.1%}")
            if health_status['overall_health'] == 'healthy':
                health_status['overall_health'] = 'warning'
        
        # Check win rate
        if metrics_7d.total_trades >= 10:  # Only check if enough trades
            if metrics_7d.win_rate < self.thresholds['min_win_rate_critical'] * 100:
                health_status['critical_issues'].append(f"Critical win rate: {metrics_7d.win_rate:.1f}%")
                health_status['overall_health'] = 'critical'
            elif metrics_7d.win_rate < self.thresholds['min_win_rate_warning'] * 100:
                health_status['warnings'].append(f"Low win rate: {metrics_7d.win_rate:.1f}%")
                if health_status['overall_health'] == 'healthy':
                    health_status['overall_health'] = 'warning'
        
        # Check daily loss limit
        daily_loss_percent = abs(metrics_7d.total_pnl) / account.initial_balance if metrics_7d.total_pnl < 0 else 0
        if daily_loss_percent > self.thresholds['max_daily_loss']:
            health_status['critical_issues'].append(f"Excessive losses: {daily_loss_percent:.1%}")
            health_status['overall_health'] = 'critical'
        
        # Check trading activity
        avg_trades_per_day = metrics_7d.total_trades / 7 if metrics_7d.total_trades > 0 else 0
        if avg_trades_per_day < self.thresholds['min_trades_per_day']:
            health_status['warnings'].append(f"Low trading activity: {avg_trades_per_day:.1f} trades/day")
        elif avg_trades_per_day > self.thresholds['max_trades_per_day']:
            health_status['warnings'].append(f"Excessive trading: {avg_trades_per_day:.1f} trades/day")
        
        # Generate recommendations
        if health_status['overall_health'] == 'critical':
            health_status['recommendations'].append("Consider disabling account temporarily")
            health_status['recommendations'].append("Review and adjust risk parameters")
            health_status['recommendations'].append("Analyze recent trades for patterns")
        elif health_status['overall_health'] == 'warning':
            health_status['recommendations'].append("Monitor closely for next 24 hours")
            health_status['recommendations'].append("Consider reducing position sizes")
        
        return health_status
    
    def monitor_all_accounts(self) -> Dict[str, Dict]:
        """Monitor health of all active accounts"""
        self.logger.info("Starting account health monitoring...")
        
        active_accounts = self.account_manager.get_active_accounts()
        health_results = {}
        
        critical_accounts = []
        warning_accounts = []
        
        for account in active_accounts:
            try:
                health_status = self.check_account_health(account)
                health_results[account.account_id] = health_status
                
                if health_status['overall_health'] == 'critical':
                    critical_accounts.append(account)
                elif health_status['overall_health'] == 'warning':
                    warning_accounts.append(account)
                
                self.logger.info(f"Account {account.account_id}: {health_status['overall_health']}")
                
            except Exception as e:
                self.logger.error(f"Error checking health for account {account.account_id}: {e}")
                health_results[account.account_id] = {
                    'account_id': account.account_id,
                    'overall_health': 'error',
                    'error': str(e)
                }
        
        # Send alerts for critical issues
        for account in critical_accounts:
            self._send_critical_alert(health_results[account.account_id])
        
        # Send warning notifications
        if warning_accounts:
            self._send_warning_alert(warning_accounts, health_results)
        
        # Send daily summary if it's time
        if self._should_send_daily_summary():
            self._send_daily_summary(health_results)
        
        self.last_check_time = datetime.now()
        return health_results
    
    def _send_critical_alert(self, health_status: Dict):
        """Send critical alert for account"""
        account_id = health_status['account_id']
        account_name = health_status['account_name']
        
        message = f"🚨 CRITICAL ACCOUNT ALERT: {account_name}\n\n"
        message += "Critical Issues:\n"
        for issue in health_status['critical_issues']:
            message += f"• {issue}\n"
        
        if health_status['warnings']:
            message += "\nWarnings:\n"
            for warning in health_status['warnings']:
                message += f"• {warning}\n"
        
        message += "\nRecommendations:\n"
        for rec in health_status['recommendations']:
            message += f"• {rec}\n"
        
        # Send Slack alert
        self.slack.critical_error(f"Account Health - {account_name}", message)
        
        # Send email alert
        self.email.critical_alert(f"Critical Account Alert - {account_name}", message)
        
        self.logger.critical(f"Critical alert sent for account {account_id}")
    
    def _send_warning_alert(self, warning_accounts: List[TradingAccount], health_results: Dict):
        """Send warning alert for accounts"""
        if not warning_accounts:
            return
        
        message = f"⚠️ Account Health Warnings ({len(warning_accounts)} accounts)\n\n"
        
        for account in warning_accounts:
            health_status = health_results[account.account_id]
            message += f"📊 {account.account_name}:\n"
            for warning in health_status['warnings']:
                message += f"  • {warning}\n"
            message += "\n"
        
        self.slack.send_alert(AlertType.SYSTEM, message, "warning")
        self.logger.warning(f"Warning alert sent for {len(warning_accounts)} accounts")
    
    def _send_daily_summary(self, health_results: Dict):
        """Send daily health summary"""
        healthy_count = sum(1 for h in health_results.values() if h.get('overall_health') == 'healthy')
        warning_count = sum(1 for h in health_results.values() if h.get('overall_health') == 'warning')
        critical_count = sum(1 for h in health_results.values() if h.get('overall_health') == 'critical')
        total_count = len(health_results)
        
        message = f"📊 Daily Account Health Summary\n\n"
        message += f"✅ Healthy: {healthy_count}\n"
        message += f"⚠️ Warning: {warning_count}\n"
        message += f"🚨 Critical: {critical_count}\n"
        message += f"📈 Total Accounts: {total_count}\n\n"
        
        # Add performance summary
        performance_report = self.performance_tracker.generate_performance_report(1)  # Last 24 hours
        message += performance_report
        
        self.slack.send_alert(AlertType.SYSTEM, message, "info")
        self.logger.info("Daily health summary sent")
    
    def _should_send_daily_summary(self) -> bool:
        """Check if it's time to send daily summary"""
        now = datetime.now()
        # Send at 9 AM daily
        return (now.hour == 9 and 
                (now - self.last_check_time).total_seconds() > 3600)  # At least 1 hour since last check
    
    def auto_disable_critical_accounts(self) -> List[str]:
        """Automatically disable accounts with critical issues"""
        health_results = self.monitor_all_accounts()
        disabled_accounts = []
        
        for account_id, health_status in health_results.items():
            if health_status.get('overall_health') == 'critical':
                account = self.account_manager.accounts.get(account_id)
                if account and account.enabled:
                    # Disable the account
                    account.enabled = False
                    self.account_manager.save_accounts()
                    disabled_accounts.append(account_id)
                    
                    self.logger.critical(f"Auto-disabled critical account: {account_id}")
                    
                    # Send notification
                    self.slack.critical_error(
                        "Account Auto-Disabled",
                        f"Account {account.account_name} has been automatically disabled due to critical health issues."
                    )
        
        return disabled_accounts
    
    def run_continuous_monitoring(self, check_interval_minutes: int = 15):
        """Run continuous account health monitoring"""
        self.logger.info(f"Starting continuous monitoring (check every {check_interval_minutes} minutes)")
        
        while True:
            try:
                self.monitor_all_accounts()
                time.sleep(check_interval_minutes * 60)
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

# CLI interface
if __name__ == "__main__":
    import sys
    
    monitor = AccountHealthMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
            monitor.run_continuous_monitoring(interval)
        elif sys.argv[1] == "check":
            results = monitor.monitor_all_accounts()
            for account_id, health in results.items():
                print(f"{account_id}: {health.get('overall_health', 'unknown')}")
        elif sys.argv[1] == "auto-disable":
            disabled = monitor.auto_disable_critical_accounts()
            print(f"Disabled {len(disabled)} critical accounts: {disabled}")
    else:
        # Single check
        results = monitor.monitor_all_accounts()
        print(f"Monitored {len(results)} accounts")
EOF

chmod +x account_health_monitor.py
```

### 🚀 Production Scaling Setup

#### 1. Complete Scaling Deployment Script

```bash
cat > deploy_scaling.sh << 'EOF'
#!/bin/bash

# AI Trading Sentinel - Production Scaling Deployment
set -e

echo "🚀 Deploying AI Trading Sentinel - Production Scaling Setup"
echo "================================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Configuration
PROJECT_DIR="/root/ai-trading-sentinel"
SERVICE_USER="trading"
VENV_PATH="$PROJECT_DIR/venv"

# Create service user if not exists
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating service user: $SERVICE_USER"
    useradd -r -s /bin/bash -d $PROJECT_DIR $SERVICE_USER
fi

# Set up directory permissions
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
chmod +x $PROJECT_DIR/*.py

# Install Python dependencies for scaling
echo "Installing scaling dependencies..."
sudo -u $SERVICE_USER $VENV_PATH/bin/pip install -q pandas numpy sqlite3 psutil

# Create systemd services for scaling components
echo "Creating systemd services..."

# Multi-account trading service
cat > /etc/systemd/system/trading-multi-account.service << 'EOL'
[Unit]
Description=AI Trading Sentinel - Multi-Account Trading
After=network.target
Requires=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/root/ai-trading-sentinel
Environment=PATH=/root/ai-trading-sentinel/venv/bin
EnvironmentFile=/root/ai-trading-sentinel/.env
ExecStart=/root/ai-trading-sentinel/venv/bin/python parallel_executor.py
Restart=always
RestartSec=30
TimeoutStartSec=60
TimeoutStopSec=30

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-multi-account

[Install]
WantedBy=multi-user.target
EOL

# Account health monitoring service
cat > /etc/systemd/system/trading-health-monitor.service << 'EOL'
[Unit]
Description=AI Trading Sentinel - Account Health Monitor
After=network.target
Requires=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/root/ai-trading-sentinel
Environment=PATH=/root/ai-trading-sentinel/venv/bin
EnvironmentFile=/root/ai-trading-sentinel/.env
ExecStart=/root/ai-trading-sentinel/venv/bin/python account_health_monitor.py continuous 15
Restart=always
RestartSec=60
TimeoutStartSec=30
TimeoutStopSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-health-monitor

[Install]
WantedBy=multi-user.target
EOL

# Performance tracking service
cat > /etc/systemd/system/trading-performance.service << 'EOL'
[Unit]
Description=AI Trading Sentinel - Performance Tracker
After=network.target
Requires=network.target

[Service]
Type=oneshot
User=trading
Group=trading
WorkingDirectory=/root/ai-trading-sentinel
Environment=PATH=/root/ai-trading-sentinel/venv/bin
EnvironmentFile=/root/ai-trading-sentinel/.env
ExecStart=/root/ai-trading-sentinel/venv/bin/python account_performance.py

[Install]
WantedBy=multi-user.target
EOL

# Performance tracking timer (runs every hour)
cat > /etc/systemd/system/trading-performance.timer << 'EOL'
[Unit]
Description=Run AI Trading Sentinel Performance Tracker
Requires=trading-performance.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOL

# Reload systemd and enable services
echo "Enabling and starting services..."
systemctl daemon-reload

# Enable services
systemctl enable trading-multi-account.service
systemctl enable trading-health-monitor.service
systemctl enable trading-performance.service
systemctl enable trading-performance.timer

# Start services
systemctl start trading-multi-account.service
systemctl start trading-health-monitor.service
systemctl start trading-performance.timer

# Create log rotation configuration
echo "Setting up log rotation..."
cat > /etc/logrotate.d/trading-sentinel << 'EOL'
/root/ai-trading-sentinel/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 trading trading
    postrotate
        systemctl reload trading-multi-account.service
        systemctl reload trading-health-monitor.service
    endscript
}
EOL

# Create monitoring dashboard startup script
cat > $PROJECT_DIR/start_dashboard.sh << 'EOL'
#!/bin/bash
cd /root/ai-trading-sentinel
source venv/bin/activate
nohup python monitoring_dashboard.py > logs/dashboard.log 2>&1 &
echo $! > dashboard.pid
echo "Monitoring dashboard started on port 8080"
EOL

chmod +x $PROJECT_DIR/start_dashboard.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/start_dashboard.sh

# Create management scripts
echo "Creating management scripts..."

# Account management script
cat > $PROJECT_DIR/manage_accounts.py << 'EOL'
#!/usr/bin/env python3
import sys
import json
from multi_account_config import MultiAccountManager, TradingAccount, AccountType, BrokerType

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_accounts.py [list|add|remove|enable|disable] [args...]")
        return
    
    manager = MultiAccountManager()
    command = sys.argv[1]
    
    if command == "list":
        accounts = manager.get_active_accounts()
        print(f"Active Accounts ({len(accounts)}):")
        for acc in accounts:
            status = "✅" if acc.enabled else "❌"
            print(f"{status} {acc.account_id}: {acc.account_name} ({acc.account_type.value})")
    
    elif command == "add":
        if len(sys.argv) < 8:
            print("Usage: add <id> <name> <broker> <type> <username> <password> <balance>")
            return
        
        account = TradingAccount(
            account_id=sys.argv[2],
            account_name=sys.argv[3],
            broker=BrokerType(sys.argv[4]),
            account_type=AccountType(sys.argv[5]),
            credentials={"username": sys.argv[6], "password": sys.argv[7]},
            initial_balance=float(sys.argv[8]),
            max_risk_per_trade=0.02,
            max_daily_trades=20,
            max_drawdown_percent=0.05
        )
        
        manager.add_account(account)
        print(f"Added account: {account.account_id}")
    
    elif command == "remove":
        if len(sys.argv) < 3:
            print("Usage: remove <account_id>")
            return
        
        manager.remove_account(sys.argv[2])
        print(f"Removed account: {sys.argv[2]}")
    
    elif command in ["enable", "disable"]:
        if len(sys.argv) < 3:
            print(f"Usage: {command} <account_id>")
            return
        
        account