"""Async execution engine for parallel tool execution."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pydantic import BaseModel

from ultra_search.core.base import BaseTool
from ultra_search.core.config import Settings, get_settings
from ultra_search.core.registry import get_tools

T = TypeVar("T", bound=BaseModel)


@dataclass
class ExecutionResult:
    """Result of a tool execution."""

    tool_name: str
    success: bool
    result: Any | None = None
    error: str | None = None
    execution_time_ms: float = 0.0


@dataclass
class BatchResult:
    """Result of executing multiple tools."""

    results: list[ExecutionResult] = field(default_factory=list)
    total_time_ms: float = 0.0

    @property
    def successful(self) -> list[ExecutionResult]:
        """Get successful results."""
        return [r for r in self.results if r.success]

    @property
    def failed(self) -> list[ExecutionResult]:
        """Get failed results."""
        return [r for r in self.results if not r.success]


class Executor:
    """Async execution engine for tools.

    Handles:
    - Single tool execution
    - Parallel batch execution
    - Error handling and retries
    - Result aggregation
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize executor.

        Args:
            settings: Settings instance. Uses default if not provided.
        """
        self.settings = settings or get_settings()
        self._tools: dict[str, type[BaseTool]] | None = None

    @property
    def tools(self) -> dict[str, type[BaseTool]]:
        """Get available tools (lazy loaded)."""
        if self._tools is None:
            enabled_domains = self.settings.get_enabled_domains()
            self._tools = get_tools(enabled_domains)
        return self._tools

    async def execute(
        self,
        tool_name: str,
        input_data: dict[str, Any],
    ) -> ExecutionResult:
        """Execute a single tool.

        Args:
            tool_name: Name of the tool to execute
            input_data: Input data as dictionary

        Returns:
            ExecutionResult with success/failure status
        """
        start_time = time.perf_counter()

        if tool_name not in self.tools:
            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found or not enabled",
            )

        try:
            tool_cls = self.tools[tool_name]
            tool = tool_cls(self.settings)

            # Validate input
            validated_input = tool.input_model(**input_data)

            # Execute
            result = await tool.execute(validated_input)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=elapsed_ms,
            )

    async def execute_batch(
        self,
        requests: list[tuple[str, dict[str, Any]]],
        max_concurrent: int | None = None,
    ) -> BatchResult:
        """Execute multiple tools in parallel.

        Args:
            requests: List of (tool_name, input_data) tuples
            max_concurrent: Max concurrent executions. Uses settings default if None.

        Returns:
            BatchResult with all execution results
        """
        start_time = time.perf_counter()
        max_concurrent = max_concurrent or self.settings.max_concurrent_requests

        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_execute(tool_name: str, input_data: dict) -> ExecutionResult:
            async with semaphore:
                return await self.execute(tool_name, input_data)

        tasks = [
            limited_execute(tool_name, input_data)
            for tool_name, input_data in requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=False)

        total_time_ms = (time.perf_counter() - start_time) * 1000
        return BatchResult(results=list(results), total_time_ms=total_time_ms)

    async def search_parallel(
        self,
        query: str,
        tools: list[str] | None = None,
    ) -> BatchResult:
        """Execute search across multiple tools in parallel.

        Convenience method for running the same query across multiple search tools.

        Args:
            query: Search query
            tools: List of tool names to use. Uses all search tools if None.

        Returns:
            BatchResult with all search results
        """
        if tools is None:
            # Use all available search-type tools
            tools = [
                name for name in self.tools
                if "search" in name.lower()
            ]

        requests = [(tool, {"query": query}) for tool in tools]
        return await self.execute_batch(requests)


# Module-level executor instance
_executor: Executor | None = None


def get_executor() -> Executor:
    """Get the global executor instance."""
    global _executor
    if _executor is None:
        _executor = Executor()
    return _executor


async def execute_tool(tool_name: str, input_data: dict[str, Any]) -> ExecutionResult:
    """Convenience function to execute a single tool.

    Args:
        tool_name: Name of the tool
        input_data: Input data dictionary

    Returns:
        ExecutionResult
    """
    return await get_executor().execute(tool_name, input_data)
