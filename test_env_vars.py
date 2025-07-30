import os
from dotenv import load_dotenv

def test_env_vars():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    username = os.getenv('BROKER_USERNAME')
    password = os.getenv('BROKER_PASSWORD')
    broker_url = os.getenv('BROKER_URL')
    
    print(f"BROKER_USERNAME: {username}")
    print(f"BROKER_PASSWORD: {'*' * len(password) if password else None}")
    print(f"BROKER_URL: {broker_url}")
    
    # Check if all required variables are set
    if not all([username, password, broker_url]):
        print("\nWARNING: One or more required environment variables are missing!")
    else:
        print("\nAll required environment variables are set.")

if __name__ == "__main__":
    print("Testing Environment Variables for StealthExecutor")
    print("==============================================\n")
    test_env_vars()