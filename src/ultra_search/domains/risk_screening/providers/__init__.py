"""Risk screening providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ultra_search.core.config import Settings

from ultra_search.core.base import BaseProvider


def get_risk_provider(provider_name: str, settings: "Settings") -> BaseProvider:
    """Get a risk screening provider instance.

    Args:
        provider_name: Name of provider (opensanctions, newsapi, gdelt)
        settings: Application settings

    Returns:
        Initialized provider instance
    """
    providers = {}

    if provider_name == "opensanctions":
        from ultra_search.domains.risk_screening.providers.opensanctions import (
            OpenSanctionsProvider,
        )
        providers["opensanctions"] = OpenSanctionsProvider
    elif provider_name == "newsapi":
        from ultra_search.domains.risk_screening.providers.newsapi import NewsAPIProvider
        providers["newsapi"] = NewsAPIProvider

    if provider_name not in providers:
        raise ValueError(
            f"Unknown risk screening provider: {provider_name}. "
            f"Available: opensanctions, newsapi"
        )

    provider_cls = providers[provider_name]
    api_key = settings.get_api_key(provider_name, domain="risk_screening")
    return provider_cls(api_key=api_key)


__all__ = ["get_risk_provider"]
