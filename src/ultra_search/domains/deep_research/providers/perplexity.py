"""Perplexity AI research provider.

Perplexity provides AI-powered research with real-time web access.
Docs: https://docs.perplexity.ai/
"""

from __future__ import annotations

from typing import Any

import httpx

from ultra_search.core.models import ResearchResult, SearchResult, ResultType
from ultra_search.domains.deep_research.providers.base import BaseResearchProvider


class PerplexityProvider(BaseResearchProvider):
    """Perplexity AI research provider.

    Uses Perplexity's API for research with:
    - Real-time web search
    - Source citations
    - Follow-up suggestions
    """

    provider_name = "perplexity"
    base_url = "https://api.perplexity.ai"
    requires_auth = True

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(api_key, **kwargs)
        self._client: httpx.AsyncClient | None = None
        self.model = kwargs.get("model", "llama-3.1-sonar-large-128k-online")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Perplexity requires an API key. Set ULTRA_PERPLEXITY_API_KEY."
                )
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def research(
        self,
        query: str,
        depth: str = "standard",
        include_sources: bool = True,
        **kwargs: Any,
    ) -> ResearchResult:
        """Perform research using Perplexity API.

        Args:
            query: Research question
            depth: Research depth
            include_sources: Whether to include citations

        Returns:
            ResearchResult with findings
        """
        client = await self._get_client()

        # Adjust system prompt based on depth
        system_prompts = {
            "quick": "Be concise and direct.",
            "standard": "Provide a thorough answer with citations.",
            "comprehensive": (
                "Provide an in-depth, comprehensive analysis. "
                "Cover multiple perspectives and cite all sources."
            ),
        }

        system_content = system_prompts.get(depth, system_prompts["standard"])

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": query},
            ],
            "return_citations": include_sources,
            "return_related_questions": depth == "comprehensive",
        }

        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        return self._parse_response(query, data, depth)

    def _parse_response(
        self,
        query: str,
        data: dict[str, Any],
        depth: str,
    ) -> ResearchResult:
        """Parse Perplexity API response."""
        # Extract main content
        choices = data.get("choices", [])
        content = ""
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")

        # Extract citations/sources
        sources: list[SearchResult] = []
        citations = data.get("citations", [])
        for citation in citations:
            sources.append(
                SearchResult(
                    title=citation.get("title", "Source"),
                    url=citation.get("url", ""),
                    snippet=citation.get("snippet", ""),
                    result_type=ResultType.WEB_PAGE,
                    source=self.provider_name,
                )
            )

        # Extract related questions
        follow_ups = data.get("related_questions", [])

        # Create summary
        summary = content.split("\n\n")[0][:500] if content else ""

        return ResearchResult(
            query=query,
            summary=summary,
            detailed_answer=content,
            sources=sources,
            follow_up_questions=follow_ups,
            provider=self.provider_name,
            model_used=self.model,
            tokens_used=data.get("usage", {}).get("total_tokens"),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
