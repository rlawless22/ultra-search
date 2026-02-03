"""Shared data models for research results."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ResultType(str, Enum):
    """Type of search/research result."""

    WEB_PAGE = "web_page"
    NEWS_ARTICLE = "news_article"
    ACADEMIC_PAPER = "academic_paper"
    SOCIAL_POST = "social_post"
    FINANCIAL_DATA = "financial_data"
    LEGAL_DOCUMENT = "legal_document"
    BUSINESS_RECORD = "business_record"
    PERSON_PROFILE = "person_profile"
    DEEP_RESEARCH = "deep_research"
    RAW_CONTENT = "raw_content"


class SearchResult(BaseModel):
    """Standard model for a single search result."""

    title: str
    url: HttpUrl | str
    snippet: str = ""
    content: str | None = None
    result_type: ResultType = ResultType.WEB_PAGE
    source: str = ""  # Provider that returned this result
    published_date: datetime | None = None
    relevance_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class SearchResponse(BaseModel):
    """Response from a search operation."""

    query: str
    results: list[SearchResult] = Field(default_factory=list)
    total_results: int | None = None
    provider: str = ""
    domain: str = ""
    execution_time_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchResult(BaseModel):
    """Result from a deep research operation."""

    query: str
    summary: str
    detailed_answer: str = ""
    sources: list[SearchResult] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    confidence_score: float | None = None
    provider: str = ""
    model_used: str | None = None
    tokens_used: int | None = None
    execution_time_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinancialQuote(BaseModel):
    """Financial quote data."""

    symbol: str
    price: float
    change: float = 0.0
    change_percent: float = 0.0
    volume: int | None = None
    market_cap: float | None = None
    timestamp: datetime | None = None
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class PersonProfile(BaseModel):
    """Person profile from people search."""

    name: str
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    social_profiles: dict[str, str] = Field(default_factory=dict)
    employment: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    confidence_score: float | None = None
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyProfile(BaseModel):
    """Company/business profile."""

    name: str
    domain: str | None = None
    description: str = ""
    industry: str | None = None
    founded_year: int | None = None
    employee_count: str | None = None
    revenue: str | None = None
    headquarters: str | None = None
    social_profiles: dict[str, str] = Field(default_factory=dict)
    funding: list[dict[str, Any]] = Field(default_factory=list)
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScrapedContent(BaseModel):
    """Content from web scraping."""

    url: HttpUrl | str
    title: str = ""
    content: str = ""
    markdown: str = ""
    html: str | None = None
    links: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
