"""NewsAPI provider for adverse media monitoring.

NewsAPI provides news search across thousands of sources.
Docs: https://newsapi.org/docs

Free tier: 100 requests/day
Paid tier: Higher limits

Alternative: GDELT Doc API (completely free, no key required)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from ultra_search.core.base import BaseProvider
from ultra_search.core.models import SearchResult, ResultType
from ultra_search.domains.risk_screening.domain import AdverseMediaResult


class NewsAPIProvider(BaseProvider):
    """NewsAPI provider for adverse media monitoring.

    API Key: Free tier available at https://newsapi.org/
    Set: ULTRA_NEWSAPI_API_KEY

    Note: For production at scale, consider GDELT (no key required) or paid NewsAPI tier.
    """

    provider_name = "newsapi"
    base_url = "https://newsapi.org/v2"
    requires_auth = True

    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "NewsAPI requires an API key. "
                    "Free tier at: https://newsapi.org/register "
                    "Or use GDELT (free, no key). Set: ULTRA_NEWSAPI_API_KEY"
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
        """Make authenticated request (API key via header)."""
        client = await self.get_client()

        # Add API key to headers
        headers = kwargs.get("headers", {})
        headers["X-Api-Key"] = self.api_key
        kwargs["headers"] = headers

        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def search_adverse_media(
        self,
        entity_name: str,
        keywords: list[str] | None = None,
        date_range: str = "past_year",
        max_articles: int = 50,
    ) -> AdverseMediaResult:
        """Search for adverse media about an entity.

        Args:
            entity_name: Business or person name
            keywords: Negative keywords (fraud, scam, etc.)
            date_range: Time range to search
            max_articles: Max articles to retrieve

        Returns:
            Adverse media results with classification
        """
        if keywords is None:
            keywords = ["fraud", "scam", "lawsuit", "investigation", "complaint"]

        # Build search query
        # Example: "ABC Moving" AND (fraud OR scam OR lawsuit OR complaint)
        keyword_query = " OR ".join(keywords)
        query = f'"{entity_name}" AND ({keyword_query})'

        # Date range
        from_date = self._calculate_date_range(date_range)

        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "pageSize": min(max_articles, 100),  # NewsAPI max is 100
            "language": "en",
        }

        # Search everything endpoint
        data = await self._make_request("GET", "/everything", params=params)

        return self._parse_adverse_media(entity_name, data, keywords, date_range)

    def _calculate_date_range(self, range_str: str) -> str:
        """Calculate from_date based on range string."""
        now = datetime.utcnow()

        if range_str == "past_week":
            from_date = now - timedelta(days=7)
        elif range_str == "past_month":
            from_date = now - timedelta(days=30)
        elif range_str == "past_year":
            from_date = now - timedelta(days=365)
        else:
            from_date = now - timedelta(days=365)

        return from_date.strftime("%Y-%m-%d")

    def _parse_adverse_media(
        self,
        entity_name: str,
        data: dict[str, Any],
        keywords: list[str],
        date_range: str,
    ) -> AdverseMediaResult:
        """Parse NewsAPI response and classify adverse media."""
        articles_data = data.get("articles", [])
        total = data.get("totalResults", len(articles_data))

        articles: list[SearchResult] = []
        fraud_count = 0
        scam_count = 0
        lawsuit_count = 0
        investigation_count = 0

        for article in articles_data:
            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")
            full_text = f"{title} {description} {content}".lower()

            # Classify
            if "fraud" in full_text:
                fraud_count += 1
            if "scam" in full_text or "hostage" in full_text:
                scam_count += 1
            if "lawsuit" in full_text or "litigation" in full_text:
                lawsuit_count += 1
            if "investigation" in full_text or "probe" in full_text:
                investigation_count += 1

            # Parse publish date
            published = None
            if article.get("publishedAt"):
                try:
                    published = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            articles.append(
                SearchResult(
                    title=title,
                    url=article.get("url", ""),
                    snippet=description or "",
                    content=content,
                    result_type=ResultType.NEWS_ARTICLE,
                    source=self.provider_name,
                    published_date=published,
                    metadata={
                        "source_name": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                    },
                )
            )

        # Calculate adverse media score (0-100)
        score = 0.0
        score += fraud_count * 15
        score += scam_count * 20
        score += lawsuit_count * 10
        score += investigation_count * 25

        return AdverseMediaResult(
            query=entity_name,
            total_articles=total,
            articles=articles,
            fraud_mentions=fraud_count,
            scam_mentions=scam_count,
            lawsuit_mentions=lawsuit_count,
            investigation_mentions=investigation_count,
            adverse_media_score=min(score, 100.0),
            provider=self.provider_name,
            date_range=date_range,
        )
