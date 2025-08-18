import uncurl

# Test uncurl functionality
curl_command = 'curl -X POST https://example.com -H "Content-Type: application/json" -d "{\"test\": \"data\"}"'
result = uncurl.parse(curl_command)
print("Uncurl result:")
print(result)
print("\nType:", type(result))