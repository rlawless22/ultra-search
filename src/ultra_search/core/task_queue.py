"""Background task queue for long-running research operations.

This module provides:
- Task queue storage (SQLite)
- Background task execution
- Task status tracking
- Result persistence
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Status of a background task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about a background task."""

    task_id: str
    tool_name: str
    query: str
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: int = 0  # 0-100
    output_file: str | None = None
    error: str | None = None
    result_json: str | None = None
    provider: str | None = None
    estimated_duration_seconds: int | None = None


class TaskQueue:
    """SQLite-backed task queue for background execution."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize task queue.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.ultra_search/tasks.db
        """
        if db_path is None:
            db_dir = Path.home() / ".ultra_search"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "tasks.db"

        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    progress INTEGER DEFAULT 0,
                    output_file TEXT,
                    error TEXT,
                    result_json TEXT,
                    provider TEXT,
                    estimated_duration_seconds INTEGER,
                    input_json TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def create_task(
        self,
        tool_name: str,
        query: str,
        input_data: dict[str, Any],
        output_file: str | None = None,
        estimated_duration: int | None = None,
    ) -> str:
        """Create a new background task.

        Args:
            tool_name: Name of the tool to execute
            query: Research query
            input_data: Full input data for the tool
            output_file: Optional output file path
            estimated_duration: Estimated duration in seconds

        Returns:
            task_id: Unique identifier for the task
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        created_at = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, tool_name, query, status, created_at,
                    output_file, estimated_duration_seconds, input_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    tool_name,
                    query,
                    TaskStatus.PENDING.value,
                    created_at,
                    output_file,
                    estimated_duration,
                    json.dumps(input_data),
                ),
            )
            conn.commit()

        return task_id

    def get_task(self, task_id: str) -> TaskInfo | None:
        """Get task information.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            )
            row = cursor.fetchone()

        if not row:
            return None

        return TaskInfo(
            task_id=row["task_id"],
            tool_name=row["tool_name"],
            query=row["query"],
            status=TaskStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None,
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
            progress=row["progress"],
            output_file=row["output_file"],
            error=row["error"],
            result_json=row["result_json"],
            provider=row["provider"],
            estimated_duration_seconds=row["estimated_duration_seconds"],
        )

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: int | None = None,
        error: str | None = None,
    ) -> None:
        """Update task status.

        Args:
            task_id: Task identifier
            status: New status
            progress: Optional progress percentage (0-100)
            error: Optional error message
        """
        updates = {"status": status.value}

        if status == TaskStatus.RUNNING and progress is None:
            updates["started_at"] = datetime.utcnow().isoformat()

        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            updates["completed_at"] = datetime.utcnow().isoformat()

        if progress is not None:
            updates["progress"] = progress

        if error is not None:
            updates["error"] = error

        # Build UPDATE query
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [task_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE task_id = ?", values
            )
            conn.commit()

    def save_task_result(
        self, task_id: str, result: BaseModel, provider: str | None = None
    ) -> None:
        """Save task result.

        Args:
            task_id: Task identifier
            result: Result object (Pydantic model)
            provider: Provider name
        """
        result_json = result.model_dump_json()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET result_json = ?, provider = ? WHERE task_id = ?",
                (result_json, provider, task_id),
            )
            conn.commit()

    def list_tasks(
        self, status: TaskStatus | None = None, limit: int = 50
    ) -> list[TaskInfo]:
        """List tasks, optionally filtered by status.

        Args:
            status: Optional status filter
            limit: Maximum number of tasks to return

        Returns:
            List of TaskInfo objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if status:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
                )

            rows = cursor.fetchall()

        tasks = []
        for row in rows:
            tasks.append(
                TaskInfo(
                    task_id=row["task_id"],
                    tool_name=row["tool_name"],
                    query=row["query"],
                    status=TaskStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    started_at=datetime.fromisoformat(row["started_at"])
                    if row["started_at"]
                    else None,
                    completed_at=datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None,
                    progress=row["progress"],
                    output_file=row["output_file"],
                    error=row["error"],
                    result_json=row["result_json"],
                    provider=row["provider"],
                    estimated_duration_seconds=row["estimated_duration_seconds"],
                )
            )

        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if task not found or already completed
        """
        task = self.get_task(task_id)
        if not task:
            return False

        if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return False

        self.update_task_status(task_id, TaskStatus.CANCELLED)
        return True


# Global queue instance
_queue: TaskQueue | None = None


def get_queue() -> TaskQueue:
    """Get the global task queue instance."""
    global _queue
    if _queue is None:
        _queue = TaskQueue()
    return _queue


def execute_task_in_background(task_id: str) -> None:
    """Execute a task in a background process.

    This function is run in a separate process via multiprocessing.

    Args:
        task_id: Task identifier
    """
    import sys

    # Import here to avoid circular imports in subprocess
    from ultra_search.core.config import get_settings
    from ultra_search.core.registry import discover_domains, get_tools

    queue = get_queue()
    task = queue.get_task(task_id)

    if not task:
        return

    try:
        # Discover tools
        discover_domains()

        # Update status to running
        queue.update_task_status(task_id, TaskStatus.RUNNING, progress=10)

        # Get settings and tools
        settings = get_settings()
        tools = get_tools(settings.get_enabled_domains())

        if task.tool_name not in tools:
            raise ValueError(f"Tool {task.tool_name} not found")

        # Load input data
        with sqlite3.connect(queue.db_path) as conn:
            cursor = conn.execute(
                "SELECT input_json FROM tasks WHERE task_id = ?", (task_id,)
            )
            input_json = cursor.fetchone()[0]

        input_data = json.loads(input_json)

        # Execute tool
        tool_cls = tools[task.tool_name]
        tool = tool_cls(settings)

        # Progress update
        queue.update_task_status(task_id, TaskStatus.RUNNING, progress=30)

        # Run async execution in this process
        validated_input = tool.input_model(**input_data)
        result = asyncio.run(tool.execute(validated_input))

        # Save result
        queue.update_task_status(task_id, TaskStatus.RUNNING, progress=90)
        queue.save_task_result(task_id, result, provider=getattr(result, "provider", None))

        # Mark completed
        queue.update_task_status(task_id, TaskStatus.COMPLETED, progress=100)

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        queue.update_task_status(task_id, TaskStatus.FAILED, error=error_msg)


def start_background_task(task_id: str) -> None:
    """Start a task in a background process.

    Args:
        task_id: Task identifier
    """
    process = multiprocessing.Process(target=execute_task_in_background, args=(task_id,))
    process.daemon = True
    process.start()
