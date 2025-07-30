import os
import sys
from utils.slack_notifications import send_slack_prophetic

def test_slack_notifications():
    """
    Test the Slack notification functionality with different message types.
    
    Before running this test, make sure to set the SLACK_WEBHOOK_URL in your .env file.
    """
    print("\n🔔 Testing Slack Notifications...")
    
    # Check if SLACK_WEBHOOK_URL is set
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url or webhook_url == "https://hooks.slack.com/services/YOUR_WEBHOOK_URL_HERE":
        print("❌ Error: SLACK_WEBHOOK_URL environment variable not set or using default value.")
        print("Please update your .env file with a valid Slack webhook URL.")
        return False
    
    # Test session ID
    session_id = f"TEST-{os.getenv('BULENOX_USERNAME', 'USER')}-{os.getpid()}"
    
    # Test different message types
    test_cases = [
        {
            "type": "login_success",
            "params": {"session_id": session_id}
        },
        {
            "type": "profit",
            "params": {
                "symbol": "EURUSD", 
                "entry": 1.0750, 
                "direction": "buy", 
                "profit": 120.50, 
                "session_id": session_id
            }
        },
        {
            "type": "fail",
            "params": {
                "symbol": "GBPJPY", 
                "entry": 182.500, 
                "direction": "sell", 
                "status": "Market closed", 
                "session_id": session_id
            }
        },
        {
            "type": "custom message",
            "params": {"session_id": session_id}
        }
    ]
    
    success_count = 0
    
    for test in test_cases:
        print(f"\nTesting message type: {test['type']}")
        result = send_slack_prophetic(test['type'], **test['params'])
        
        if result:
            print(f"✅ Successfully sent {test['type']} notification")
            success_count += 1
        else:
            print(f"❌ Failed to send {test['type']} notification")
    
    print(f"\nTest summary: {success_count}/{len(test_cases)} notifications sent successfully")
    return success_count == len(test_cases)

if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded environment variables from .env file")
    except ImportError:
        print("Warning: python-dotenv not installed. Using existing environment variables.")
    
    success = test_slack_notifications()
    sys.exit(0 if success else 1)