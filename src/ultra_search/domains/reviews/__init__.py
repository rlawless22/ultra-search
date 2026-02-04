"""Reviews & Reputation domain - Multi-platform review aggregation.

Providers:
- google_places: Google Places API (reviews and ratings)
- yelp: Yelp Fusion API (reviews and business data)

Tools:
- search_google_reviews: Get Google reviews for a business
- search_yelp_reviews: Get Yelp reviews for a business
- aggregate_reviews: Get reviews from all platforms

Note: Reviews should be treated as signals, not truth. Watch for:
- Time clustering (fake review campaigns)
- Repeated phrasing
- Suspicious reviewer profiles
"""

from ultra_search.domains.reviews import domain  # noqa: F401

__all__ = []
