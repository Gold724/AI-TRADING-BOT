#!/usr/bin/env python3
"""
TradeBot Sentinel - Example Usage

This script demonstrates how to use the TradeBot Sentinel automation
with different configurations and error handling.
"""

import asyncio
import os
import sys
from tradebot_sentinel_automation import TradeBotSentinelAutomation


async def example_basic_usage():
    """Basic usage example - headless mode"""
    print("🤖 Example 1: Basic Usage (Headless)")
    
    # Ensure environment variables are set
    if not os.getenv('BULENOX_USERNAME') or not os.getenv('BULENOX_PASSWORD'):
        print("❌ Please set BULENOX_USERNAME and BULENOX_PASSWORD environment variables")
        return False
    
    automation = TradeBotSentinelAutomation(headless=True)
    success = await automation.run_automation()
    
    if success:
        print("✅ Basic automation completed successfully!")
    else:
        print("❌ Basic automation failed!")
    
    return success


async def example_visible_mode():
    """Visible mode example for debugging"""
    print("\n👁️ Example 2: Visible Mode (Debug)")
    
    automation = TradeBotSentinelAutomation(headless=False)
    success = await automation.run_automation()
    
    if success:
        print("✅ Visible mode automation completed successfully!")
    else:
        print("❌ Visible mode automation failed!")
    
    return success


async def example_custom_trade():
    """Custom trade parameters example"""
    print("\n📊 Example 3: Custom Trade Parameters")
    
    automation = TradeBotSentinelAutomation(headless=True)
    
    try:
        # Setup browser
        await automation.setup_browser()
        
        # Login
        if not await automation.login():
            print("❌ Login failed")
            return False
        
        # Navigate to trading
        if not await automation.navigate_to_trading():
            print("❌ Trading navigation failed")
            return False
        
        # Place custom trade order
        success = await automation.place_trade_order(
            symbol="ETHUSDT",
            amount=0.01,
            side="sell"
        )
        
        if success:
            print("✅ Custom trade order placed successfully!")
            
            # Wait for trade execution
            print("⏳ Waiting for trade execution...")
            await asyncio.sleep(15)
            
            # Check results
            if automation.trade_requests:
                print(f"📊 Captured {len(automation.trade_requests)} trade requests")
                for i, req in enumerate(automation.trade_requests, 1):
                    print(f"  {i}. {req['method']} {req['url']}")
            else:
                print("ℹ️ No trade requests captured")
        else:
            print("❌ Custom trade order failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Custom trade example failed: {e}")
        return False
    
    finally:
        await automation.cleanup()


async def example_error_handling():
    """Error handling and recovery example"""
    print("\n🛡️ Example 4: Error Handling")
    
    # Intentionally use wrong credentials to test error handling
    original_username = os.getenv('BULENOX_USERNAME')
    original_password = os.getenv('BULENOX_PASSWORD')
    
    # Set invalid credentials
    os.environ['BULENOX_USERNAME'] = 'invalid_user'
    os.environ['BULENOX_PASSWORD'] = 'invalid_pass'
    
    try:
        automation = TradeBotSentinelAutomation(headless=True)
        success = await automation.run_automation()
        
        if not success:
            print("✅ Error handling worked correctly - invalid login detected")
        else:
            print("⚠️ Unexpected success with invalid credentials")
        
    except Exception as e:
        print(f"✅ Exception caught correctly: {e}")
    
    finally:
        # Restore original credentials
        if original_username:
            os.environ['BULENOX_USERNAME'] = original_username
        if original_password:
            os.environ['BULENOX_PASSWORD'] = original_password
    
    return True


async def main():
    """Run all examples"""
    print("🚀 TradeBot Sentinel - Example Usage")
    print("=" * 50)
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Visible Mode", example_visible_mode),
        ("Custom Trade", example_custom_trade),
        ("Error Handling", example_error_handling)
    ]
    
    results = []
    
    for name, example_func in examples:
        try:
            print(f"\n🔄 Running {name} example...")
            success = await example_func()
            results.append((name, success))
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
            break
        except Exception as e:
            print(f"❌ {name} example failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:<20} {status}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} examples passed")
    
    if total_passed == total_tests:
        print("🎉 All examples completed successfully!")
        return 0
    else:
        print("⚠️ Some examples failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)