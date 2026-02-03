"""Deep research providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ultra_search.core.config import Settings

from ultra_search.domains.deep_research.providers.base import BaseResearchProvider


def get_research_provider(provider_name: str, settings: "Settings") -> BaseResearchProvider:
    """Get a research provider instance by name.

    Args:
        provider_name: Name of the provider (openai, perplexity)
        settings: Application settings for API keys

    Returns:
        Initialized provider instance
    """
    providers = {}

    # Lazy import providers
    if provider_name == "openai":
        from ultra_search.domains.deep_research.providers.openai_provider import (
            OpenAIResearchProvider,
        )
        providers["openai"] = OpenAIResearchProvider
    elif provider_name == "perplexity":
        from ultra_search.domains.deep_research.providers.perplexity import (
            PerplexityProvider,
        )
        providers["perplexity"] = PerplexityProvider

    if provider_name not in providers:
        raise ValueError(
            f"Unknown research provider: {provider_name}. "
            f"Available: openai, perplexity"
        )

    provider_cls = providers[provider_name]
    api_key = settings.get_api_key(provider_name, domain="deep_research")

    return provider_cls(api_key=api_key)


__all__ = [
    "BaseResearchProvider",
    "get_research_provider",
]
