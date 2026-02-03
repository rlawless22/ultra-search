"""Scraping domain tools - STUB."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import ScrapedContent
from ultra_search.core.registry import register_tool


class ScrapeUrlInput(BaseModel):
    """Input for URL scraping."""

    url: str = Field(..., description="URL to scrape")
    include_html: bool = Field(default=False, description="Include raw HTML")
    wait_for: str | None = Field(default=None, description="CSS selector to wait for")


class ScrapeUrlOutput(BaseModel):
    """Output from URL scraping."""

    url: str
    title: str
    content: str
    markdown: str
    links: list[str]
    provider: str


# UNCOMMENT AND IMPLEMENT:
# @register_tool(domain="scraping")
class ScrapeUrl(BaseTool[ScrapeUrlInput, ScrapeUrlOutput]):
    """Scrape content from a URL.

    TODO: Implement with Firecrawl, Browserless, or similar.
    """

    name: ClassVar[str] = "scrape_url"
    description: ClassVar[str] = (
        "Extract content from a web page URL. "
        "Returns text, markdown, and links."
    )
    domain: ClassVar[str] = "scraping"
    input_model: ClassVar[type[BaseModel]] = ScrapeUrlInput
    output_model: ClassVar[type[BaseModel]] = ScrapeUrlOutput

    async def execute(self, input_data: ScrapeUrlInput) -> ScrapeUrlOutput:
        raise NotImplementedError("Scraping domain not yet implemented.")
