"""Base class for deep research providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ultra_search.core.models import ResearchResult


class BaseResearchProvider(ABC):
    """Abstract base class for deep research providers."""

    provider_name: str = "base"
    requires_auth: bool = True

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize provider.

        Args:
            api_key: API key for authentication
            **kwargs: Additional configuration
        """
        self.api_key = api_key

    @abstractmethod
    async def research(
        self,
        query: str,
        depth: str = "standard",
        include_sources: bool = True,
        **kwargs: Any,
    ) -> ResearchResult:
        """Perform deep research on a query.

        Args:
            query: Research question or topic
            depth: Research depth (quick, standard, comprehensive)
            include_sources: Whether to include source citations
            **kwargs: Additional parameters

        Returns:
            ResearchResult with findings
        """
        pass

    async def close(self) -> None:
        """Clean up resources."""
        pass

    async def __aenter__(self) -> "BaseResearchProvider":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
