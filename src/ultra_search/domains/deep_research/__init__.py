"""Deep Research domain - AI-powered comprehensive research.

Providers:
- openai: OpenAI with web search (Responses API)
- perplexity: Perplexity AI

Async Tools (for long-running research):
- start_deep_research_async: Start research in background
- check_research_status: Check task status
- list_research_tasks: List all tasks
- get_research_result: Get completed results
- cancel_research_task: Cancel running task
"""

from ultra_search.domains.deep_research.domain import (
    DeepResearchInput,
    DeepResearchOutput,
    DeepResearch,
)

# Import async tools to register them
from ultra_search.domains.deep_research import async_tools  # noqa: F401

__all__ = [
    "DeepResearchInput",
    "DeepResearchOutput",
    "DeepResearch",
]
