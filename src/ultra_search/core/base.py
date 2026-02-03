"""Abstract base classes for tools and providers."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

import httpx
from pydantic import BaseModel

# Type variables for generic tool typing
InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseTool(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all research tools.

    Each tool has:
    - A unique name (used for MCP registration)
    - A description (shown to Claude)
    - A domain (for grouping/filtering)
    - Input/output Pydantic models for validation
    """

    name: ClassVar[str]
    description: ClassVar[str]
    domain: ClassVar[str]
    input_model: ClassVar[type[BaseModel]]
    output_model: ClassVar[type[BaseModel]]

    def __init__(self, settings: Any) -> None:
        """Initialize tool with settings for API key access."""
        self.settings = settings

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the tool with validated input.

        Args:
            input_data: Validated input matching input_model

        Returns:
            Output data matching output_model
        """
        pass

    def get_schema(self) -> dict[str, Any]:
        """Get JSON schema for the tool's input model."""
        return self.input_model.model_json_schema()


class BaseProvider(ABC):
    """Abstract base class for API providers.

    Providers handle the actual API communication for a domain.
    Multiple providers can exist for the same domain (e.g., SerpAPI vs Tavily for web search).
    """

    provider_name: ClassVar[str]
    base_url: ClassVar[str]
    requires_auth: ClassVar[bool] = True

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize provider with API credentials.

        Args:
            api_key: API key for authentication
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers=self._get_default_headers(),
            )
        return self._client

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for requests. Override in subclasses."""
        return {"User-Agent": "UltraSearch/0.1.0"}

    @abstractmethod
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Parsed JSON response
        """
        pass

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
