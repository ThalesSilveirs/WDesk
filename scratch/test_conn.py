import requests
import sys

url = "http://evolution-go:8080/instance/all"
headers = {"apikey": "your-token-here"}

try:
    print(f"Testing connection to {url}...")
    response = requests.get(url, headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
