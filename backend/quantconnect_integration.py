import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuantConnectIntegration:
    def __init__(self):
        """Initialize QuantConnect integration with API credentials"""
        self.api_key = os.getenv('QUANTCONNECT_API_KEY')
        self.project_id = os.getenv('QUANTCONNECT_PROJECT_ID')
        self.base_url = 'https://www.quantconnect.com/api/v2'
        
        if not self.api_key or not self.project_id:
            raise ValueError("QuantConnect API key and project ID must be set in .env file")
    
    def _make_request(self, endpoint, method='GET', data=None):
        """Make authenticated request to QuantConnect API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add timestamp for authentication
        timestamp = int(time.time() * 1000)
        
        # Create auth data
        auth_data = {
            'apiKey': self.api_key,
            'timestamp': timestamp
        }
        
        # Combine with request data if any
        if data:
            request_data = {**auth_data, **data}
        else:
            request_data = auth_data
        
        # Make request
        if method == 'GET':
            response = requests.get(url, headers=headers, params=request_data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=request_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check for errors
        response.raise_for_status()
        
        return response.json()
    
    def get_project_details(self):
        """Get details of the configured project"""
        endpoint = f"projects/{self.project_id}/read"
        return self._make_request(endpoint)
    
    def get_backtest_list(self):
        """Get list of backtests for the project"""
        endpoint = f"projects/{self.project_id}/backtests/read"
        return self._make_request(endpoint)
    
    def get_backtest_results(self, backtest_id):
        """Get detailed results of a specific backtest"""
        endpoint = f"projects/{self.project_id}/backtests/{backtest_id}/read"
        return self._make_request(endpoint)
    
    def create_backtest(self, name, code=None):
        """Create a new backtest"""
        endpoint = f"projects/{self.project_id}/backtests/create"
        
        data = {
            'name': name,
            'compile': True
        }
        
        if code:
            data['code'] = code
        
        return self._make_request(endpoint, method='POST', data=data)
    
    def get_live_algorithm_status(self, deployment_id):
        """Get status of a live trading algorithm"""
        endpoint = f"live/read"
        data = {
            'deployId': deployment_id
        }
        return self._make_request(endpoint, method='POST', data=data)
    
    def deploy_live_algorithm(self, project_id=None, compile=True, node_id=None, brokerage='Paper'):
        """Deploy algorithm to live trading"""
        if project_id is None:
            project_id = self.project_id
            
        endpoint = "live/create"
        data = {
            'projectId': project_id,
            'compileId': None,  # Will be auto-compiled if None
            'nodeId': node_id,
            'brokerage': brokerage,
            'compile': compile
        }
        return self._make_request(endpoint, method='POST', data=data)
    
    def stop_live_algorithm(self, deployment_id):
        """Stop a live trading algorithm"""
        endpoint = "live/update"
        data = {
            'deployId': deployment_id,
            'status': 'Stopped'
        }
        return self._make_request(endpoint, method='POST', data=data)
    
    def get_strategy_equity(self, deployment_id):
        """Get equity curve data for a live algorithm"""
        endpoint = "live/read"
        data = {
            'deployId': deployment_id
        }
        response = self._make_request(endpoint, method='POST', data=data)
        
        # Extract equity data if available
        if 'result' in response and 'charts' in response['result']:
            charts = response['result']['charts']
            if 'Strategy Equity' in charts:
                return charts['Strategy Equity']
        
        return None
    
    def get_live_results(self, deployment_id):
        """Get comprehensive results for a live algorithm"""
        endpoint = "live/read"
        data = {
            'deployId': deployment_id
        }
        return self._make_request(endpoint, method='POST', data=data)

# Example usage
def test_quantconnect_integration():
    """Test QuantConnect integration"""
    try:
        qc = QuantConnectIntegration()
        project_details = qc.get_project_details()
        print(f"Project details: {json.dumps(project_details, indent=2)}")
        
        backtests = qc.get_backtest_list()
        print(f"Backtests: {json.dumps(backtests, indent=2)}")
        
        return True
    except Exception as e:
        print(f"Error testing QuantConnect integration: {e}")
        return False

if __name__ == "__main__":
    print("Testing QuantConnect integration...")
    success = test_quantconnect_integration()
    if success:
        print("QuantConnect integration test successful!")
    else:
        print("QuantConnect integration test failed!")