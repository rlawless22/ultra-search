"""OpenAI research provider using the Responses API with web search.

This uses OpenAI's models with web search tool enabled for research.
Docs: https://platform.openai.com/docs/api-reference/responses
"""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from ultra_search.core.models import ResearchResult, SearchResult, ResultType
from ultra_search.domains.deep_research.providers.base import BaseResearchProvider


class OpenAIResearchProvider(BaseResearchProvider):
    """OpenAI research provider.

    Uses OpenAI's Responses API with web search capability
    for AI-powered research with real-time information.
    """

    provider_name = "openai"
    requires_auth = True

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(api_key, **kwargs)
        self.client: AsyncOpenAI | None = None
        self.model = kwargs.get("model", "gpt-4o")

    async def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self.client is None:
            if not self.api_key:
                raise ValueError("OpenAI requires an API key. Set ULTRA_OPENAI_API_KEY.")
            self.client = AsyncOpenAI(api_key=self.api_key)
        return self.client

    async def research(
        self,
        query: str,
        depth: str = "standard",
        include_sources: bool = True,
        **kwargs: Any,
    ) -> ResearchResult:
        """Perform research using OpenAI with web search.

        Args:
            query: Research question
            depth: Research depth (affects model and detail)
            include_sources: Whether to extract sources

        Returns:
            ResearchResult with findings
        """
        client = await self._get_client()

        # Adjust prompt based on depth
        system_prompts = {
            "quick": "Provide a brief, direct answer to the question.",
            "standard": (
                "Research the topic thoroughly and provide a comprehensive answer. "
                "Include relevant facts, context, and cite your sources."
            ),
            "comprehensive": (
                "Conduct in-depth research on this topic. Provide a detailed analysis "
                "covering multiple perspectives, recent developments, and expert opinions. "
                "Cite all sources and suggest follow-up questions for further research."
            ),
        }

        system_prompt = system_prompts.get(depth, system_prompts["standard"])

        # Use the Responses API with web search tool
        response = await client.responses.create(
            model=self.model,
            input=query,
            instructions=system_prompt,
            tools=[{"type": "web_search_preview"}] if include_sources else [],
        )

        # Extract the response text
        output_text = ""
        sources: list[SearchResult] = []

        # Parse response output
        if hasattr(response, "output"):
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            output_text += content.text

        # Extract sources from annotations if available
        if include_sources and hasattr(response, "output"):
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "annotations"):
                            for annotation in content.annotations:
                                if hasattr(annotation, "url"):
                                    sources.append(
                                        SearchResult(
                                            title=getattr(annotation, "title", "Source"),
                                            url=annotation.url,
                                            snippet="",
                                            result_type=ResultType.WEB_PAGE,
                                            source=self.provider_name,
                                        )
                                    )

        # Generate follow-up questions for comprehensive research
        follow_ups = []
        if depth == "comprehensive":
            follow_ups = self._generate_follow_ups(query)

        # Create summary (first paragraph or first 500 chars)
        summary = output_text.split("\n\n")[0][:500] if output_text else ""

        return ResearchResult(
            query=query,
            summary=summary,
            detailed_answer=output_text,
            sources=sources,
            follow_up_questions=follow_ups,
            provider=self.provider_name,
            model_used=self.model,
            tokens_used=getattr(response, "usage", {}).get("total_tokens"),
        )

    def _generate_follow_ups(self, query: str) -> list[str]:
        """Generate follow-up question suggestions."""
        # Simple heuristic follow-ups - could be enhanced with AI
        return [
            f"What are the latest developments in {query}?",
            f"What are the opposing viewpoints on {query}?",
            f"How does {query} compare to alternatives?",
        ]

    async def close(self) -> None:
        """Close the OpenAI client."""
        if self.client is not None:
            await self.client.close()
            self.client = None
