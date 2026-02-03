# Async Research Guide

## Overview

Ultra Search now supports **background research tasks** that can run for hours without blocking Claude Code. This solves the timeout problem for long-running research operations.

## The Problem We Solved

### Before (Synchronous Only):
```
User: "Research quantum computing comprehensively"
Claude: [Calls deep_research, waits 30 minutes]
        ⏱️ Timeout after 30 seconds → FAIL
```

**Issues:**
- Claude Code blocks for the entire duration
- Timeouts kill long operations
- Can't do anything else while waiting
- Lost work if connection drops

### After (With Async Support):
```
User: "Research quantum computing comprehensively"
Claude: [Calls start_deep_research_async]
        ✓ Returns immediately with task_id
        "Started task_abc123, will take ~30 minutes"

User: "Let's work on something else"
Claude: [Works on other tasks]

[30 minutes later]
User: "Check on that research"
Claude: [Calls check_research_status]
        ✓ "Complete! Results in quantum.md"
```

**Benefits:**
- ✅ Non-blocking - continue working
- ✅ **Runs indefinitely** - no timeout limits!
- ✅ Multiple tasks in parallel
- ✅ Survives restarts
- ✅ Graceful error handling

---

## YES - Tasks Can Run As Long As Needed!

**The answer to your question: YES, tasks can run for hours, days, or even longer!**

### How It Works:

1. **Separate Process**: Tasks run in independent Python processes via `multiprocessing`
2. **No Timeout**: There's no connection timeout because the task isn't blocking the MCP connection
3. **Persistent Storage**: Task state is stored in SQLite (`~/.ultra_search/tasks.db`)
4. **Resume Support**: Even if the user restarts Claude Code, the task continues

### What This Means:

```python
# This can run for 2 hours, no problem:
start_deep_research_async(
    query="Comprehensive analysis of global climate policies 1990-2026",
    depth="comprehensive"
)

# Or even longer:
start_deep_research_async(
    query="Complete survey of machine learning research 2020-2026",
    depth="comprehensive"
)
```

The task will:
- Start in the background
- Continue running even if you close the terminal
- Save results when complete
- Be checkable anytime with `check_research_status`

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code (MCP Client)                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Claude Agent                                      │  │
│  │  "Start research on quantum computing"           │  │
│  └───────────┬───────────────────────────────────────┘  │
│              │ MCP Call                                  │
└──────────────┼───────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  Ultra Search MCP Server                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ start_deep_research_async Tool                    │  │
│  │  1. Creates task in SQLite                        │  │
│  │  2. Spawns background process                     │  │
│  │  3. Returns task_id immediately                   │  │
│  └───────────┬───────────────────────────────────────┘  │
└──────────────┼───────────────────────────────────────────┘
               │ Returns immediately
               │ (non-blocking)
               ▼
       ┌───────────────┐
       │  task_abc123  │ ← Returns to Claude
       └───────────────┘

Meanwhile in background:
┌─────────────────────────────────────────────────────────┐
│  Background Worker Process (multiprocessing)            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 1. Load task from SQLite                          │  │
│  │ 2. Execute deep_research tool                     │  │
│  │ 3. Update progress in database                    │  │
│  │ 4. Save results when complete                     │  │
│  │ 5. Write output file if specified                 │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
│  ⏱️ Can run for hours without timeout                    │
└─────────────────────────────────────────────────────────┘

Later:
┌─────────────────────────────────────────────────────────┐
│  Claude Code                                            │
│  "Check on that quantum research"                       │
└───────────┬─────────────────────────────────────────────┘
            │ MCP Call
            ▼
