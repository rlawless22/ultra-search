"""Google Places API provider for reviews.

Google Places API provides access to business information and reviews.
Docs: https://developers.google.com/maps/documentation/places/web-service

Setup:
1. Create project in Google Cloud Console
2. Enable Places API
3. Create API key
4. Set: ULTRA_GOOGLE_PLACES_API_KEY
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ultra_search.core.base import BaseProvider
from ultra_search.domains.reviews.domain import BusinessReviewsSummary, Review


class GooglePlacesProvider(BaseProvider):
    """Google Places API provider.

    API Key: Requires Google Cloud Platform API key with Places API enabled
    Pricing: Pay-per-request, see https://mapsplatform.google.com/pricing/
    """

    provider_name = "google_places"
    base_url = "https://maps.googleapis.com/maps/api/place"
    requires_auth = True

    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Google Places requires an API key. "
                    "Get one at: https://console.cloud.google.com/ "
                    "Enable Places API, then set: ULTRA_GOOGLE_PLACES_API_KEY"
                )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make authenticated request (API key via params)."""
        client = await self.get_client()

        # Add API key to params
        params = kwargs.get("params", {})
        params["key"] = self.api_key
        kwargs["params"] = params

        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_reviews(
        self,
        business_name: str,
        address: str | None = None,
        phone: str | None = None,
        max_reviews: int = 20,
    ) -> BusinessReviewsSummary:
        """Get Google reviews for a business.

        Args:
            business_name: Name of business
            address: Optional address for matching
            phone: Optional phone for matching
            max_reviews: Max reviews to retrieve

        Returns:
            Business reviews summary
        """
        # Step 1: Find the business (Place ID)
        place_id = await self._find_place(business_name, address)

        if not place_id:
            # Return empty summary if not found
            return BusinessReviewsSummary(
                business_name=business_name,
                platform="google",
                total_reviews=0,
                metadata={"error": "Business not found"},
            )

        # Step 2: Get Place Details with reviews
        details = await self._get_place_details(place_id, max_reviews)

        return self._parse_reviews(details, business_name)

    async def _find_place(
        self,
        business_name: str,
        address: str | None = None,
    ) -> str | None:
        """Find place_id for a business.

        Uses Find Place API to search by name and optional address.
        """
        query = business_name
        if address:
            query += f", {address}"

        data = await self._make_request(
            "GET",
            "/findplacefromtext/json",
            params={
                "input": query,
                "inputtype": "textquery",
                "fields": "place_id,name",
            },
        )

        candidates = data.get("candidates", [])
        if candidates:
            return candidates[0].get("place_id")

        return None

    async def _get_place_details(self, place_id: str, max_reviews: int) -> dict:
        """Get detailed place information including reviews.

        Uses Place Details API with fields mask for reviews.
        """
        fields = [
            "name",
            "formatted_address",
            "formatted_phone_number",
            "rating",
            "user_ratings_total",
            "reviews",
            "website",
        ]

        data = await self._make_request(
            "GET",
            "/details/json",
            params={
                "place_id": place_id,
                "fields": ",".join(fields),
            },
        )

        return data.get("result", {})

    def _parse_reviews(
        self,
        place_data: dict[str, Any],
        business_name: str,
    ) -> BusinessReviewsSummary:
        """Parse Google Places API response into reviews summary."""
        reviews_list: list[Review] = []
        reviews_data = place_data.get("reviews", [])

        for review_data in reviews_data:
            # Parse timestamp
            timestamp = None
            if "time" in review_data:
                timestamp = datetime.fromtimestamp(review_data["time"])

            reviews_list.append(
                Review(
                    author_name=review_data.get("author_name", "Anonymous"),
                    rating=float(review_data.get("rating", 0)),
                    text=review_data.get("text"),
                    timestamp=timestamp,
                    platform="google",
                    author_review_count=review_data.get("author_review_count"),
                    metadata={
                        "author_url": review_data.get("author_url"),
                        "profile_photo_url": review_data.get("profile_photo_url"),
                        "relative_time": review_data.get("relative_time_description"),
                    },
                )
            )

        # Calculate rating distribution
        distribution = {}
        for review in reviews_list:
            rating_str = str(int(review.rating))
            distribution[rating_str] = distribution.get(rating_str, 0) + 1

        # Detect suspicious patterns
        suspicious = []
        if len(reviews_list) > 10:
            # Check for time clustering (many reviews in short time)
            timestamps = [r.timestamp for r in reviews_list if r.timestamp]
            if len(timestamps) > 5:
                timestamps.sort()
                # Check if > 30% of reviews are within 7 days
                from datetime import timedelta
                for i in range(len(timestamps) - 3):
                    window = timestamps[i:i+4]
                    if window[-1] - window[0] < timedelta(days=7):
                        suspicious.append("Time clustering detected (4+ reviews within 7 days)")
                        break

        return BusinessReviewsSummary(
            business_name=place_data.get("name", business_name),
            platform="google",
            average_rating=place_data.get("rating"),
            total_reviews=place_data.get("user_ratings_total", len(reviews_list)),
            reviews=reviews_list,
            rating_distribution=distribution,
            suspicious_patterns=suspicious,
            address=place_data.get("formatted_address"),
            phone=place_data.get("formatted_phone_number"),
            website=place_data.get("website"),
            metadata={"place_id": place_data.get("place_id")},
        )
