import requests

url = "http://localhost:8000/chatbot/ask"
# We need a token to test, but let's see if we get a 401 (meaning the endpoint exists)
# Or a 404 (meaning the endpoint doesn't exist)
payload = {"message": "test"}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Connection Failed: {str(e)}")