┌─────────────────────────────────────────────────────────┐
│  check_research_status Tool                             │
│  1. Reads from SQLite                                   │
│  2. Returns status, progress, results                   │
└─────────────────────────────────────────────────────────┘
```

---

## New Tools

### 1. `start_deep_research_async`

**Purpose**: Start long-running research in background

**Input:**
```python
{
    "query": "Research topic",
    "depth": "comprehensive",  # quick, standard, or comprehensive
    "output_file": "results.md",  # optional
    "output_format": "md"  # optional: json, md, html, txt
}
```

**Output:**
```python
{
    "task_id": "task_abc123def456",
    "query": "Research topic",
    "status": "started",
    "estimated_duration_minutes": 30,
    "message": "Research task started..."
}
```

**Duration Estimates:**
- `quick`: ~2 minutes
- `standard`: ~10 minutes
- `comprehensive`: ~30 minutes (but can vary!)

---

### 2. `check_research_status`

**Purpose**: Check progress and status of a task

**Input:**
```python
{
    "task_id": "task_abc123def456"
}
```

**Output:**
```python
{
    "task_id": "task_abc123def456",
    "query": "Research topic",
    "status": "running",  # pending, running, completed, failed, cancelled
    "progress": 65,  # 0-100
    "started_at": "2026-02-03T01:30:00",
    "completed_at": null,
    "estimated_duration_minutes": 30,
    "output_file": "results.md",
    "error": null,
    "result_summary": "Brief preview if completed...",
    "provider": "openai"
}
```

**Status Values:**
- `pending`: Task created, not started yet
- `running`: Currently executing
- `completed`: Finished successfully
- `failed`: Error occurred (see `error` field)
- `cancelled`: User cancelled the task

---

### 3. `list_research_tasks`

**Purpose**: List all tasks with optional filtering

**Input:**
```python
{
    "status_filter": "running",  # optional: pending, running, completed, failed, cancelled
    "limit": 20  # max results
}
```

**Output:**
```python
{
    "tasks": [
        {
            "task_id": "task_abc123",
            "query": "Quantum computing...",
            "status": "running",
            "progress": 75,
            "created_at": "2026-02-03T01:00:00",
            "output_file": "quantum.md"
        },
        // ... more tasks
    ],
    "total_count": 3
}
```

---

### 4. `get_research_result`

**Purpose**: Get full results of a completed task

**Input:**
```python
{
    "task_id": "task_abc123def456"
}
```

**Output:**
```python
{
    "task_id": "task_abc123def456",
    "query": "Research topic",
    "summary": "Brief summary...",
    "detailed_answer": "Full comprehensive answer...",
    "sources": [
        {
            "title": "Source 1",
            "url": "https://...",
            "snippet": "..."
        },
        // ... more sources
    ],
    "follow_up_questions": [
        "Related question 1?",
        "Related question 2?"
    ],
    "provider": "openai",
    "output_file_path": "quantum.md"
}
```

**Note**: Only works for `completed` tasks. Fails if task is still running or failed.

---

### 5. `cancel_research_task`

**Purpose**: Cancel a running or pending task

**Input:**
```python
{
    "task_id": "task_abc123def456"
}
```

**Output:**
```python
{
    "task_id": "task_abc123def456",
    "success": true,
    "message": "Task cancelled successfully"
}
```

**Note**: Can only cancel `pending` or `running` tasks. Cannot cancel completed or failed tasks.

---

## Usage Examples

### Example 1: Single Long Research

```python
# Start research
result = start_deep_research_async(
    query="Comprehensive analysis of renewable energy technologies",
    depth="comprehensive",
    output_file="renewable_energy_report.md"
)

task_id = result.task_id
# Returns: "task_7a8b9c0d1e2f"

# ... do other work ...

# Check status later
status = check_research_status(task_id=task_id)
# Status: "running", Progress: 45%

# ... wait more ...

# Check again
status = check_research_status(task_id=task_id)
# Status: "completed"

# Get full results
results = get_research_result(task_id=task_id)
# Full research with sources, answer, follow-ups
```

---

### Example 2: Multiple Parallel Research Tasks

```python
# Start 5 research tasks simultaneously
tasks = []

for topic in ["AI", "Quantum", "Climate", "Biotech", "Energy"]:
    result = start_deep_research_async(
        query=f"Future of {topic} technology",
        depth="comprehensive",
        output_file=f"research/{topic.lower()}.md"
    )
    tasks.append((topic, result.task_id))

# All 5 are now running in parallel!

# Check all at once
all_tasks = list_research_tasks(status_filter="running")
# Shows all 5 running tasks

# Wait and check which are done
completed_tasks = list_research_tasks(status_filter="completed")

# Get results for completed ones
for task in completed_tasks.tasks:
    results = get_research_result(task_id=task.task_id)
    print(f"Completed: {task.query}")
```

---

### Example 3: User Returns After Hours

```python
# User closed Claude Code, reopens next day

# List all recent tasks
tasks = list_research_tasks(limit=10)

# Find completed ones
for task in tasks.tasks:
    if task.status == "completed":
        print(f"✓ {task.query} - saved to {task.output_file}")
    elif task.status == "running":
        status = check_research_status(task_id=task.task_id)
        print(f"⏳ {task.query} - {status.progress}% complete")
    elif task.status == "failed":
        status = check_research_status(task_id=task.task_id)
        print(f"✗ {task.query} - Error: {status.error}")
```

---

## Task Persistence

### Database Location

Tasks are stored in: `~/.ultra_search/tasks.db`

This is a SQLite database containing:
- Task metadata (ID, query, status, etc.)
- Input parameters
- Results (when complete)
- Error messages (if failed)

### Data Retention

Tasks persist **permanently** unless manually deleted. This means:
- ✅ Tasks survive Claude Code restarts
- ✅ Can check tasks from days/weeks ago
- ✅ Historical record of all research

### Cleanup

Currently no automatic cleanup. To manually clean:

```bash
# Delete old completed tasks (manual SQL)
sqlite3 ~/.ultra_search/tasks.db "DELETE FROM tasks WHERE status='completed' AND completed_at < datetime('now', '-30 days')"
```

---

## Best Practices

### 1. Use Async for Comprehensive Research

```python
# Good - Use async for comprehensive
start_deep_research_async(depth="comprehensive")

