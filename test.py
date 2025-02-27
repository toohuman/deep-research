import requests

import requests
import os
from dotenv import load_dotenv

url = "https://api.firecrawl.dev/v1/search"
query = "mac book air m4"
# Load environment variables
load_dotenv('.env.local')

# Retrieve API keys from environment variables
firecrawl_api_key = os.getenv("FIRECRAWL_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

payload = {
    "query": "What is the meaning of life?",
    "limit": 5,
    "tbs": "<string>",
    "lang": "en",
    "country": "us",
    "location": "<string>",
    "timeout": 60000,
    "scrapeOptions": {}
}
headers = {
    "Authorization": f"Bearer {firecrawl_api_key}",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)