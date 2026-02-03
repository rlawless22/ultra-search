"""Academic domain tools - STUB.

Free APIs available:
- Semantic Scholar: https://api.semanticscholar.org/
- arXiv: https://arxiv.org/help/api
- OpenAlex: https://docs.openalex.org/
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import SearchResult
from ultra_search.core.registry import register_tool


class PaperSearchInput(BaseModel):
    """Input for academic paper search."""

    query: str = Field(..., description="Search query for papers")
    num_results: int = Field(default=10, ge=1, le=100)
    year_from: int | None = Field(default=None, description="Filter papers from this year")
    year_to: int | None = Field(default=None, description="Filter papers until this year")


class PaperSearchOutput(BaseModel):
    """Output from academic paper search."""

    query: str
    results: list[SearchResult]
    total_results: int | None
    provider: str


# UNCOMMENT AND IMPLEMENT:
# @register_tool(domain="academic")
class SearchPapers(BaseTool[PaperSearchInput, PaperSearchOutput]):
    """Search for academic papers and research.

    TODO: Implement with Semantic Scholar, arXiv, or similar.
    """

    name: ClassVar[str] = "search_papers"
    description: ClassVar[str] = (
        "Search for academic papers and research articles. "
        "Returns titles, authors, abstracts, and citation counts."
    )
    domain: ClassVar[str] = "academic"
    input_model: ClassVar[type[BaseModel]] = PaperSearchInput
    output_model: ClassVar[type[BaseModel]] = PaperSearchOutput

    async def execute(self, input_data: PaperSearchInput) -> PaperSearchOutput:
        raise NotImplementedError(
            "Academic domain not yet implemented. "
            "Free APIs: Semantic Scholar, arXiv, OpenAlex"
        )