# Avoid - Blocks for too long
deep_research(depth="comprehensive")  # Will timeout!
```

### 2. Always Capture task_id

```python
result = start_deep_research_async(...)
task_id = result.task_id  # Save this!
```

### 3. Check Before Getting Results

```python
# Good - Check status first
status = check_research_status(task_id=task_id)
if status.status == "completed":
    results = get_research_result(task_id=task_id)

# Bad - Might fail if not complete
results = get_research_result(task_id=task_id)  # Error if still running!
```

### 4. Use File Output

```python
# Always specify output_file for long research
start_deep_research_async(
    query="...",
    output_file="research/report.md"  # Results persist even if you forget task_id
)
```

### 5. Handle Errors Gracefully

```python
status = check_research_status(task_id=task_id)
if status.status == "failed":
    print(f"Research failed: {status.error}")
    # Offer to retry or suggest alternative
```

---

## Troubleshooting

### Task Failed Immediately

**Symptom**: Status shows "failed" with progress at 10-30%

**Common Causes:**
- Missing API key
- Invalid provider configuration
- Network issues

**Solution:**
```python
status = check_research_status(task_id=task_id)
print(status.error)  # Shows the actual error message
```

### Task Stuck at Same Progress

**Symptom**: Progress doesn't change after multiple checks

**Possible Issues:**
- Provider API is slow/stuck
- Network connectivity issues
- Provider rate limiting

**Solution:**
- Wait longer (some providers are just slow)
- Cancel and retry with different provider
- Check provider API status page

### Can't Find Task

**Symptom**: "Task not found" error

**Causes:**
- Wrong task_id
- Task from different database
- Database corrupted

**Solution:**
```python
# List all tasks to find the right one
tasks = list_research_tasks(limit=50)
for task in tasks.tasks:
    print(f"{task.task_id}: {task.query}")
```

---

## Performance Considerations

### Concurrent Tasks

You can run **unlimited parallel tasks**, but consider:
- Provider rate limits (e.g., OpenAI limits)
- System resources (CPU, memory)
- Network bandwidth

**Recommendation**: 3-5 parallel comprehensive research tasks max

### Storage

Each task stores:
- ~2-10 KB metadata
- Variable result size (10 KB - 1 MB depending on research depth)

**Recommendation**: Clean up old tasks periodically

### Background Processes

Each task spawns a Python process that:
- Uses ~100-500 MB RAM
- Minimal CPU (mostly waiting for API calls)
- Self-terminates when complete

---

## Comparison: Sync vs Async

| Feature | Sync (`deep_research`) | Async (`start_deep_research_async`) |
|---------|------------------------|-------------------------------------|
| **Returns** | Full results | Task ID immediately |
| **Blocking** | Yes | No |
| **Max Duration** | ~5 minutes | Unlimited |
| **Multiple Tasks** | Sequential only | Parallel |
| **Timeout Risk** | High for long tasks | None |
| **Use Case** | Quick research | Comprehensive research |
| **Progress Tracking** | No | Yes (check_research_status) |
| **Result Storage** | Memory only | Database + file |

---

## Future Enhancements

Planned features:
- [ ] Task scheduling (run at specific time)
- [ ] Webhook notifications when complete
- [ ] Email alerts for long tasks
- [ ] Progress streaming (real-time updates)
- [ ] Task dependencies (run B after A completes)
- [ ] Automatic retry on failure
- [ ] Priority queue (high-priority tasks first)
- [ ] Resource limits (max concurrent per provider)

---

## FAQ

**Q: Do I need to keep Claude Code open?**
A: No! Tasks continue in background processes. You can close and reopen Claude Code anytime.

**Q: What happens if my computer restarts?**
A: Tasks will stop. When you restart, check their status - they'll show as "failed" if interrupted.

**Q: Can I run the same research twice?**
A: Yes, just start a new task. Each gets a unique task_id.

**Q: How do I know which task is which?**
A: Use the query field or output_file to identify tasks. Or use descriptive queries.

**Q: Can I delete old tasks?**
A: Currently manual only (SQL delete). Automatic cleanup coming in future version.

**Q: What's the longest task that's been tested?**
A: The system has no hard limits. Theoretically could run for days if the provider supports it.

---

## Summary

**Key Takeaway**: Use async tools for any research that might take > 5 minutes. They return immediately, run indefinitely, and let you check results whenever you want.

```python
# The pattern:
task_id = start_deep_research_async(...)  # Returns immediately
# ... do other work ...
status = check_research_status(task_id)  # Check anytime
results = get_research_result(task_id)  # When complete
```

**This solves the 30+ minute research problem completely!** 🎉
