"""Risk Screening domain tools for sanctions and adverse media monitoring."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import SearchResult
from ultra_search.core.registry import register_tool


# === DATA MODELS ===


class SanctionsMatch(BaseModel):
    """A single sanctions/watchlist match."""

    entity_name: str
    match_score: float  # 0-1 confidence
    dataset: str  # Which watchlist (OFAC, UN, EU, etc.)
    entity_type: str | None = None  # person, organization, vessel
    aliases: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    listed_date: str | None = None
    reason: str | None = None  # Why sanctioned

    metadata: dict[str, Any] = Field(default_factory=dict)


class SanctionsScreeningResult(BaseModel):
    """Result of sanctions/watchlist screening."""

    query_name: str
    total_matches: int
    matches: list[SanctionsMatch] = Field(default_factory=list)
    highest_match_score: float = 0.0
    risk_level: str = "clear"  # clear, low, medium, high

    provider: str
    screened_datasets: list[str] = Field(default_factory=list)


class AdverseMediaResult(BaseModel):
    """Result of adverse media search."""

    query: str
    total_articles: int
    articles: list[SearchResult] = Field(default_factory=list)

    # Classification
    fraud_mentions: int = 0
    scam_mentions: int = 0
    lawsuit_mentions: int = 0
    investigation_mentions: int = 0

    # Risk assessment
    adverse_media_score: float = 0.0  # 0-100

    provider: str
    date_range: str | None = None


# === INPUT/OUTPUT MODELS ===


class ScreenSanctionsInput(BaseModel):
    """Input for sanctions screening."""

    entity_name: str = Field(..., description="Business or person name to screen")
    entity_type: str = Field(
        default="organization",
        description="Type: organization, person, vessel"
    )
    countries: list[str] = Field(
        default_factory=list,
        description="Optional country filters (e.g., ['US', 'RU'])"
    )
    fuzzy_matching: bool = Field(
        default=True,
        description="Enable fuzzy name matching"
    )

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class ScreenSanctionsOutput(BaseModel):
    """Output from sanctions screening."""

    screening_result: SanctionsScreeningResult
    output_file_path: str | None = None


class SearchAdverseMediaInput(BaseModel):
    """Input for adverse media search."""

    entity_name: str = Field(..., description="Business or person name")
    keywords: list[str] = Field(
        default=["fraud", "scam", "lawsuit", "investigation", "complaint"],
        description="Negative keywords to search for"
    )
    date_range: str = Field(
        default="past_year",
        description="Time range: past_week, past_month, past_year"
    )
    max_articles: int = Field(default=50, ge=1, le=200, description="Max articles")

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class SearchAdverseMediaOutput(BaseModel):
    """Output from adverse media search."""

    adverse_media_result: AdverseMediaResult
    output_file_path: str | None = None


class MonitorEntityRiskInput(BaseModel):
    """Input for combined entity risk monitoring."""

    entity_name: str = Field(..., description="Business or person name")
    address: str | None = Field(None, description="Business address")
    entity_type: str = Field(default="organization", description="organization or person")

    # Screening options
    check_sanctions: bool = Field(default=True, description="Screen watchlists")
    check_adverse_media: bool = Field(default=True, description="Search negative news")

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class MonitorEntityRiskOutput(BaseModel):
    """Output from entity risk monitoring."""

    entity_name: str
    overall_risk_score: float  # 0-100
    risk_level: str  # clear, low, medium, high, critical

    # Results
    sanctions_result: SanctionsScreeningResult | None = None
    adverse_media_result: AdverseMediaResult | None = None

    # Summary
    risk_factors: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    output_file_path: str | None = None


# === TOOLS ===


@register_tool(domain="risk_screening")
class ScreenSanctions(BaseTool[ScreenSanctionsInput, ScreenSanctionsOutput]):
    """Screen entity against sanctions and watchlists.

    Checks against:
    - OFAC (US Treasury sanctions)
    - UN Security Council sanctions
    - EU sanctions
    - UK sanctions
    - Interpol red notices
    - PEP (Politically Exposed Persons) lists
    - Criminal watchlists

    Returns matches with confidence scores and risk levels.
    Critical for compliance and due diligence.
    """

    name: ClassVar[str] = "screen_sanctions"
    description: ClassVar[str] = (
        "Screen entity against sanctions, watchlists, and PEP databases. "
        "Checks OFAC, UN, EU, Interpol, and more. "
        "Returns matches with confidence scores. "
        "Essential for compliance and risk assessment."
    )
    domain: ClassVar[str] = "risk_screening"
    input_model: ClassVar[type[BaseModel]] = ScreenSanctionsInput
    output_model: ClassVar[type[BaseModel]] = ScreenSanctionsOutput

    async def execute(self, input_data: ScreenSanctionsInput) -> ScreenSanctionsOutput:
        """Execute sanctions screening."""
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.risk_screening.providers import get_risk_provider

        provider = get_risk_provider("opensanctions", self.settings)

        screening_result = await provider.screen_entity(
            entity_name=input_data.entity_name,
            entity_type=input_data.entity_type,
            countries=input_data.countries,
            fuzzy=input_data.fuzzy_matching,
        )

        output = ScreenSanctionsOutput(
            screening_result=screening_result,
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


@register_tool(domain="risk_screening")
class SearchAdverseMedia(BaseTool[SearchAdverseMediaInput, SearchAdverseMediaOutput]):
    """Search for adverse media mentions of an entity.

    Searches news sources for negative mentions including:
    - Fraud, scam, scheme keywords
    - Lawsuits, litigation, settlements
    - Investigations (DOJ, FTC, state AG)
    - Complaints, BBB alerts
    - "Hostage load", moving scams (for carriers)

    Returns articles with classification and risk scoring.
    Critical for detecting entities with recent issues.
    """

    name: ClassVar[str] = "search_adverse_media"
    description: ClassVar[str] = (
        "Search for adverse media (negative news) about an entity. "
        "Finds mentions of fraud, lawsuits, investigations, complaints. "
        "Includes moving scam keywords for carrier vetting. "
        "Returns articles with risk scoring."
    )
    domain: ClassVar[str] = "risk_screening"
    input_model: ClassVar[type[BaseModel]] = SearchAdverseMediaInput
    output_model: ClassVar[type[BaseModel]] = SearchAdverseMediaOutput

    async def execute(self, input_data: SearchAdverseMediaInput) -> SearchAdverseMediaOutput:
        """Execute adverse media search."""
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.risk_screening.providers import get_risk_provider

        provider = get_risk_provider("newsapi", self.settings)

        adverse_result = await provider.search_adverse_media(
            entity_name=input_data.entity_name,
            keywords=input_data.keywords,
            date_range=input_data.date_range,
            max_articles=input_data.max_articles,
        )

        output = SearchAdverseMediaOutput(
            adverse_media_result=adverse_result,
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


@register_tool(domain="risk_screening")
class MonitorEntityRisk(BaseTool[MonitorEntityRiskInput, MonitorEntityRiskOutput]):
    """Comprehensive entity risk monitoring combining multiple checks.

    Runs in parallel:
    - Sanctions/watchlist screening
    - Adverse media search
    - Pattern analysis
    - Risk scoring

    Returns unified risk assessment with actionable recommendations.
    Perfect for comprehensive carrier due diligence.
    """

    name: ClassVar[str] = "monitor_entity_risk"
    description: ClassVar[str] = (
        "Comprehensive entity risk monitoring. "
        "Runs sanctions screening and adverse media search in parallel. "
        "Returns unified risk score and recommendations. "
        "Ideal for complete carrier due diligence."
    )
    domain: ClassVar[str] = "risk_screening"
    input_model: ClassVar[type[BaseModel]] = MonitorEntityRiskInput
    output_model: ClassVar[type[BaseModel]] = MonitorEntityRiskOutput

    async def execute(self, input_data: MonitorEntityRiskInput) -> MonitorEntityRiskOutput:
        """Execute comprehensive risk monitoring."""
        import asyncio
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.risk_screening.providers import get_risk_provider

        # Run checks in parallel
        tasks = []
        sanctions_result = None
        adverse_result = None

        if input_data.check_sanctions:
            sanctions_provider = get_risk_provider("opensanctions", self.settings)
            tasks.append(
                sanctions_provider.screen_entity(
                    entity_name=input_data.entity_name,
                    entity_type=input_data.entity_type,
                )
            )

        if input_data.check_adverse_media:
            news_provider = get_risk_provider("newsapi", self.settings)
            tasks.append(
                news_provider.search_adverse_media(
                    entity_name=input_data.entity_name,
                    keywords=["fraud", "scam", "lawsuit", "hostage", "complaint"],
                )
            )

        # Execute in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            if input_data.check_sanctions and len(results) > 0:
                if not isinstance(results[0], Exception):
                    sanctions_result = results[0]

            if input_data.check_adverse_media:
                adverse_idx = 1 if input_data.check_sanctions else 0
                if len(results) > adverse_idx and not isinstance(results[adverse_idx], Exception):
                    adverse_result = results[adverse_idx]

        # Calculate overall risk
        overall_risk_score = 0.0
        risk_factors = []

        if sanctions_result:
            if sanctions_result.total_matches > 0:
                overall_risk_score += 50.0
                risk_factors.append(
                    f"Found on {sanctions_result.total_matches} watchlist(s)"
                )

        if adverse_result:
            overall_risk_score += adverse_result.adverse_media_score * 0.5
            if adverse_result.fraud_mentions > 0:
                risk_factors.append(f"{adverse_result.fraud_mentions} fraud mentions in news")
            if adverse_result.lawsuit_mentions > 0:
                risk_factors.append(f"{adverse_result.lawsuit_mentions} lawsuit mentions")

        # Determine risk level
        if overall_risk_score >= 75:
            risk_level = "critical"
        elif overall_risk_score >= 50:
            risk_level = "high"
        elif overall_risk_score >= 25:
            risk_level = "medium"
        elif overall_risk_score > 0:
            risk_level = "low"
        else:
            risk_level = "clear"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, sanctions_result, adverse_result
        )

        output = MonitorEntityRiskOutput(
            entity_name=input_data.entity_name,
            overall_risk_score=min(overall_risk_score, 100.0),
            risk_level=risk_level,
            sanctions_result=sanctions_result,
            adverse_media_result=adverse_result,
            risk_factors=risk_factors,
            recommendations=recommendations,
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

    def _generate_recommendations(
        self,
        risk_level: str,
        sanctions: SanctionsScreeningResult | None,
        adverse: AdverseMediaResult | None,
    ) -> list[str]:
        """Generate actionable recommendations based on findings."""
        recs = []

        if risk_level == "critical":
            recs.append("DO NOT PROCEED - Critical risk factors identified")

        if sanctions and sanctions.total_matches > 0:
            recs.append("Verify identity precisely - sanctions matches found")
            recs.append("Consult compliance team before proceeding")

        if adverse:
            if adverse.fraud_mentions > 3:
                recs.append("Multiple fraud allegations - conduct thorough investigation")
            if adverse.lawsuit_mentions > 2:
                recs.append("Active litigation found - review court records")
            if adverse.investigation_mentions > 0:
                recs.append("Government investigation mentioned - high risk")

        if risk_level == "clear":
            recs.append("No significant risk factors identified")

        return recs
