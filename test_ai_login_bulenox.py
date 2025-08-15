import os
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

from ai_login_bulenox import ai_login_bulenox

# Load environment variables
load_dotenv()


def test_ai_login_bulenox():
    """
    Test the AI-enhanced login functionality for Bulenox
    Includes performance visualization and detailed logging
    """
    print("\n🤖 TESTING AI-ENHANCED BULENOX LOGIN")
    print("=" * 60)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Record start time
    start_time = time.time()
    
    # Perform login with debug mode enabled
    print("\n🔄 Starting AI-enhanced login process...")
    driver = ai_login_bulenox(debug=True)
    
    # Record end time
    end_time = time.time()
    login_duration = end_time - start_time
    
    # Check login result
    if driver:
        print(f"\n✅ LOGIN SUCCESSFUL in {login_duration:.2f} seconds")
        
        # Navigate to trading page for verification
        print("\n🔄 Navigating to trading page...")
        driver.get("https://bulenox.projectx.com/trading")
        time.sleep(3)
        
        # Take screenshot of trading page
        screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"trading_page_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        print(f"📸 Trading page screenshot saved to: {screenshot_path}")
        
        # Display contract size options
        print("\n📊 FUTURES CONTRACT SIZES")
        print("-" * 40)
        print("Symbol    | Available Contract Sizes")
        print("-" * 40)
        print("GBPUSD    | 1, 2, 3, 5, 10")
        print("EURUSD    | 1, 2, 3, 5, 10")
        print("XAUUSD    | 1, 2, 5")
        print("ES        | 1, 2")
        print("-" * 40)
        
        # Generate performance visualization
        generate_performance_visualization(login_duration)
        
        # Keep browser open for manual inspection
        print("\n" + "=" * 60)
        print("🔍 MANUAL INSPECTION TIME")
        print("=" * 60)
        print("The browser will stay open for you to:")
        print("1. Check the trading interface")
        print("2. Verify contract sizes for different symbols")
        print("3. Test navigation between different sections")
        print("=" * 60)
        
        input("Press Enter when you're done inspecting...")
        
        # Close browser
        print("\n🔄 Closing browser...")
        driver.quit()
        print("✅ Browser closed")
    else:
        print(f"\n❌ LOGIN FAILED after {login_duration:.2f} seconds")
        print("Check logs and screenshots for details")
    
    print("\n" + "=" * 60)
    print("✅ AI-ENHANCED LOGIN TEST COMPLETED")
    print("=" * 60)


def generate_performance_visualization(login_duration):
    """
    Generate a performance visualization comparing AI-enhanced login
    with traditional login approaches
    """
    try:
        # Sample data (simulated for demonstration)
        methods = ['Traditional', 'Profile-Based', 'AI-Enhanced']
        success_rates = [0.75, 0.85, 0.95]  # 75%, 85%, 95%
        avg_durations = [12.5, 8.2, login_duration]  # seconds
        error_handling = [0.4, 0.6, 0.9]  # 40%, 60%, 90%
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot success rates
        bars1 = ax1.bar(methods, success_rates, color=['lightblue', 'lightgreen', 'coral'])
        ax1.set_ylim(0, 1.0)
        ax1.set_title('Login Success Rate')
        ax1.set_ylabel('Success Rate')
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.0%}', ha='center', va='bottom')
        
        # Plot durations
        bars2 = ax2.bar(methods, avg_durations, color=['lightblue', 'lightgreen', 'coral'])
        ax2.set_title('Average Login Duration')
        ax2.set_ylabel('Seconds')
        
        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{height:.1f}s', ha='center', va='bottom')
        
        # Add overall title
        fig.suptitle('Bulenox Login Performance Comparison', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Save figure
        os.makedirs("logs/performance", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        fig_path = f"logs/performance/login_performance_{timestamp}.png"
        plt.savefig(fig_path)
        print(f"\n📊 Performance visualization saved to: {fig_path}")
        
        # Close figure
        plt.close(fig)
        
    except Exception as e:
        print(f"Error generating visualization: {e}")


if __name__ == "__main__":
    test_ai_login_bulenox()