"""Deep Research domain tools and models."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import ResearchResult, SearchResult
from ultra_search.core.registry import register_tool


class DeepResearchInput(BaseModel):
    """Input for deep research."""

    query: str = Field(..., description="Research question or topic")
    depth: str = Field(
        default="standard",
        description="Research depth: quick, standard, or comprehensive"
    )
    include_sources: bool = Field(
        default=True,
        description="Include source citations in results"
    )


class DeepResearchOutput(BaseModel):
    """Output from deep research."""

    query: str
    summary: str
    detailed_answer: str
    sources: list[SearchResult]
    follow_up_questions: list[str]
    provider: str
    model_used: str | None = None


@register_tool(domain="deep_research")
class DeepResearch(BaseTool[DeepResearchInput, DeepResearchOutput]):
    """Perform comprehensive AI-powered research on a topic.

    This tool uses AI models with web search capabilities to provide
    detailed, sourced answers to research questions.
    """

    name: ClassVar[str] = "deep_research"
    description: ClassVar[str] = (
        "Perform comprehensive AI-powered research on any topic. "
        "Returns a detailed answer with sources and follow-up questions. "
        "Best for complex questions requiring synthesis of multiple sources."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = DeepResearchInput
    output_model: ClassVar[type[BaseModel]] = DeepResearchOutput

    async def execute(self, input_data: DeepResearchInput) -> DeepResearchOutput:
        """Execute deep research.

        Args:
            input_data: Research query and parameters

        Returns:
            Comprehensive research results
        """
        provider = await self._get_provider()
        result = await provider.research(
            query=input_data.query,
            depth=input_data.depth,
            include_sources=input_data.include_sources,
        )

        return DeepResearchOutput(
            query=input_data.query,
            summary=result.summary,
            detailed_answer=result.detailed_answer,
            sources=result.sources,
            follow_up_questions=result.follow_up_questions,
            provider=provider.provider_name,
            model_used=result.model_used,
        )

    async def _get_provider(self) -> Any:
        """Get the appropriate research provider."""
        from ultra_search.domains.deep_research.providers import get_research_provider

        domain_cfg = self.settings.domains.get("deep_research")
        provider_name = domain_cfg.default_provider if domain_cfg else "openai"

        return get_research_provider(provider_name, self.settings)


class QuickAnswerInput(BaseModel):
    """Input for quick answer."""

    question: str = Field(..., description="Question to answer")


class QuickAnswerOutput(BaseModel):
    """Output from quick answer."""

    question: str
    answer: str
    confidence: float | None = None
    provider: str


@register_tool(domain="deep_research")
class QuickAnswer(BaseTool[QuickAnswerInput, QuickAnswerOutput]):
    """Get a quick, concise answer to a question.

    Faster than deep_research but less comprehensive.
    Good for factual questions with clear answers.
    """

    name: ClassVar[str] = "quick_answer"
    description: ClassVar[str] = (
        "Get a quick, concise answer to a factual question. "
        "Faster than deep_research but less detailed. "
        "Best for simple questions with direct answers."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = QuickAnswerInput
    output_model: ClassVar[type[BaseModel]] = QuickAnswerOutput

    async def execute(self, input_data: QuickAnswerInput) -> QuickAnswerOutput:
        """Get quick answer."""
        from ultra_search.domains.deep_research.providers import get_research_provider

        domain_cfg = self.settings.domains.get("deep_research")
        provider_name = domain_cfg.default_provider if domain_cfg else "openai"
        provider = get_research_provider(provider_name, self.settings)

        result = await provider.research(
            query=input_data.question,
            depth="quick",
            include_sources=False,
        )

        return QuickAnswerOutput(
            question=input_data.question,
            answer=result.summary,
            confidence=result.confidence_score,
            provider=provider.provider_name,
        )
