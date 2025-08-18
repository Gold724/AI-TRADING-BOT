#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class PaperTradingValidator:
    def __init__(self):
        self.setup_logging()
        self.paper_balance = float(os.getenv('PAPER_BALANCE', 10000))
        self.initial_balance = self.paper_balance
        self.trades = []
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'trade_executions': 0,
            'risk_violations': 0,
            'performance_metrics': {}
        }
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('paper_trading_test.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def simulate_trade_signal(self, symbol="EURUSD", direction="BUY", confidence=0.8):
        """Simulate incoming trade signal"""
        return {
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'entry_price': 1.0850 if symbol == "EURUSD" else 1.2650,
            'spread': 0.0002
        }
    
    def calculate_position_size(self, signal):
        """Calculate position size based on risk management"""
        risk_percentage = float(os.getenv('RISK_PERCENTAGE', 1.0))
        risk_amount = self.paper_balance * (risk_percentage / 100)
        
        # Simulate position size calculation
        position_size = min(risk_amount * 10, float(os.getenv('MAX_TRADE_AMOUNT', 500)))
        return max(position_size, float(os.getenv('MIN_TRADE_AMOUNT', 100)))
    
    def execute_paper_trade(self, signal):
        """Execute a paper trade"""
        try:
            position_size = self.calculate_position_size(signal)
            
            trade = {
                'id': len(self.trades) + 1,
                'symbol': signal['symbol'],
                'direction': signal['direction'],
                'entry_price': signal['entry_price'],
                'position_size': position_size,
                'timestamp': signal['timestamp'],
                'status': 'open',
                'pnl': 0.0
            }
            
            self.trades.append(trade)
            self.test_results['trade_executions'] += 1
            
            self.logger.info(f"[TRADE] Paper Trade Executed: {trade['symbol']} {trade['direction']} ${trade['position_size']:.2f}")
            return trade
            
        except Exception as e:
            self.logger.error(f"[ERROR] Trade execution failed: {e}")
            return None
    
    def simulate_trade_outcome(self, trade):
        """Simulate trade outcome (profit/loss)"""
        import random
        
        # Simulate market movement (60% win rate for testing)
        win_probability = 0.6
        is_winner = random.random() < win_probability
        
        if is_winner:
            # Simulate profit (1-3% gain)
            profit_percentage = random.uniform(1, 3)
            pnl = trade['position_size'] * (profit_percentage / 100)
        else:
            # Simulate loss (1-2% loss)
            loss_percentage = random.uniform(1, 2)
            pnl = -trade['position_size'] * (loss_percentage / 100)
        
        trade['pnl'] = pnl
        trade['status'] = 'closed'
        trade['exit_timestamp'] = datetime.now().isoformat()
        
        self.paper_balance += pnl
        
        result = "PROFIT" if pnl > 0 else "LOSS"
        self.logger.info(f"[RESULT] Trade Closed: {trade['symbol']} {result} ${pnl:.2f} | Balance: ${self.paper_balance:.2f}")
        
        return trade
    
    def test_risk_management(self):
        """Test risk management controls"""
        self.logger.info("[TEST] Testing Risk Management Controls")
        
        tests = [
            self.test_max_daily_trades,
            self.test_position_sizing,
            self.test_drawdown_limits,
            self.test_stop_loss_logic
        ]
        
        for test in tests:
            try:
                result = test()
                if result:
                    self.test_results['passed_tests'] += 1
                    self.logger.info(f"[PASS] {test.__name__} PASSED")
                else:
                    self.test_results['failed_tests'] += 1
                    self.logger.error(f"[FAIL] {test.__name__} FAILED")
                self.test_results['total_tests'] += 1
            except Exception as e:
                self.test_results['failed_tests'] += 1
                self.test_results['total_tests'] += 1
                self.logger.error(f"[ERROR] {test.__name__} ERROR: {e}")
    
    def test_max_daily_trades(self):
        """Test maximum daily trades limit"""
        max_trades = int(os.getenv('MAX_DAILY_TRADES', 3))
        daily_trades = len([t for t in self.trades if t['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))])
        
        if daily_trades <= max_trades:
            return True
        else:
            self.test_results['risk_violations'] += 1
            return False
    
    def test_position_sizing(self):
        """Test position sizing logic"""
        if not self.trades:
            return True
        
        max_position = float(os.getenv('MAX_TRADE_AMOUNT', 500))
        min_position = float(os.getenv('MIN_TRADE_AMOUNT', 100))
        
        for trade in self.trades:
            if trade['position_size'] > max_position or trade['position_size'] < min_position:
                self.test_results['risk_violations'] += 1
                return False
        
        return True
    
    def test_drawdown_limits(self):
        """Test maximum drawdown limits"""
        max_drawdown = float(os.getenv('MAX_DRAWDOWN', 5.0))
        current_drawdown = ((self.initial_balance - self.paper_balance) / self.initial_balance) * 100
        
        if current_drawdown <= max_drawdown:
            return True
        else:
            self.test_results['risk_violations'] += 1
            return False
    
    def test_stop_loss_logic(self):
        """Test stop loss implementation"""
        stop_loss_pct = float(os.getenv('STOP_LOSS_PERCENTAGE', 2.0))
        
        # Simulate stop loss trigger
        for trade in self.trades:
            if trade['status'] == 'closed' and trade['pnl'] < 0:
                max_loss = trade['position_size'] * (stop_loss_pct / 100)
                if abs(trade['pnl']) <= max_loss * 1.1:  # 10% tolerance
                    continue
                else:
                    self.test_results['risk_violations'] += 1
                    return False
        
        return True
    
    def calculate_performance_metrics(self):
        """Calculate trading performance metrics"""
        if not self.trades:
            return
        
        closed_trades = [t for t in self.trades if t['status'] == 'closed']
        
        if not closed_trades:
            return
        
        total_pnl = sum(t['pnl'] for t in closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(closed_trades) * 100
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        self.test_results['performance_metrics'] = {
            'total_trades': len(closed_trades),
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_balance': self.paper_balance,
            'return_percentage': ((self.paper_balance - self.initial_balance) / self.initial_balance) * 100
        }
    
    async def run_paper_trading_session(self, duration_minutes=5, trade_frequency=30):
        """Run a complete paper trading session"""
        self.logger.info(f"[START] Starting {duration_minutes}-minute paper trading session")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        directions = ['BUY', 'SELL']
        
        trade_count = 0
        while datetime.now() < end_time and trade_count < 3:
            # Check if we can make more trades today
            max_trades = int(os.getenv('MAX_DAILY_TRADES', 3))
            if len(self.trades) >= max_trades:
                self.logger.info(f"[LIMIT] Daily trade limit reached ({max_trades})")
                break
            
            # Generate random trade signal
            import random
            signal = self.simulate_trade_signal(
                symbol=random.choice(symbols),
                direction=random.choice(directions),
                confidence=random.uniform(0.6, 0.9)
            )
            
            # Execute trade
            trade = self.execute_paper_trade(signal)
            
            if trade:
                # Simulate trade duration (5-15 seconds for testing)
                await asyncio.sleep(random.uniform(5, 15))
                
                # Close trade with simulated outcome
                self.simulate_trade_outcome(trade)
                trade_count += 1
            
            # Wait before next trade
            await asyncio.sleep(trade_frequency)
        
        self.logger.info("[COMPLETE] Paper trading session completed")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.calculate_performance_metrics()
        
        report = {
            'test_summary': self.test_results,
            'trading_performance': self.test_results['performance_metrics'],
            'trades': self.trades,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report to file
        with open('paper_trading_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("[REPORT] PAPER TRADING VALIDATION REPORT")
        self.logger.info("=" * 60)
        
        self.logger.info(f"Tests Passed: {self.test_results['passed_tests']}/{self.test_results['total_tests']}")
        self.logger.info(f"Trade Executions: {self.test_results['trade_executions']}")
        self.logger.info(f"Risk Violations: {self.test_results['risk_violations']}")
        
        if self.test_results['performance_metrics']:
            metrics = self.test_results['performance_metrics']
            self.logger.info(f"\n[METRICS] PERFORMANCE METRICS:")
            self.logger.info(f"Total P&L: ${metrics['total_pnl']:.2f}")
            self.logger.info(f"Win Rate: {metrics['win_rate']:.1f}%")
            self.logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}")
            self.logger.info(f"Final Balance: ${metrics['final_balance']:.2f}")
            self.logger.info(f"Return: {metrics['return_percentage']:.2f}%")
        
        # Determine overall result
        success_rate = self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)
        
        if success_rate >= 0.8 and self.test_results['risk_violations'] == 0:
            self.logger.info("\n[SUCCESS] PAPER TRADING VALIDATION: PASSED")
            self.logger.info("[OK] System ready for live trading consideration")
            return True
        else:
            self.logger.info("\n[WARNING] PAPER TRADING VALIDATION: NEEDS ATTENTION")
            self.logger.info("[ACTION] Address issues before live trading")
            return False

async def main():
    validator = PaperTradingValidator()
    
    # Run risk management tests
    validator.test_risk_management()
    
    # Run paper trading session
    await validator.run_paper_trading_session(duration_minutes=2, trade_frequency=10)
    
    # Generate final report
    success = validator.generate_report()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)