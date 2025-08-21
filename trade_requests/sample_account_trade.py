# Generated from Bulenox trade request
# Original cURL command:
curl 'https://bulenox.projectx.com/api/trade'   -H 'authority: bulenox.com'   -H 'accept: application/json'   -H 'accept-language: en-US,en;q=0.9'   -H 'authorization: Bearer YOUR_TOKEN_HERE'   -H 'content-type: application/json'   -H 'origin: https://bulenox.projectx.com'   -H 'referer: https://bulenox.projectx.com/trade'   -H 'sec-ch-ua: "Chromium";v="112"'   -H 'sec-ch-ua-mobile: ?0'   -H 'sec-ch-ua-platform: "Windows"'   -H 'sec-fetch-dest: empty'   -H 'sec-fetch-mode: cors'   -H 'sec-fetch-site: same-origin'   -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'   --data-raw '{"symbol":"EURUSD","volume":0.01,"side":"buy","type":"market"}'   --compressed

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
