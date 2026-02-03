"""Web search providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ultra_search.core.config import Settings

from ultra_search.domains.web_search.providers.base import BaseSearchProvider
from ultra_search.domains.web_search.providers.mock import MockSearchProvider


def get_search_provider(provider_name: str, settings: "Settings") -> BaseSearchProvider:
    """Get a search provider instance by name.

    Args:
        provider_name: Name of the provider (serpapi, tavily, brave, parallel, mock)
        settings: Application settings for API keys

    Returns:
        Initialized provider instance
    """
    providers = {
        "mock": MockSearchProvider,
    }

    # Lazy import optional providers
    if provider_name == "serpapi":
        from ultra_search.domains.web_search.providers.serpapi import SerpAPIProvider
        providers["serpapi"] = SerpAPIProvider
    elif provider_name == "tavily":
        from ultra_search.domains.web_search.providers.tavily import TavilyProvider
        providers["tavily"] = TavilyProvider
    elif provider_name == "brave":
        from ultra_search.domains.web_search.providers.brave import BraveSearchProvider
        providers["brave"] = BraveSearchProvider
    elif provider_name == "parallel":
        from ultra_search.domains.web_search.providers.parallel import ParallelSearchProvider
        providers["parallel"] = ParallelSearchProvider

    if provider_name not in providers:
        raise ValueError(
            f"Unknown search provider: {provider_name}. "
            f"Available: {list(providers.keys())}"
        )

    provider_cls = providers[provider_name]
    api_key = settings.get_api_key(provider_name, domain="web_search")

    return provider_cls(api_key=api_key)


__all__ = [
    "BaseSearchProvider",
    "MockSearchProvider",
    "get_search_provider",
]
