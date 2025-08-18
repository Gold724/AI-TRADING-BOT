#!/usr/bin/env python3
"""
TradeBot Sentinel Enhanced System Test
Tests all the new features: notifications, risk management, and scheduling
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from notifications import NotificationManager
from risk_management import RiskManager
from scheduler import CronScheduler, ScheduledJob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_notifications():
    """Test notification system"""
    logger.info("🔔 Testing Notification System...")
    
    try:
        notification_manager = NotificationManager()
        
        # Test trade alert
        await notification_manager.send_trade_alert({
            'symbol': 'BTCUSDT',
            'amount': 0.001,
            'price': 45000.0,
            'side': 'BUY',
            'timestamp': datetime.now().isoformat()
        })
        
        # Test system status
        await notification_manager.send_system_status(
            "System Test",
            {
                'daily_trades': 5,
                'daily_pnl': 150.50,
                'uptime': '2h 30m',
                'status': 'Testing notifications'
            }
        )
        
        # Test error alert
        await notification_manager.send_error_alert(
            "Test Error",
            "This is a test error message"
        )
        
        logger.info("✅ Notification system test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Notification test failed: {e}")
        return False

async def test_risk_management():
    """Test risk management system"""
    logger.info("🛡️ Testing Risk Management System...")
    
    try:
        risk_manager = RiskManager()
        
        # Test trade validation
        trade_data = {
            'symbol': 'BTCUSDT',
            'amount': 0.001,
            'price': 45000.0,
            'side': 'BUY'
        }
        
        can_trade = risk_manager.can_place_trade(trade_data)
        logger.info(f"Trade validation result: {can_trade}")
        
        if can_trade:
            # Record the trade
            risk_manager.record_trade(trade_data)
            logger.info("Trade recorded successfully")
        
        # Test risk summary
        risk_summary = risk_manager.get_risk_summary()
        logger.info(f"Risk summary: {risk_summary['risk_utilization']}")
        
        logger.info("✅ Risk management system test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Risk management test failed: {e}")
        return False

def test_scheduler():
    """Test scheduler system"""
    logger.info("⏰ Testing Scheduler System...")
    
    try:
        scheduler = CronScheduler()
        
        # Create a test job
        test_job = ScheduledJob(
            name="Test Job",
            command="echo 'Test job executed'",
            schedule="*/1 * * * *",  # Every minute
            enabled=True,
            max_retries=1,
            max_runtime=30
        )
        
        # Add job to scheduler
        scheduler.add_job(test_job)
        logger.info(f"Added test job: {test_job.name}")
        
        # Check jobs
        jobs_count = len(scheduler.jobs)
        logger.info(f"Total jobs in scheduler: {jobs_count}")
        
        # Remove test job
        scheduler.remove_job("Test Job")
        logger.info("Removed test job")
        
        logger.info("✅ Scheduler system test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Scheduler test failed: {e}")
        return False

async def test_integration():
    """Test integration between all systems"""
    logger.info("🔗 Testing System Integration...")
    
    try:
        # Initialize all systems
        notification_manager = NotificationManager()
        risk_manager = RiskManager()
        
        # Simulate a trade scenario
        trade_data = {
            'symbol': 'ETHUSDT',
            'amount': 0.1,
            'price': 3000.0,
            'side': 'SELL'
        }
        
        # Check if trade is allowed
        if risk_manager.can_place_trade(trade_data):
            # Record trade
            risk_manager.record_trade(trade_data)
            
            # Send notification
            await notification_manager.send_trade_alert(trade_data)
            
            logger.info("✅ Integration test: Trade processed successfully")
        else:
            # Send risk alert
            await notification_manager.send_risk_alert(
                "Daily Limit",
                "5",
                "3"
            )
            logger.info("✅ Integration test: Trade blocked by risk management")
        
        logger.info("✅ System integration test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting TradeBot Sentinel Enhanced System Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Test notifications
    results.append(await test_notifications())
    
    # Test risk management
    results.append(await test_risk_management())
    
    # Test scheduler
    results.append(test_scheduler())
    
    # Test integration
    results.append(await test_integration())
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    test_names = [
        "Notifications",
        "Risk Management", 
        "Scheduler",
        "Integration"
    ]
    
    passed = 0
    for i, result in enumerate(results):
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_names[i]}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"📈 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All enhanced features are working correctly!")
        logger.info("🚀 TradeBot Sentinel is ready for autonomous operation")
    else:
        logger.warning("⚠️ Some tests failed. Please check the logs above.")
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)