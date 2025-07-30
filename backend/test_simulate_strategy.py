import requests
import json

session = requests.Session()

# Login to get session cookie
login_url = "http://127.0.0.1:5000/api/login"
login_payload = {"username": "admin", "password": "password123"}
login_headers = {"Content-Type": "application/json"}
login_response = session.post(login_url, data=json.dumps(login_payload), headers=login_headers)
print("Login Status Code:", login_response.status_code)
print("Login Response:", login_response.json())

# Now call simulate endpoint with session cookie
simulate_url = "http://127.0.0.1:5000/api/simulate"
payload = {
    "strategy_name": "quantconnect_strategy.py",
    "start_date": "2020-01-01",
    "end_date": "2020-12-31"
}
headers = {"Content-Type": "application/json"}
response = session.post(simulate_url, data=json.dumps(payload), headers=headers)
print("Simulate Status Code:", response.status_code)
print("Simulate Response:", response.json())