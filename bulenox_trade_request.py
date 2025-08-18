# Converted from Bulenox trade request cURL command
import requests

def execute_bulenox_trade(token, symbol="EURUSD", volume=0.01, side="buy", trade_type="market"):
    """
    Execute a trade on Bulenox platform
    
    Args:
        token (str): Your Bulenox authorization token
        symbol (str): Trading pair symbol (default: EURUSD)
        volume (float): Trade volume/lot size (default: 0.01)
        side (str): Trade direction - 'buy' or 'sell' (default: buy)
        trade_type (str): Order type - 'market', 'limit', etc. (default: market)
        
    Returns:
        dict: JSON response from the API
    """
    url = 'https://bulenox.com/api/trade'
    
    headers = {
        'authority': 'bulenox.com',
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'origin': 'https://bulenox.com',
        'referer': 'https://bulenox.com/trade',
        'sec-ch-ua': '"Chromium";v="112"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    
    data = {
        "symbol": symbol,
        "volume": volume,
        "side": side,
        "type": trade_type
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()


if __name__ == "__main__":
    # Example usage
    # Replace YOUR_TOKEN_HERE with your actual Bulenox authorization token
    token = "YOUR_TOKEN_HERE"
    
    # Execute a trade
    try:
        result = execute_bulenox_trade(token)
        print("Trade executed successfully:")
        print(result)
    except Exception as e:
        print(f"Error executing trade: {e}")