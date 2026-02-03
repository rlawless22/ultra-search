"""Web Search domain - General web search capabilities.

Providers:
- serpapi: SerpAPI Google Search
- tavily: Tavily AI-powered search
- brave: Brave Search API
- mock: Mock provider for testing
"""

from ultra_search.domains.web_search.domain import (
    SearchWebInput,
    SearchWebOutput,
    SearchWeb,
)

__all__ = [
    "SearchWebInput",
    "SearchWebOutput",
    "SearchWeb",
]
