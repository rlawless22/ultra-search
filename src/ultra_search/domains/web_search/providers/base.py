"""Base class for web search providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from ultra_search.core.models import SearchResult


class BaseSearchProvider(ABC):
    """Abstract base class for web search providers."""

    provider_name: str = "base"
    base_url: str = ""
    requires_auth: bool = True

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize provider.

        Args:
            api_key: API key for authentication
            **kwargs: Additional provider configuration
        """
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Perform a search.

        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search (web, news, images)
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        pass

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseSearchProvider":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
