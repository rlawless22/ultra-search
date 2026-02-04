"""Yelp Fusion API provider for reviews.

Yelp Fusion provides business search and review data.
Docs: https://docs.developer.yelp.com/

Setup:
1. Create app at https://www.yelp.com/developers/v3/manage_app
2. Get API key
3. Set: ULTRA_YELP_API_KEY
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ultra_search.core.base import BaseProvider
from ultra_search.domains.reviews.domain import BusinessReviewsSummary, Review


class YelpProvider(BaseProvider):
    """Yelp Fusion API provider.

    API Key: Free tier available, register at https://www.yelp.com/developers
    Rate Limits: 500 calls/day (free tier)
    """

    provider_name = "yelp"
    base_url = "https://api.yelp.com/v3"
    requires_auth = True

    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with API key."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Yelp requires an API key. "
                    "Get one at: https://www.yelp.com/developers/v3/manage_app "
                    "Then set: ULTRA_YELP_API_KEY"
                )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make authenticated request to Yelp API."""
        client = await self.get_client()
        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_reviews(
        self,
        business_name: str,
        location: str | None = None,
        phone: str | None = None,
        max_reviews: int = 20,
    ) -> BusinessReviewsSummary:
        """Get Yelp reviews for a business.

        Args:
            business_name: Name of business
            location: City, State or ZIP code
            phone: Phone number for matching
            max_reviews: Max reviews (Yelp limits to 3 per business via API)

        Returns:
            Business reviews summary
        """
        # Step 1: Search for business
        business_id = await self._find_business(business_name, location, phone)

        if not business_id:
            return BusinessReviewsSummary(
                business_name=business_name,
                platform="yelp",
                total_reviews=0,
                metadata={"error": "Business not found"},
            )

        # Step 2: Get business details
        business_details = await self._get_business_details(business_id)

        # Step 3: Get reviews (limited to 3 by Yelp API)
        reviews_data = await self._get_business_reviews(business_id)

        return self._parse_reviews(business_details, reviews_data)

    async def _find_business(
        self,
        name: str,
        location: str | None = None,
        phone: str | None = None,
    ) -> str | None:
        """Find Yelp business ID.

        Uses Business Search endpoint.
        """
        params = {"term": name, "limit": 5}

        if location:
            params["location"] = location

        if phone:
            params["phone"] = phone

        data = await self._make_request("GET", "/businesses/search", params=params)

        businesses = data.get("businesses", [])
        if businesses:
            # Return first match
            return businesses[0].get("id")

        return None

    async def _get_business_details(self, business_id: str) -> dict:
        """Get business details including overall ratings."""
        return await self._make_request("GET", f"/businesses/{business_id}")

    async def _get_business_reviews(self, business_id: str) -> dict:
        """Get business reviews.

        Note: Yelp API limits to 3 reviews per business.
        For full review access, would need web scraping (against ToS) or
        Yelp partnership.
        """
        return await self._make_request("GET", f"/businesses/{business_id}/reviews")

    def _parse_reviews(
        self,
        business: dict[str, Any],
        reviews_data: dict[str, Any],
    ) -> BusinessReviewsSummary:
        """Parse Yelp API responses into reviews summary."""
        reviews_list: list[Review] = []

        for review_data in reviews_data.get("reviews", []):
            # Parse timestamp
            timestamp = None
            time_created = review_data.get("time_created")
            if time_created:
                try:
                    timestamp = datetime.fromisoformat(time_created.replace("Z", "+00:00"))
                except Exception:
                    pass

            user = review_data.get("user", {})

            reviews_list.append(
                Review(
                    author_name=user.get("name", "Anonymous"),
                    rating=float(review_data.get("rating", 0)),
                    text=review_data.get("text"),
                    timestamp=timestamp,
                    platform="yelp",
                    author_review_count=user.get("review_count"),
                    metadata={
                        "url": review_data.get("url"),
                        "user_profile_url": user.get("profile_url"),
                    },
                )
            )

        # Calculate distribution
        distribution = {}
        for review in reviews_list:
            rating_str = str(int(review.rating))
            distribution[rating_str] = distribution.get(rating_str, 0) + 1

        # Format address
        location = business.get("location", {})
        address_parts = [
            location.get("address1"),
            location.get("city"),
            location.get("state"),
            location.get("zip_code"),
        ]
        formatted_address = ", ".join([p for p in address_parts if p])

        return BusinessReviewsSummary(
            business_name=business.get("name", ""),
            platform="yelp",
            average_rating=business.get("rating"),
            total_reviews=business.get("review_count", len(reviews_list)),
            reviews=reviews_list,
            rating_distribution=distribution,
            suspicious_patterns=[],  # Could add pattern detection here
            address=formatted_address or None,
            phone=business.get("display_phone"),
            website=business.get("url"),
            metadata={
                "business_id": business.get("id"),
                "is_closed": business.get("is_closed"),
                "categories": business.get("categories", []),
                "note": "Yelp API limits to 3 reviews per business via API",
            },
        )
