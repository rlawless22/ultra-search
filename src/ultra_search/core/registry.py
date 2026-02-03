"""Tool and provider registration system with auto-discovery."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ultra_search.core.base import BaseTool

# Global registries
_TOOL_REGISTRY: dict[str, dict[str, type[BaseTool]]] = {}
_PROVIDER_REGISTRY: dict[str, dict[str, type[Any]]] = {}
_discovered = False


def register_tool(domain: str):
    """Decorator to register a tool under a domain.

    Usage:
        @register_tool(domain="web_search")
        class SearchWeb(BaseTool[SearchInput, SearchOutput]):
            name = "search_web"
            description = "Search the web"
            ...

    Args:
        domain: The domain this tool belongs to (e.g., "web_search", "financial")

    Returns:
        Decorator function that registers the tool class
    """

    def decorator(cls: type[BaseTool]) -> type[BaseTool]:
        if domain not in _TOOL_REGISTRY:
            _TOOL_REGISTRY[domain] = {}

        tool_name = getattr(cls, "name", cls.__name__)
        _TOOL_REGISTRY[domain][tool_name] = cls
        return cls

    return decorator


def register_provider(domain: str):
    """Decorator to register a provider under a domain.

    Usage:
        @register_provider(domain="web_search")
        class SerpAPIProvider(BaseProvider):
            provider_name = "serpapi"
            ...

    Args:
        domain: The domain this provider belongs to

    Returns:
        Decorator function that registers the provider class
    """

    def decorator(cls: type[Any]) -> type[Any]:
        if domain not in _PROVIDER_REGISTRY:
            _PROVIDER_REGISTRY[domain] = {}

        provider_name = getattr(cls, "provider_name", cls.__name__)
        _PROVIDER_REGISTRY[domain][provider_name] = cls
        return cls

    return decorator


def get_tools(domains: list[str] | None = None) -> dict[str, type[BaseTool]]:
    """Get all registered tools, optionally filtered by domains.

    Args:
        domains: List of domain names to filter by. If None, returns all tools.

    Returns:
        Dictionary mapping tool names to tool classes
    """
    discover_domains()

    if domains is None:
        domains = list(_TOOL_REGISTRY.keys())

    tools: dict[str, type[BaseTool]] = {}
    for domain in domains:
        if domain in _TOOL_REGISTRY:
            tools.update(_TOOL_REGISTRY[domain])
    return tools


def get_providers(domain: str) -> dict[str, type[Any]]:
    """Get all registered providers for a domain.

    Args:
        domain: The domain to get providers for

    Returns:
        Dictionary mapping provider names to provider classes
    """
    discover_domains()
    return _PROVIDER_REGISTRY.get(domain, {})


def get_all_domains() -> list[str]:
    """Get list of all registered domains.

    Returns:
        List of domain names
    """
    discover_domains()
    return list(_TOOL_REGISTRY.keys())


def discover_domains() -> None:
    """Auto-discover and import all domain modules.

    This function finds all domain packages under ultra_search.domains
    and imports them, which triggers their @register_tool decorators.
    """
    global _discovered
    if _discovered:
        return

    try:
        import ultra_search.domains as domains_pkg

        domains_path = Path(domains_pkg.__file__).parent

        for _, module_name, is_pkg in pkgutil.iter_modules([str(domains_path)]):
            if is_pkg:
                # Import the domain module (triggers registration)
                try:
                    importlib.import_module(f"ultra_search.domains.{module_name}")
                except ImportError as e:
                    # Log but don't fail - allows partial domain loading
                    print(f"Warning: Could not load domain '{module_name}': {e}")

    except ImportError:
        # Domains package not yet created
        pass

    _discovered = True


def reset_registry() -> None:
    """Reset the registries. Useful for testing."""
    global _discovered
    _TOOL_REGISTRY.clear()
    _PROVIDER_REGISTRY.clear()
    _discovered = False
