"""Async (background) versions of deep research tools.

These tools start long-running research tasks in the background and return immediately,
allowing Claude Code to continue working while research completes.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.models import SearchResult
from ultra_search.core.registry import register_tool
from ultra_search.core.task_queue import TaskStatus, get_queue, start_background_task


# === INPUT/OUTPUT MODELS ===


class StartDeepResearchInput(BaseModel):
    """Input for starting async deep research."""

    query: str = Field(..., description="Research question or topic")
    depth: str = Field(
        default="comprehensive",
        description="Research depth: quick, standard, or comprehensive"
    )
    include_sources: bool = Field(
        default=True,
        description="Include source citations in results"
    )
    output_file: str | None = Field(
        default=None,
        description="Optional file path to save results. Supports .json, .md, .txt, .html"
    )
    output_format: str | None = Field(
        default=None,
        description="Output format override (json, md, txt, html)"
    )


class StartDeepResearchOutput(BaseModel):
    """Output from starting async deep research."""

    task_id: str
    query: str
    status: str
    estimated_duration_minutes: int
    message: str


class CheckResearchStatusInput(BaseModel):
    """Input for checking research status."""

    task_id: str = Field(..., description="Task identifier from start_deep_research_async")


class CheckResearchStatusOutput(BaseModel):
    """Output from checking research status."""

    task_id: str
    query: str
    status: str
    progress: int  # 0-100
    started_at: str | None = None
    completed_at: str | None = None
    estimated_duration_minutes: int | None = None
    output_file: str | None = None
    error: str | None = None
    result_summary: str | None = None
    provider: str | None = None


class ListResearchTasksInput(BaseModel):
    """Input for listing research tasks."""

    status_filter: str | None = Field(
        default=None,
        description="Filter by status: pending, running, completed, failed, cancelled"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of tasks")


class TaskSummary(BaseModel):
    """Summary of a research task."""

    task_id: str
    query: str
    status: str
    progress: int
    created_at: str
    output_file: str | None = None


class ListResearchTasksOutput(BaseModel):
    """Output from listing research tasks."""

    tasks: list[TaskSummary]
    total_count: int


class GetResearchResultInput(BaseModel):
    """Input for getting completed research result."""

    task_id: str = Field(..., description="Task identifier")


class GetResearchResultOutput(BaseModel):
    """Output from getting research result."""

    task_id: str
    query: str
    summary: str
    detailed_answer: str
    sources: list[SearchResult]
    follow_up_questions: list[str]
    provider: str
    output_file_path: str | None = None


class CancelResearchTaskInput(BaseModel):
    """Input for cancelling a research task."""

    task_id: str = Field(..., description="Task identifier to cancel")


class CancelResearchTaskOutput(BaseModel):
    """Output from cancelling a research task."""

    task_id: str
    success: bool
    message: str


# === TOOLS ===


@register_tool(domain="deep_research")
class StartDeepResearchAsync(BaseTool[StartDeepResearchInput, StartDeepResearchOutput]):
    """Start comprehensive AI-powered research in the background.

    This tool starts a long-running research task and returns immediately.
    The research continues in the background, allowing you to work on other tasks.

    Use this for research that may take 5-60 minutes.
    Check status with check_research_status or list_research_tasks.
    """

    name: ClassVar[str] = "start_deep_research_async"
    description: ClassVar[str] = (
        "Start comprehensive AI-powered research in the background. "
        "Returns immediately with a task_id. Use this for research that takes 5+ minutes. "
        "Check status later with check_research_status."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = StartDeepResearchInput
    output_model: ClassVar[type[BaseModel]] = StartDeepResearchOutput

    async def execute(self, input_data: StartDeepResearchInput) -> StartDeepResearchOutput:
        """Start async deep research."""
        queue = get_queue()

        # Estimate duration based on depth
        duration_map = {
            "quick": 2,
            "standard": 10,
            "comprehensive": 30,
        }
        estimated_minutes = duration_map.get(input_data.depth, 10)

        # Create task in queue
        task_id = queue.create_task(
            tool_name="deep_research",
            query=input_data.query,
            input_data=input_data.model_dump(),
            output_file=input_data.output_file,
            estimated_duration=estimated_minutes * 60,
        )

        # Start background execution
        start_background_task(task_id)

        return StartDeepResearchOutput(
            task_id=task_id,
            query=input_data.query,
            status="started",
            estimated_duration_minutes=estimated_minutes,
            message=(
                f"Research task started (ID: {task_id}). "
                f"Estimated completion: ~{estimated_minutes} minutes. "
                f"Check status with check_research_status(task_id='{task_id}')"
            ),
        )


@register_tool(domain="deep_research")
class CheckResearchStatus(BaseTool[CheckResearchStatusInput, CheckResearchStatusOutput]):
    """Check the status of a background research task.

    Returns current status, progress, and results if completed.
    """

    name: ClassVar[str] = "check_research_status"
    description: ClassVar[str] = (
        "Check the status of a background research task started with start_deep_research_async. "
        "Returns progress, status, and results if completed."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = CheckResearchStatusInput
    output_model: ClassVar[type[BaseModel]] = CheckResearchStatusOutput

    async def execute(
        self, input_data: CheckResearchStatusInput
    ) -> CheckResearchStatusOutput:
        """Check research status."""
        queue = get_queue()
        task = queue.get_task(input_data.task_id)

        if not task:
            raise ValueError(f"Task {input_data.task_id} not found")

        # Extract summary from result if completed
        result_summary = None
        if task.status == TaskStatus.COMPLETED and task.result_json:
            import json

            result_data = json.loads(task.result_json)
            result_summary = result_data.get("summary", "")[:200]

        return CheckResearchStatusOutput(
            task_id=task.task_id,
            query=task.query,
            status=task.status.value,
            progress=task.progress,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            estimated_duration_minutes=task.estimated_duration_seconds // 60
            if task.estimated_duration_seconds
            else None,
            output_file=task.output_file,
            error=task.error,
            result_summary=result_summary,
            provider=task.provider,
        )


@register_tool(domain="deep_research")
class ListResearchTasks(BaseTool[ListResearchTasksInput, ListResearchTasksOutput]):
    """List all research tasks, optionally filtered by status.

    Shows all background research tasks with their current status.
    """

    name: ClassVar[str] = "list_research_tasks"
    description: ClassVar[str] = (
        "List all background research tasks. "
        "Optionally filter by status (pending, running, completed, failed). "
        "Shows task IDs, queries, and current progress."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = ListResearchTasksInput
    output_model: ClassVar[type[BaseModel]] = ListResearchTasksOutput

    async def execute(self, input_data: ListResearchTasksInput) -> ListResearchTasksOutput:
        """List research tasks."""
        queue = get_queue()

        status_filter = None
        if input_data.status_filter:
            try:
                status_filter = TaskStatus(input_data.status_filter.lower())
            except ValueError:
                pass

        tasks = queue.list_tasks(status=status_filter, limit=input_data.limit)

        task_summaries = [
            TaskSummary(
                task_id=task.task_id,
                query=task.query,
                status=task.status.value,
                progress=task.progress,
                created_at=task.created_at.isoformat(),
                output_file=task.output_file,
            )
            for task in tasks
        ]

        return ListResearchTasksOutput(
            tasks=task_summaries,
            total_count=len(task_summaries),
        )


@register_tool(domain="deep_research")
class GetResearchResult(BaseTool[GetResearchResultInput, GetResearchResultOutput]):
    """Get the full result of a completed research task.

    Retrieves detailed results including summary, answer, sources, and follow-up questions.
    """

    name: ClassVar[str] = "get_research_result"
    description: ClassVar[str] = (
        "Get the full result of a completed research task. "
        "Returns detailed answer, sources, and follow-up questions. "
        "Only works for completed tasks."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = GetResearchResultInput
    output_model: ClassVar[type[BaseModel]] = GetResearchResultOutput

    async def execute(self, input_data: GetResearchResultInput) -> GetResearchResultOutput:
        """Get research result."""
        import json

        queue = get_queue()
        task = queue.get_task(input_data.task_id)

        if not task:
            raise ValueError(f"Task {input_data.task_id} not found")

        if task.status != TaskStatus.COMPLETED:
            raise ValueError(
                f"Task {input_data.task_id} is not completed (status: {task.status.value})"
            )

        if not task.result_json:
            raise ValueError(f"Task {input_data.task_id} has no result data")

        # Parse result
        result_data = json.loads(task.result_json)

        return GetResearchResultOutput(
            task_id=task.task_id,
            query=result_data.get("query", task.query),
            summary=result_data.get("summary", ""),
            detailed_answer=result_data.get("detailed_answer", ""),
            sources=[SearchResult(**s) for s in result_data.get("sources", [])],
            follow_up_questions=result_data.get("follow_up_questions", []),
            provider=result_data.get("provider", task.provider),
            output_file_path=result_data.get("output_file_path"),
        )


@register_tool(domain="deep_research")
class CancelResearchTask(BaseTool[CancelResearchTaskInput, CancelResearchTaskOutput]):
    """Cancel a pending or running research task.

    Stops a background research task that hasn't completed yet.
    """

    name: ClassVar[str] = "cancel_research_task"
    description: ClassVar[str] = (
        "Cancel a pending or running research task. "
        "Cannot cancel completed or failed tasks."
    )
    domain: ClassVar[str] = "deep_research"
    input_model: ClassVar[type[BaseModel]] = CancelResearchTaskInput
    output_model: ClassVar[type[BaseModel]] = CancelResearchTaskOutput

    async def execute(self, input_data: CancelResearchTaskInput) -> CancelResearchTaskOutput:
        """Cancel research task."""
        queue = get_queue()
        success = queue.cancel_task(input_data.task_id)

        if success:
            message = f"Task {input_data.task_id} cancelled successfully"
        else:
            message = f"Task {input_data.task_id} could not be cancelled (not found or already completed)"

        return CancelResearchTaskOutput(
            task_id=input_data.task_id,
            success=success,
            message=message,
        )
