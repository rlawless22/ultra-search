"""Reviews domain tools for multi-platform review aggregation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.registry import register_tool


# === DATA MODELS ===


class Review(BaseModel):
    """A single review from any platform."""

    author_name: str
    rating: float  # 1-5 scale
    text: str | None = None
    timestamp: datetime | None = None
    platform: str  # google, yelp, trustpilot, etc.

    # Fraud detection signals
    author_review_count: int | None = None  # Total reviews by author
    verified_purchase: bool | None = None
    helpful_votes: int | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class BusinessReviewsSummary(BaseModel):
    """Aggregated review data for a business."""

    business_name: str
    platform: str
    average_rating: float | None = None
    total_reviews: int
    reviews: list[Review] = Field(default_factory=list)

    # Distribution
    rating_distribution: dict[str, int] = Field(default_factory=dict)  # "5": count, "4": count...

    # Fraud signals
    suspicious_patterns: list[str] = Field(default_factory=list)

    # Location info
    address: str | None = None
    phone: str | None = None
    website: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


# === INPUT/OUTPUT MODELS ===


class SearchGoogleReviewsInput(BaseModel):
    """Input for Google reviews search."""

    business_name: str = Field(..., description="Business name")
    address: str | None = Field(None, description="Business address for matching")
    phone: str | None = Field(None, description="Phone number for matching")
    max_reviews: int = Field(default=20, ge=1, le=100, description="Max reviews to retrieve")

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class SearchGoogleReviewsOutput(BaseModel):
    """Output from Google reviews search."""

    reviews_summary: BusinessReviewsSummary
    place_id: str | None = None  # Google Place ID for reference
    output_file_path: str | None = None


class SearchYelpReviewsInput(BaseModel):
    """Input for Yelp reviews search."""

    business_name: str = Field(..., description="Business name")
    location: str | None = Field(None, description="City, State or ZIP")
    phone: str | None = Field(None, description="Phone for matching")
    max_reviews: int = Field(default=20, ge=1, le=100, description="Max reviews")

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class SearchYelpReviewsOutput(BaseModel):
    """Output from Yelp reviews search."""

    reviews_summary: BusinessReviewsSummary
    business_id: str | None = None  # Yelp business ID
    output_file_path: str | None = None


class AggregateReviewsInput(BaseModel):
    """Input for aggregating reviews from all platforms."""

    business_name: str = Field(..., description="Business name")
    address: str | None = Field(None, description="Address for matching")
    phone: str | None = Field(None, description="Phone for matching")
    location: str | None = Field(None, description="City, State")
    platforms: list[str] = Field(
        default=["google", "yelp"],
        description="Platforms to search: google, yelp"
    )

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class AggregateReviewsOutput(BaseModel):
    """Output from aggregating reviews across platforms."""

    business_name: str
    total_reviews: int
    overall_average_rating: float | None = None
    platform_summaries: list[BusinessReviewsSummary] = Field(default_factory=list)

    # Fraud detection summary
    fraud_risk_score: float | None = None  # 0-100
    suspicious_patterns: list[str] = Field(default_factory=list)

    output_file_path: str | None = None


# === TOOLS ===


@register_tool(domain="reviews")
class SearchGoogleReviews(BaseTool[SearchGoogleReviewsInput, SearchGoogleReviewsOutput]):
    """Search Google reviews for a business.

    Uses Google Places API to find a business and retrieve reviews.
    Returns ratings, review text, timestamps, and fraud detection signals.

    Critical for moving company vetting - look for patterns like:
    - "Held my belongings hostage"
    - "Price increased 3x on delivery day"
    - "Damaged furniture"
    - "Never delivered"
    """

    name: ClassVar[str] = "search_google_reviews"
    description: ClassVar[str] = (
        "Search Google reviews for a business. "
        "Returns ratings, review text, and fraud detection signals. "
        "Use for vetting moving companies and service providers."
    )
    domain: ClassVar[str] = "reviews"
    input_model: ClassVar[type[BaseModel]] = SearchGoogleReviewsInput
    output_model: ClassVar[type[BaseModel]] = SearchGoogleReviewsOutput

    async def execute(self, input_data: SearchGoogleReviewsInput) -> SearchGoogleReviewsOutput:
        """Execute Google reviews search."""
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.reviews.providers import get_reviews_provider

        provider = get_reviews_provider("google_places", self.settings)

        reviews_summary = await provider.get_reviews(
            business_name=input_data.business_name,
            address=input_data.address,
            phone=input_data.phone,
            max_reviews=input_data.max_reviews,
        )

        output = SearchGoogleReviewsOutput(
            reviews_summary=reviews_summary,
            place_id=reviews_summary.metadata.get("place_id"),
            output_file_path=None,
        )

        # File output
        if input_data.output_file:
            format_str = input_data.output_format or Path(input_data.output_file).suffix.lstrip(".")
            output_format = OutputFormat(format_str) if format_str in ["json", "md", "txt", "html"] else OutputFormat.JSON

            config = FileOutputConfig(path=input_data.output_file, format=output_format)
            written_path = await write_result_to_file(output, config)
            output.output_file_path = str(written_path)

        return output


@register_tool(domain="reviews")
class SearchYelpReviews(BaseTool[SearchYelpReviewsInput, SearchYelpReviewsOutput]):
    """Search Yelp reviews for a business.

    Uses Yelp Fusion API to find a business and retrieve reviews.
    """

    name: ClassVar[str] = "search_yelp_reviews"
    description: ClassVar[str] = (
        "Search Yelp reviews for a business. "
        "Returns ratings, review text, and business information. "
        "Useful for cross-platform review verification."
    )
    domain: ClassVar[str] = "reviews"
    input_model: ClassVar[type[BaseModel]] = SearchYelpReviewsInput
    output_model: ClassVar[type[BaseModel]] = SearchYelpReviewsOutput

    async def execute(self, input_data: SearchYelpReviewsInput) -> SearchYelpReviewsOutput:
        """Execute Yelp reviews search."""
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.reviews.providers import get_reviews_provider

        provider = get_reviews_provider("yelp", self.settings)

        reviews_summary = await provider.get_reviews(
            business_name=input_data.business_name,
            location=input_data.location,
            phone=input_data.phone,
            max_reviews=input_data.max_reviews,
        )

        output = SearchYelpReviewsOutput(
            reviews_summary=reviews_summary,
            business_id=reviews_summary.metadata.get("business_id"),
            output_file_path=None,
        )

        # File output
        if input_data.output_file:
            format_str = input_data.output_format or Path(input_data.output_file).suffix.lstrip(".")
            output_format = OutputFormat(format_str) if format_str in ["json", "md", "txt", "html"] else OutputFormat.JSON

            config = FileOutputConfig(path=input_data.output_file, format=output_format)
            written_path = await write_result_to_file(output, config)
            output.output_file_path = str(written_path)

        return output


@register_tool(domain="reviews")
class AggregateReviews(BaseTool[AggregateReviewsInput, AggregateReviewsOutput]):
    """Aggregate reviews from multiple platforms in parallel.

    Searches Google, Yelp, and other configured platforms simultaneously,
    analyzes for fraud patterns (time clustering, suspicious phrasing),
    and returns unified view with risk scoring.

    Perfect for comprehensive moving company vetting.
    """

    name: ClassVar[str] = "aggregate_reviews"
    description: ClassVar[str] = (
        "Aggregate reviews from Google, Yelp, and other platforms. "
        "Runs searches in parallel and detects fraud patterns. "
        "Returns unified view with risk scoring. "
        "Ideal for comprehensive carrier vetting."
    )
    domain: ClassVar[str] = "reviews"
    input_model: ClassVar[type[BaseModel]] = AggregateReviewsInput
    output_model: ClassVar[type[BaseModel]] = AggregateReviewsOutput

    async def execute(self, input_data: AggregateReviewsInput) -> AggregateReviewsOutput:
        """Execute multi-platform review aggregation."""
        import asyncio
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.reviews.providers import get_reviews_provider

        # Fetch from all platforms in parallel
        tasks = []
        providers = []

        for platform in input_data.platforms:
            try:
                provider = get_reviews_provider(platform, self.settings)
                providers.append((platform, provider))

                if platform == "google":
                    task = provider.get_reviews(
                        business_name=input_data.business_name,
                        address=input_data.address,
                        phone=input_data.phone,
                    )
                elif platform == "yelp":
                    task = provider.get_reviews(
                        business_name=input_data.business_name,
                        location=input_data.location,
                        phone=input_data.phone,
                    )
                else:
                    continue

                tasks.append(task)
            except Exception:
                # Skip unavailable providers
                continue

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        platform_summaries = []
        total_reviews = 0
        all_ratings = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue  # Skip failed providers

            platform_summaries.append(result)
            total_reviews += result.total_reviews

            if result.average_rating:
                all_ratings.append(result.average_rating)

        # Calculate overall average
        overall_avg = sum(all_ratings) / len(all_ratings) if all_ratings else None

        # Detect fraud patterns
        suspicious_patterns = self._detect_fraud_patterns(platform_summaries)
        fraud_risk = len(suspicious_patterns) * 15.0  # Simple scoring

        output = AggregateReviewsOutput(
            business_name=input_data.business_name,
            total_reviews=total_reviews,
            overall_average_rating=overall_avg,
            platform_summaries=platform_summaries,
            fraud_risk_score=min(fraud_risk, 100.0),
            suspicious_patterns=suspicious_patterns,
            output_file_path=None,
        )

        # File output
        if input_data.output_file:
            format_str = input_data.output_format or Path(input_data.output_file).suffix.lstrip(".")
            output_format = OutputFormat(format_str) if format_str in ["json", "md", "txt", "html"] else OutputFormat.JSON

            config = FileOutputConfig(path=input_data.output_file, format=output_format)
            written_path = await write_result_to_file(output, config)
            output.output_file_path = str(written_path)

        return output

    def _detect_fraud_patterns(
        self, summaries: list[BusinessReviewsSummary]
    ) -> list[str]:
        """Detect potential review fraud patterns.

        Looks for:
        - Suspicious time clustering
        - Rating anomalies
        - Review volume spikes
        """
        patterns = []

        for summary in summaries:
            # Check for suspicious patterns already flagged by provider
            patterns.extend(summary.suspicious_patterns)

            # Check rating distribution
            if summary.rating_distribution:
                five_star = summary.rating_distribution.get("5", 0)
                one_star = summary.rating_distribution.get("1", 0)
                total = sum(summary.rating_distribution.values())

                if total > 0:
                    five_star_pct = (five_star / total) * 100
                    one_star_pct = (one_star / total) * 100

                    # Suspicious if >70% are 5-star
                    if five_star_pct > 70:
                        patterns.append(
                            f"{summary.platform}: {five_star_pct:.0f}% 5-star reviews (possible fake positives)"
                        )

                    # Polarized reviews (lots of 5-star and 1-star, few middle)
                    if five_star_pct > 40 and one_star_pct > 40:
                        patterns.append(
                            f"{summary.platform}: Polarized reviews (possible review manipulation)"
                        )

        return list(set(patterns))  # Deduplicate
