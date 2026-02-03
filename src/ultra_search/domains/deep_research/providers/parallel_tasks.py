"""Parallel AI Tasks API provider for deep research.

Parallel Tasks API enables comprehensive research and analysis.
Docs: https://docs.parallel.ai/
"""

from __future__ import annotations

from typing import Any

import httpx

from ultra_search.core.models import ResearchResult, SearchResult, ResultType
from ultra_search.domains.deep_research.providers.base import BaseResearchProvider


class ParallelTasksProvider(BaseResearchProvider):
    """Parallel AI Tasks API provider.

    Uses Parallel's Tasks API for research with:
    - Comprehensive web research
    - Multi-step task execution
    - Evidence-based analysis
    - Source citations
    """

    provider_name = "parallel_tasks"
    base_url = "https://api.parallel.ai"
    requires_auth = True

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(api_key, **kwargs)
        self._client: httpx.AsyncClient | None = None
        self.timeout = kwargs.get("timeout", 120.0)  # Longer timeout for research

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Parallel AI requires an API key. Set ULTRA_PARALLEL_API_KEY."
                )
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    async def research(
        self,
        query: str,
        depth: str = "standard",
        include_sources: bool = True,
        **kwargs: Any,
    ) -> ResearchResult:
        """Perform research using Parallel Tasks API.

        Args:
            query: Research question or topic
            depth: Research depth (quick, standard, comprehensive)
            include_sources: Whether to include source citations
            **kwargs: Additional parameters

        Returns:
            ResearchResult with findings and sources
        """
        client = await self._get_client()

        # Map depth to task complexity
        complexity_map = {
            "quick": "simple",
            "standard": "moderate",
            "comprehensive": "complex",
        }
        complexity = complexity_map.get(depth, "moderate")

        # Create research task
        task_payload = {
            "query": query,
            "complexity": complexity,
            "include_sources": include_sources,
            "max_sources": 10 if depth == "quick" else 20 if depth == "standard" else 50,
        }
        task_payload.update(kwargs)

        response = await client.post("/v1/tasks", json=task_payload)
        response.raise_for_status()
        data = response.json()

        # Poll for task completion if needed
        task_id = data.get("task_id")
        if task_id:
            data = await self._poll_task(client, task_id)

        return self._parse_response(query, data, depth)

    async def _poll_task(self, client: httpx.AsyncClient, task_id: str) -> dict[str, Any]:
        """Poll task until completion.

        Args:
            client: HTTP client
            task_id: Task identifier

        Returns:
            Completed task data
        """
        import asyncio

        max_attempts = 60  # 5 minutes with 5-second intervals
        for attempt in range(max_attempts):
            response = await client.get(f"/v1/tasks/{task_id}")
            response.raise_for_status()
            data = response.json()

            status = data.get("status")
            if status == "completed":
                return data
            elif status == "failed":
                raise RuntimeError(f"Task failed: {data.get('error', 'Unknown error')}")

            await asyncio.sleep(5)  # Wait 5 seconds between checks

        raise TimeoutError(f"Task {task_id} did not complete within timeout")

    def _parse_response(
        self,
        query: str,
        data: dict[str, Any],
        depth: str,
    ) -> ResearchResult:
        """Parse Parallel Tasks API response."""
        # Extract main analysis
        result = data.get("result", {})
        answer = result.get("answer", "")
        summary = result.get("summary", "")

        # Extract sources
        sources: list[SearchResult] = []
        for source in result.get("sources", []):
            sources.append(
                SearchResult(
                    title=source.get("title", ""),
                    url=source.get("url", ""),
                    snippet=source.get("snippet", ""),
                    content=source.get("content"),
                    result_type=ResultType.WEB_PAGE,
                    source=self.provider_name,
                    relevance_score=source.get("relevance_score"),
                    metadata={
                        "citation_count": source.get("citation_count"),
                        "credibility_score": source.get("credibility_score"),
                    },
                )
            )

        # Extract follow-up questions
        follow_ups = result.get("related_queries", [])

        # Calculate confidence
        confidence = result.get("confidence_score")

        return ResearchResult(
            query=query,
            summary=summary or answer[:500],
            detailed_answer=answer,
            sources=sources,
            follow_up_questions=follow_ups,
            confidence_score=confidence,
            provider=self.provider_name,
            metadata={
                "task_id": data.get("task_id"),
                "complexity": data.get("complexity"),
                "total_sources_found": data.get("total_sources"),
                "processing_time": data.get("processing_time_ms"),
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
