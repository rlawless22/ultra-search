"""SerpAPI search provider.

SerpAPI provides structured Google search results.
Docs: https://serpapi.com/search-api
"""

from __future__ import annotations

from typing import Any

from ultra_search.core.models import SearchResult, ResultType
from ultra_search.domains.web_search.providers.base import BaseSearchProvider


class SerpAPIProvider(BaseSearchProvider):
    """SerpAPI Google Search provider.

    Provides access to Google search results through SerpAPI.
    Supports web, news, images, and more.
    """

    provider_name = "serpapi"
    base_url = "https://serpapi.com"
    requires_auth = True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search using SerpAPI.

        Args:
            query: Search query
            num_results: Number of results
            search_type: Type of search (web, news, images)

        Returns:
            List of search results
        """
        if not self.api_key:
            raise ValueError("SerpAPI requires an API key. Set ULTRA_SERPAPI_API_KEY.")

        client = await self.get_client()

        # Map search type to SerpAPI engine
        engine_map = {
            "web": "google",
            "news": "google_news",
            "images": "google_images",
        }
        engine = engine_map.get(search_type, "google")

        params = {
            "api_key": self.api_key,
            "engine": engine,
            "q": query,
            "num": num_results,
        }
        params.update(kwargs)

        response = await client.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        data = response.json()

        return self._parse_results(data, search_type)

    def _parse_results(self, data: dict[str, Any], search_type: str) -> list[SearchResult]:
        """Parse SerpAPI response into SearchResult objects."""
        results = []

        # Handle different result types
        if search_type == "news":
            items = data.get("news_results", [])
        elif search_type == "images":
            items = data.get("images_results", [])
        else:
            items = data.get("organic_results", [])

        for item in items:
            result_type = ResultType.NEWS_ARTICLE if search_type == "news" else ResultType.WEB_PAGE

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", item.get("original", "")),
                    snippet=item.get("snippet", item.get("source", "")),
                    result_type=result_type,
                    source=self.provider_name,
                    metadata={
                        "position": item.get("position"),
                        "displayed_link": item.get("displayed_link"),
                        "thumbnail": item.get("thumbnail"),
                    },
                )
            )

        return results
