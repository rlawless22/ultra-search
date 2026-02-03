"""Mock search provider for testing without API keys."""

from __future__ import annotations

from typing import Any

from ultra_search.core.models import SearchResult, ResultType
from ultra_search.domains.web_search.providers.base import BaseSearchProvider


class MockSearchProvider(BaseSearchProvider):
    """Mock search provider that returns fake results.

    Useful for:
    - Testing without API keys
    - Development and debugging
    - Demonstrating the system
    """

    provider_name = "mock"
    base_url = ""
    requires_auth = False

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Return mock search results.

        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search

        Returns:
            List of mock search results
        """
        results = []

        for i in range(min(num_results, 5)):
            result_type = ResultType.NEWS_ARTICLE if search_type == "news" else ResultType.WEB_PAGE

            results.append(
                SearchResult(
                    title=f"Mock Result {i + 1}: {query}",
                    url=f"https://example.com/result/{i + 1}?q={query.replace(' ', '+')}",
                    snippet=f"This is a mock search result for '{query}'. "
                            f"In production, this would contain real content from {self.provider_name}.",
                    result_type=result_type,
                    source=self.provider_name,
                    relevance_score=1.0 - (i * 0.1),
                    metadata={
                        "mock": True,
                        "position": i + 1,
                        "search_type": search_type,
                    },
                )
            )

        return results
