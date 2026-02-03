"""Parallel AI Search API provider.

Parallel provides AI-native web search with token-efficient results.
Docs: https://docs.parallel.ai/
"""

from __future__ import annotations

from typing import Any

from ultra_search.core.models import SearchResult, ResultType
from ultra_search.domains.web_search.providers.base import BaseSearchProvider


class ParallelSearchProvider(BaseSearchProvider):
    """Parallel AI Search API provider.

    Purpose-built search API for AI agents with:
    - Token-efficient results
    - JavaScript-rendered content handling
    - Complex PDF extraction
    - Evidence-based results
    """

    provider_name = "parallel"
    base_url = "https://api.parallel.ai"
    requires_auth = True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search using Parallel AI Search API.

        Args:
            query: Search query
            num_results: Number of results (default 10)
            search_type: Type of search (web, news)
            **kwargs: Additional parameters

        Returns:
            List of search results
        """
        if not self.api_key:
            raise ValueError("Parallel AI requires an API key. Set ULTRA_PARALLEL_API_KEY.")

        client = await self.get_client()

        # Prepare request payload
        payload = {
            "query": query,
            "num_results": num_results,
            "search_type": search_type,
        }
        payload.update(kwargs)

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        response = await client.post(
            f"{self.base_url}/v1/search",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        return self._parse_results(data, search_type)

    def _parse_results(self, data: dict[str, Any], search_type: str) -> list[SearchResult]:
        """Parse Parallel AI response into SearchResult objects."""
        results = []

        # Extract results from response
        items = data.get("results", [])

        for item in items:
            result_type = ResultType.NEWS_ARTICLE if search_type == "news" else ResultType.WEB_PAGE

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    content=item.get("content"),  # Full content if available
                    result_type=result_type,
                    source=self.provider_name,
                    relevance_score=item.get("score"),
                    metadata={
                        "token_count": item.get("token_count"),
                        "domain": item.get("domain"),
                        "published_date": item.get("published_date"),
                        "author": item.get("author"),
                    },
                )
            )

        return results
