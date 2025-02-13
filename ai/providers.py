from dotenv import load_dotenv
load_dotenv('.env.local')
import os
import openai
from openai import ChatCompletion
import json
import asyncio
import httpx

# Retrieve OpenAI API key from environment variables.
# Try OPENAI_API_KEY first, then fallback to OPENAI_KEY.
api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
if not api_key or api_key == "sk-dummy-key":
    raise ValueError("A valid OpenAI API key must be set in the environment variable. Provided key is invalid.")

openai.api_key = api_key

# Instantiate the client with your API key.
from openai import OpenAI
client = OpenAI(api_key=api_key)

async def generate_object(*, model, system, prompt, schema):
    """
    Calls the OpenAI ChatCompletion API using the new interface.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    # Use the new client method via asyncio.to_thread to avoid blocking.
    response = await asyncio.to_thread(client.chat.completions.create, model=model, messages=messages)
    content = response.choices[0].message.content
    # If the schema expects a reportMarkdown field, return the raw content.
    if "reportMarkdown" in schema.get("properties", {}):
        return {"object": {"reportMarkdown": content}}
    try:
        parsed = json.loads(content)
    except Exception as e:
        import re
        # Attempt to extract numbered list segments from the response regardless of leading text.
        matches = re.findall(r"(?m)^\s*\d+\.\s*(.*)$", content)
        if matches:
            parsed = {"questions": [match.strip() for match in matches if match.strip()]}
        else:
            raise ValueError(f"Failed to parse response as JSON or extract numbered list items: {e}\nResponse content: {content}")
    return {"object": parsed}

def o3_mini_model(model_name, **kwargs):
    """
    Returns the model name. In this implementation, the model identifier is simply a string.
    """
    return model_name

o3_mini_model = o3_mini_model("o3-mini-2025-01-31") #o3-mini-2025-01-31, gpt-3.5-turbo

def system_prompt():
    from prompt import system_prompt as sys_prompt
    return sys_prompt()

def trim_prompt(prompt, context_size=128000):
    if len(prompt) <= context_size:
        return prompt
    return prompt[:context_size]

class FirecrawlApp:
    def __init__(self, api_key="", api_url=None):
        self.api_key = api_key or os.getenv("FIRECRAWL_KEY")
        const_url = os.getenv("FIRECRAWL_BASE_URL")
        if (not const_url) or const_url.strip() == "":
            print("Warning: FIRECRAWL_BASE_URL not provided. Using http://localhost:3002 for testing.")
            self.api_url = "http://localhost:3002"
        else:
            self.api_url = api_url or const_url

    async def search(self, query, timeout, limit, scrapeOptions):
        """
        Makes an HTTP GET request to the Firecrawl API endpoint (FIRECRAWL_BASE_URL) to perform a search.
        If using the default local testing URL, returns a dummy response.
        """
        params = {
            "query": query,
            "limit": limit,
            "formats": ",".join(scrapeOptions.get("formats", []))
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        # If the URL does not start with 'http://' or 'https://', consider it invalid and return a dummy response.
        if not (self.api_url.startswith("http://") or self.api_url.startswith("https://")):
            print("Warning: Firecrawl API URL is invalid. Returning dummy search response.")
            return {"data": []}
        # If using a local testing URL, return a dummy response.
        if self.api_url == "dummy":
            print("Warning: Dummy search response returned.")
            return {"data": [{"markdown": f"Dummy content for query: {query}", "url": f"http://dummy.com/{query.replace(' ', '_')}" }]}
        if "localhost" in self.api_url.lower():
            print("Warning: Dummy search response returned.")
            return {"data": [{"markdown": f"Dummy content for query: {query}", "url": f"http://dummy.com/{query.replace(' ', '_')}" }]}
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Ensure the URL ends with '/search'
            url = self.api_url if self.api_url.endswith("/search") else f"{self.api_url}/search"
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
