"""Regulatory compliance providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ultra_search.core.config import Settings

from ultra_search.core.base import BaseProvider


def get_regulatory_provider(provider_name: str, settings: "Settings") -> BaseProvider:
    """Get a regulatory compliance provider instance.

    Args:
        provider_name: Name of provider (fmcsa, middesk)
        settings: Application settings

    Returns:
        Initialized provider instance
    """
    providers = {}

    # Lazy import providers
    if provider_name == "fmcsa":
        from ultra_search.domains.regulatory_compliance.providers.fmcsa import FMCSAProvider
        providers["fmcsa"] = FMCSAProvider
    elif provider_name == "middesk":
        from ultra_search.domains.regulatory_compliance.providers.middesk import MiddeskProvider
        providers["middesk"] = MiddeskProvider

    if provider_name not in providers:
        raise ValueError(
            f"Unknown regulatory provider: {provider_name}. "
            f"Available: fmcsa, middesk"
        )

    provider_cls = providers[provider_name]
    api_key = settings.get_api_key(provider_name, domain="regulatory_compliance")

    return provider_cls(api_key=api_key)


__all__ = [
    "get_regulatory_provider",
]
