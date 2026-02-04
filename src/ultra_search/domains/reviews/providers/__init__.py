"""Reviews providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ultra_search.core.config import Settings

from ultra_search.core.base import BaseProvider


def get_reviews_provider(provider_name: str, settings: "Settings") -> BaseProvider:
    """Get a reviews provider instance.

    Args:
        provider_name: Name of provider (google_places, yelp)
        settings: Application settings

    Returns:
        Initialized provider instance
    """
    providers = {}

    if provider_name == "google_places" or provider_name == "google":
        from ultra_search.domains.reviews.providers.google_places import GooglePlacesProvider
        providers["google_places"] = GooglePlacesProvider
        providers["google"] = GooglePlacesProvider
    elif provider_name == "yelp":
        from ultra_search.domains.reviews.providers.yelp import YelpProvider
        providers["yelp"] = YelpProvider

    if provider_name not in providers:
        raise ValueError(
            f"Unknown reviews provider: {provider_name}. "
            f"Available: google_places, yelp"
        )

    provider_cls = providers[provider_name]

    # Handle both google_places and google_places_api_key
    if provider_name in ["google_places", "google"]:
        api_key = settings.get_api_key("google_places", domain="reviews")
    else:
        api_key = settings.get_api_key(provider_name, domain="reviews")

    return provider_cls(api_key=api_key)


__all__ = ["get_reviews_provider"]
