"""Configuration management using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderConfig(BaseModel):
    """Configuration for a specific provider within a domain."""

    enabled: bool = True
    api_key: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DomainConfig(BaseModel):
    """Configuration for a research domain."""

    enabled: bool = True
    default_provider: str | None = None
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


class Settings(BaseSettings):
    """Main application settings.

    Settings can be loaded from:
    1. Environment variables (ULTRA_ prefix)
    2. .env file
    3. config/settings.yaml

    Environment variable examples:
        ULTRA_OPENAI_API_KEY=sk-...
        ULTRA_DOMAINS__WEB_SEARCH__ENABLED=true
        ULTRA_DOMAINS__WEB_SEARCH__PROVIDERS__SERPAPI__API_KEY=...
    """

    model_config = SettingsConfigDict(
        env_prefix="ULTRA_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Global API Keys (fallbacks) ===
    openai_api_key: str | None = None
    serpapi_api_key: str | None = None
    tavily_api_key: str | None = None
    brave_api_key: str | None = None
    perplexity_api_key: str | None = None

    # === Domain Configurations ===
    domains: dict[str, DomainConfig] = Field(default_factory=lambda: {
        "web_search": DomainConfig(enabled=True, default_provider="mock"),
        "deep_research": DomainConfig(enabled=True, default_provider="openai"),
        "financial": DomainConfig(enabled=False),
        "legal": DomainConfig(enabled=False),
        "academic": DomainConfig(enabled=False),
        "social_media": DomainConfig(enabled=False),
        "business_intel": DomainConfig(enabled=False),
        "people_search": DomainConfig(enabled=False),
        "news": DomainConfig(enabled=False),
        "scraping": DomainConfig(enabled=False),
    })

    # === Execution Settings ===
    max_concurrent_requests: int = 10
    default_timeout: float = 30.0
    retry_attempts: int = 3

    def get_api_key(self, provider: str, domain: str | None = None) -> str | None:
        """Get API key for a provider, checking domain-specific config first.

        Args:
            provider: Provider name (e.g., "serpapi", "openai")
            domain: Optional domain to check for domain-specific key

        Returns:
            API key string or None if not configured
        """
        # Check domain-specific provider config first
        if domain and domain in self.domains:
            domain_cfg = self.domains[domain]
            if provider in domain_cfg.providers:
                provider_cfg = domain_cfg.providers[provider]
                if provider_cfg.api_key:
                    return provider_cfg.api_key

        # Fall back to global keys
        key_attr = f"{provider}_api_key"
        return getattr(self, key_attr, None)

    def is_domain_enabled(self, domain: str) -> bool:
        """Check if a domain is enabled.

        Args:
            domain: Domain name to check

        Returns:
            True if domain is enabled
        """
        if domain not in self.domains:
            return False
        return self.domains[domain].enabled

    def get_enabled_domains(self) -> list[str]:
        """Get list of all enabled domains.

        Returns:
            List of enabled domain names
        """
        return [name for name, cfg in self.domains.items() if cfg.enabled]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Singleton Settings instance
    """
    return Settings()


def reload_settings() -> Settings:
    """Force reload settings (clears cache).

    Returns:
        Fresh Settings instance
    """
    get_settings.cache_clear()
    return get_settings()
