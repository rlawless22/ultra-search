"""Deep Research domain - AI-powered comprehensive research.

Providers:
- openai: OpenAI with web search (Responses API)
- perplexity: Perplexity AI
"""

from ultra_search.domains.deep_research.domain import (
    DeepResearchInput,
    DeepResearchOutput,
    DeepResearch,
)

__all__ = [
    "DeepResearchInput",
    "DeepResearchOutput",
    "DeepResearch",
]
