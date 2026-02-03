"""Brave Search API provider.

Brave Search provides privacy-focused web search.
Docs: https://brave.com/search/api/
"""

from __future__ import annotations

from typing import Any

from ultra_search.core.models import SearchResult, ResultType
from ultra_search.domains.web_search.providers.base import BaseSearchProvider


class BraveSearchProvider(BaseSearchProvider):
    """Brave Search API provider.

    Privacy-focused search engine with:
    - Web search
    - News search
    - No user tracking
    """

    provider_name = "brave"
    base_url = "https://api.search.brave.com/res/v1"
    requires_auth = True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search using Brave Search API.

        Args:
            query: Search query
            num_results: Number of results
            search_type: Type of search (web, news)

        Returns:
            List of search results
        """
        if not self.api_key:
            raise ValueError("Brave Search requires an API key. Set ULTRA_BRAVE_API_KEY.")

        client = await self.get_client()

        # Determine endpoint
        endpoint = "/news/search" if search_type == "news" else "/web/search"

        params = {
            "q": query,
            "count": num_results,
        }
        params.update(kwargs)

        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json",
        }

        response = await client.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        return self._parse_results(data, search_type)

    def _parse_results(self, data: dict[str, Any], search_type: str) -> list[SearchResult]:
        """Parse Brave Search response into SearchResult objects."""
        results = []

        # Get results based on search type
        if search_type == "news":
            items = data.get("results", [])
        else:
            web_data = data.get("web", {})
            items = web_data.get("results", [])

        for item in items:
            result_type = ResultType.NEWS_ARTICLE if search_type == "news" else ResultType.WEB_PAGE

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    result_type=result_type,
                    source=self.provider_name,
                    metadata={
                        "age": item.get("age"),
                        "language": item.get("language"),
                        "family_friendly": item.get("family_friendly"),
                    },
                )
            )

        return results
