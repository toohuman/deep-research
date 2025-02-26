import os
import httpx
import asyncio
from typing import Dict, Any, Optional, List

class FirecrawlApp:
    """Python implementation of FirecrawlApp similar to the TypeScript version."""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize the FirecrawlApp with API key and optional base URL."""
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FirecrawlApp requires an API key")

        self.api_url = api_url or "https://api.firecrawl.dev/v1"

    async def search(self, query: str, timeout: int = 15000, limit: int = 5,
                    scrapeOptions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search the web using Firecrawl API.

        Args:
            query: The search query
            timeout: Timeout in milliseconds
            limit: Maximum number of results
            scrapeOptions: Options for scraping

        Returns:
            Search response as a dictionary
        """
        url = f"{self.api_url}/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "query": query,
            "timeout": timeout,
            "limit": limit,
            "scrapeOptions": scrapeOptions or {"formats": ["markdown"]},
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def map_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map a website URL using Firecrawl API.

        Args:
            url: The website URL to map
            params: Additional parameters

        Returns:
            Mapping response as a dictionary
        """
        endpoint = f"{self.api_url}/map"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "url": url,
            **(params or {})
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(endpoint, json=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def scrape_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scrape a specific URL using Firecrawl API.

        Args:
            url: The URL to scrape
            params: Additional parameters

        Returns:
            Scraping response as a dictionary
        """
        endpoint = f"{self.api_url}/scrape"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "url": url,
            **(params or {})
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(endpoint, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
