import requests
import json

# Auto-generated from trade request
url = "https://example.com/api/trade"
headers = {
    "Content-Type": "application/json"
}
data = {}

response = requests.post(url, headers=headers, data=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
