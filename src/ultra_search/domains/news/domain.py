"""News domain tools - STUB."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import SearchResult
from ultra_search.core.registry import register_tool


class NewsSearchInput(BaseModel):
    """Input for news search."""

    query: str = Field(..., description="News search query")
    num_results: int = Field(default=10, ge=1, le=100)
    language: str = Field(default="en", description="Language code")
    sort_by: str = Field(default="relevancy", description="Sort: relevancy, popularity, publishedAt")


class NewsSearchOutput(BaseModel):
    """Output from news search."""

    query: str
    results: list[SearchResult]
    total_results: int | None
    provider: str


# UNCOMMENT AND IMPLEMENT:
# @register_tool(domain="news")
class SearchNews(BaseTool[NewsSearchInput, NewsSearchOutput]):
    """Search for news articles.

    TODO: Implement with NewsAPI, GDELT, or similar.
    """

    name: ClassVar[str] = "search_news_articles"
    description: ClassVar[str] = (
        "Search for recent news articles on a topic. "
        "Returns headlines, sources, and publication dates."
    )
    domain: ClassVar[str] = "news"
    input_model: ClassVar[type[BaseModel]] = NewsSearchInput
    output_model: ClassVar[type[BaseModel]] = NewsSearchOutput

    async def execute(self, input_data: NewsSearchInput) -> NewsSearchOutput:
        raise NotImplementedError("News domain not yet implemented.")
