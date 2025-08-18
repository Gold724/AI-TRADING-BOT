# Generated from Bulenox trade request
# Original cURL command:
curl 'https://o152829.ingest.sentry.io/api/4505284847337472/envelope/?sentry_key=b4ae83b218d4480397b461b127490c47&sentry_version=7&sentry_client=sentry.javascript.react%2F7.80.0' -X POST -H 'sec-ch-ua-platform: "Windows"' -H 'referer: https://bulenox.projectx.com/' -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' -H 'sec-ch-ua: "Chromium";v="139", "Not;A=Brand";v="99"' -H 'content-type: text/plain;charset=UTF-8' -H 'sec-ch-ua-mobile: ?0' --data-raw '{"sent_at":"2025-08-11T07:57:26.909Z","sdk":{"name":"sentry.javascript.react","version":"7.80.0"}}
{"type":"session"}
{"sid":"43320568f73c48ffbcb6d7520779bc83","init":true,"started":"2025-08-11T07:57:26.909Z","timestamp":"2025-08-11T07:57:26.909Z","status":"ok","errors":0,"attrs":{"release":"1.20.7","environment":"bulenox-prod","user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}}'

# To convert this to Python code:
# 1. Install curlconverter: pip install curlconverter
# 2. Use: from curlconverter import convert; print(convert('''curl_command_here'''))
# Or use an online converter like https://curl.trillworks.com

# Example Python requests code structure:
# import requests
# 
# headers = {
#     # Headers from the curl command
# }
# 
# data = {
#     # Data from the curl command
# }
# 
# response = requests.post('URL_FROM_CURL', headers=headers, json=data)
# print(response.text)
