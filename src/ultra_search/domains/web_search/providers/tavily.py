"""Tavily AI search provider.

Tavily provides AI-powered search optimized for LLMs.
Docs: https://docs.tavily.com/
"""

from __future__ import annotations

from typing import Any

from ultra_search.core.models import SearchResult, ResultType
from ultra_search.domains.web_search.providers.base import BaseSearchProvider


class TavilyProvider(BaseSearchProvider):
    """Tavily AI-powered search provider.

    Tavily is designed for AI agents and provides:
    - AI-optimized search results
    - Content extraction
    - Answer generation
    """

    provider_name = "tavily"
    base_url = "https://api.tavily.com"
    requires_auth = True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search using Tavily API.

        Args:
            query: Search query
            num_results: Number of results
            search_type: Type of search

        Returns:
            List of search results
        """
        if not self.api_key:
            raise ValueError("Tavily requires an API key. Set ULTRA_TAVILY_API_KEY.")

        client = await self.get_client()

        # Map search type to Tavily topic
        topic_map = {
            "web": "general",
            "news": "news",
        }
        topic = topic_map.get(search_type, "general")

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": num_results,
            "topic": topic,
            "include_answer": kwargs.get("include_answer", False),
            "include_raw_content": kwargs.get("include_raw_content", False),
        }

        response = await client.post(f"{self.base_url}/search", json=payload)
        response.raise_for_status()
        data = response.json()

        return self._parse_results(data, search_type)

    def _parse_results(self, data: dict[str, Any], search_type: str) -> list[SearchResult]:
        """Parse Tavily response into SearchResult objects."""
        results = []

        for item in data.get("results", []):
            result_type = ResultType.NEWS_ARTICLE if search_type == "news" else ResultType.WEB_PAGE

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    content=item.get("raw_content"),
                    result_type=result_type,
                    source=self.provider_name,
                    relevance_score=item.get("score"),
                    metadata={
                        "published_date": item.get("published_date"),
                    },
                )
            )

        return results
