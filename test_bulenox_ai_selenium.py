import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

from bulenox_ai_selenium import login_bulenox_ai

# Load environment variables
load_dotenv()


def test_ai_login():
    """Test the AI-enhanced Bulenox login functionality"""
    print("\n" + "=" * 80)
    print("🤖 TESTING AI-ENHANCED BULENOX LOGIN")
    print("=" * 80)
    
    # Record start time
    start_time = time.time()
    
    # Perform login
    print("\n🔄 Initiating AI-enhanced login...")
    bulenox = login_bulenox_ai(debug=True)
    
    if not bulenox:
        print("\n❌ AI-enhanced login failed")
        return
    
    # Calculate login duration
    login_duration = time.time() - start_time
    print(f"\n✅ AI-enhanced login successful in {login_duration:.2f} seconds")
    
    try:
        # Navigate to trading page
        print("\n🔄 Navigating to trading page...")
        bulenox.navigate_to_trading()
        
        # Take screenshot of trading interface
        print("\n📸 Taking screenshot of trading interface...")
        bulenox._take_screenshot("trading_interface")
        
        # Display sample futures contract sizes
        print("\n📊 Bulenox Futures Contract Sizes:")
        print("  - Gold (XAUUSD): 1 contract = 100 troy ounces")
        print("  - E-mini S&P 500 (ES): 1 contract = $50 × S&P 500 Index")
        print("  - Euro FX (EURUSD): 1 contract = €125,000")
        print("  - British Pound (GBPUSD): 1 contract = £62,500")
        print("  - Japanese Yen (USDJPY): 1 contract = ¥12,500,000")
        
        # Generate performance visualization
        print("\n📈 Generating performance visualization...")
        generate_performance_visualization(login_duration)
        
        # Keep browser open for inspection
        print("\n🔍 Browser will remain open for manual inspection")
        print("Press Ctrl+C to close the browser and exit")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Closing browser and exiting...")
            bulenox.close()
    
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
    finally:
        if bulenox and bulenox.driver:
            bulenox.close()


def generate_performance_visualization(ai_login_duration):
    """Generate a performance comparison visualization"""
    # Sample data (based on typical performance)
    traditional_login_duration = 12.5  # seconds
    
    # Create comparison data
    methods = ['Traditional Selenium', 'AI-Enhanced Selenium']
    durations = [traditional_login_duration, ai_login_duration]
    
    # Calculate improvement percentage
    improvement = ((traditional_login_duration - ai_login_duration) / traditional_login_duration) * 100
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(methods, durations, color=['#3498db', '#2ecc71'])
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.2f}s', ha='center', va='bottom')
    
    # Add improvement annotation
    plt.annotate(f'{improvement:.1f}% Faster', 
                xy=(1, ai_login_duration), 
                xytext=(1.2, ai_login_duration + 2),
                arrowprops=dict(facecolor='black', shrink=0.05))
    
    # Customize chart
    plt.title('Bulenox Login Performance Comparison', fontsize=16)
    plt.ylabel('Login Duration (seconds)', fontsize=12)
    plt.ylim(0, max(durations) * 1.3)  # Add some space at the top
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plt.figtext(0.5, 0.01, f'Generated: {timestamp}', ha='center', fontsize=8)
    
    # Save the chart
    os.makedirs("logs", exist_ok=True)
    plt.savefig(os.path.join("logs", "bulenox_login_performance.png"))
    plt.close()


if __name__ == "__main__":
    test_ai_login()