"""Web Search domain tools and models."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import SearchResponse, SearchResult, ResultType
from ultra_search.core.registry import register_tool


class SearchWebInput(BaseModel):
    """Input for web search."""

    query: str = Field(..., description="Search query")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    search_type: str = Field(default="web", description="Type of search: web, news, images")
    output_file: str | None = Field(
        default=None,
        description="Optional file path to save results. Supports .json, .md, .txt, .html"
    )
    output_format: str | None = Field(
        default=None,
        description="Output format override (json, md, txt, html). Auto-detected from file extension if not specified."
    )


class SearchWebOutput(BaseModel):
    """Output from web search."""

    query: str
    results: list[SearchResult]
    total_results: int | None = None
    provider: str
    search_type: str
    output_file_path: str | None = None


@register_tool(domain="web_search")
class SearchWeb(BaseTool[SearchWebInput, SearchWebOutput]):
    """Search the web using configured provider.

    This tool searches the web and returns relevant results.
    The actual search is performed by the configured provider
    (SerpAPI, Tavily, Brave, etc.).
    """

    name: ClassVar[str] = "search_web"
    description: ClassVar[str] = (
        "Search the web for information. Returns titles, URLs, and snippets. "
        "Use for finding current information, websites, articles, and general research."
    )
    domain: ClassVar[str] = "web_search"
    input_model: ClassVar[type[BaseModel]] = SearchWebInput
    output_model: ClassVar[type[BaseModel]] = SearchWebOutput

    async def execute(self, input_data: SearchWebInput) -> SearchWebOutput:
        """Execute web search.

        Args:
            input_data: Validated search input

        Returns:
            Search results from the configured provider
        """
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )

        # Get provider based on settings
        provider = await self._get_provider()
        results = await provider.search(
            query=input_data.query,
            num_results=input_data.num_results,
            search_type=input_data.search_type,
        )

        output = SearchWebOutput(
            query=input_data.query,
            results=results,
            total_results=len(results),
            provider=provider.provider_name,
            search_type=input_data.search_type,
            output_file_path=None,
        )

        # Write to file if requested
        if input_data.output_file:
            # Detect format from extension or use override
            if input_data.output_format:
                format_str = input_data.output_format.lower()
            else:
                ext = Path(input_data.output_file).suffix.lstrip(".")
                format_str = ext if ext in ["json", "md", "txt", "html"] else "json"

            try:
                output_format = OutputFormat(format_str)
            except ValueError:
                output_format = OutputFormat.JSON

            config = FileOutputConfig(
                path=input_data.output_file,
                format=output_format,
                append=False,
                add_timestamp=True,
                create_dirs=True,
            )

            written_path = await write_result_to_file(output, config)
            output.output_file_path = str(written_path)

        return output

    async def _get_provider(self) -> Any:
        """Get the appropriate search provider based on settings."""
        from ultra_search.domains.web_search.providers import get_search_provider

        domain_cfg = self.settings.domains.get("web_search")
        provider_name = domain_cfg.default_provider if domain_cfg else "mock"

        return get_search_provider(provider_name, self.settings)


class SearchNewsInput(BaseModel):
    """Input for news search."""

    query: str = Field(..., description="News search query")
    num_results: int = Field(default=10, ge=1, le=50, description="Number of results")
    freshness: str = Field(default="week", description="Time range: day, week, month")


class SearchNewsOutput(BaseModel):
    """Output from news search."""

    query: str
    results: list[SearchResult]
    provider: str


@register_tool(domain="web_search")
class SearchNews(BaseTool[SearchNewsInput, SearchNewsOutput]):
    """Search for recent news articles."""

    name: ClassVar[str] = "search_news"
    description: ClassVar[str] = (
        "Search for recent news articles on a topic. "
        "Returns headlines, sources, and publication dates."
    )
    domain: ClassVar[str] = "web_search"
    input_model: ClassVar[type[BaseModel]] = SearchNewsInput
    output_model: ClassVar[type[BaseModel]] = SearchNewsOutput

    async def execute(self, input_data: SearchNewsInput) -> SearchNewsOutput:
        """Execute news search."""
        from ultra_search.domains.web_search.providers import get_search_provider

        domain_cfg = self.settings.domains.get("web_search")
        provider_name = domain_cfg.default_provider if domain_cfg else "mock"
        provider = get_search_provider(provider_name, self.settings)

        results = await provider.search(
            query=input_data.query,
            num_results=input_data.num_results,
            search_type="news",
        )

        # Mark results as news articles
        for result in results:
            result.result_type = ResultType.NEWS_ARTICLE

        return SearchNewsOutput(
            query=input_data.query,
            results=results,
            provider=provider.provider_name,
        )
