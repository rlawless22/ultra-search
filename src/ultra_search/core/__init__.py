"""Core framework for Ultra Search."""

from ultra_search.core.base import BaseTool, BaseProvider
from ultra_search.core.registry import register_tool, get_tools, get_all_domains
from ultra_search.core.config import Settings, get_settings
from ultra_search.core.models import SearchResult, ResearchResult

__all__ = [
    "BaseTool",
    "BaseProvider",
    "register_tool",
    "get_tools",
    "get_all_domains",
    "Settings",
    "get_settings",
    "SearchResult",
    "ResearchResult",
]
