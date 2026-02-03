"""File output utilities for saving tool results."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class OutputFormat(str, Enum):
    """Supported output file formats."""

    JSON = "json"
    MARKDOWN = "md"
    TEXT = "txt"
    HTML = "html"


class FileOutputConfig(BaseModel):
    """Configuration for file output."""

    path: str | Path
    format: OutputFormat = OutputFormat.JSON
    append: bool = False
    add_timestamp: bool = True
    create_dirs: bool = True


async def write_result_to_file(
    result: BaseModel | dict[str, Any],
    config: FileOutputConfig,
) -> Path:
    """Write a tool result to a file.

    Args:
        result: Result object (Pydantic model or dict)
        config: File output configuration

    Returns:
        Path to the written file

    Raises:
        IOError: If file writing fails
    """
    output_path = Path(config.path)

    # Create directories if needed
    if config.create_dirs:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert result to dict if it's a Pydantic model
    if isinstance(result, BaseModel):
        result_dict = result.model_dump(mode="python")
    else:
        result_dict = result

    # Generate content based on format
    content = _format_content(result_dict, config.format)

    # Add timestamp header if requested
    if config.add_timestamp:
        timestamp = datetime.utcnow().isoformat()
        if config.format == OutputFormat.MARKDOWN:
            header = f"# Generated: {timestamp}\n\n"
        elif config.format == OutputFormat.HTML:
            header = f"<!-- Generated: {timestamp} -->\n\n"
        elif config.format == OutputFormat.JSON:
            result_dict["_generated_at"] = timestamp
            content = _format_content(result_dict, config.format)
            header = ""
        else:
            header = f"Generated: {timestamp}\n\n"
        content = header + content

    # Write to file
    mode = "a" if config.append else "w"
    output_path.write_text(content, encoding="utf-8")

    return output_path


def _format_content(data: dict[str, Any], format: OutputFormat) -> str:
    """Format data according to output format.

    Args:
        data: Data dictionary to format
        format: Desired output format

    Returns:
        Formatted string content
    """
    if format == OutputFormat.JSON:
        return json.dumps(data, indent=2, default=str)

    elif format == OutputFormat.MARKDOWN:
        return _to_markdown(data)

    elif format == OutputFormat.HTML:
        return _to_html(data)

    else:  # TEXT
        return _to_text(data)


def _to_markdown(data: dict[str, Any]) -> str:
    """Convert data to Markdown format."""
    lines = []

    # Handle common research result fields
    if "query" in data:
        lines.append(f"# Research: {data['query']}\n")

    if "summary" in data:
        lines.append("## Summary\n")
        lines.append(f"{data['summary']}\n")

    if "detailed_answer" in data:
        lines.append("## Detailed Answer\n")
        lines.append(f"{data['detailed_answer']}\n")

    if "results" in data:
        lines.append("## Results\n")
        for i, result in enumerate(data["results"], 1):
            if isinstance(result, dict):
                lines.append(f"### {i}. {result.get('title', 'Result')}\n")
                if "url" in result:
                    lines.append(f"**URL:** {result['url']}\n")
                if "snippet" in result:
                    lines.append(f"{result['snippet']}\n")
            lines.append("")

    if "sources" in data:
        lines.append("## Sources\n")
        for i, source in enumerate(data["sources"], 1):
            if isinstance(source, dict):
                title = source.get("title", "Source")
                url = source.get("url", "")
                lines.append(f"{i}. [{title}]({url})")
        lines.append("")

    if "follow_up_questions" in data and data["follow_up_questions"]:
        lines.append("## Follow-up Questions\n")
        for question in data["follow_up_questions"]:
            lines.append(f"- {question}")
        lines.append("")

    # Add metadata if present
    if "metadata" in data:
        lines.append("## Metadata\n")
        lines.append("```json")
        lines.append(json.dumps(data["metadata"], indent=2))
        lines.append("```\n")

    return "\n".join(lines)


def _to_html(data: dict[str, Any]) -> str:
    """Convert data to HTML format."""
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <title>Research Results</title>",
        "  <style>",
        "    body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }",
        "    h1 { color: #333; }",
        "    h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }",
        "    .result { margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #4CAF50; }",
        "    .source { margin: 10px 0; }",
        "    a { color: #1976D2; text-decoration: none; }",
        "    a:hover { text-decoration: underline; }",
        "  </style>",
        "</head>",
        "<body>",
    ]

    if "query" in data:
        lines.append(f"  <h1>Research: {data['query']}</h1>")

    if "summary" in data:
        lines.append("  <h2>Summary</h2>")
        lines.append(f"  <p>{data['summary']}</p>")

    if "detailed_answer" in data:
        lines.append("  <h2>Detailed Answer</h2>")
        lines.append(f"  <p>{data['detailed_answer']}</p>")

    if "results" in data:
        lines.append("  <h2>Results</h2>")
        for result in data["results"]:
            if isinstance(result, dict):
                lines.append("  <div class='result'>")
                lines.append(f"    <h3>{result.get('title', 'Result')}</h3>")
                if "url" in result:
                    lines.append(f"    <p><a href='{result['url']}'>{result['url']}</a></p>")
                if "snippet" in result:
                    lines.append(f"    <p>{result['snippet']}</p>")
                lines.append("  </div>")

    if "sources" in data:
        lines.append("  <h2>Sources</h2>")
        for i, source in enumerate(data["sources"], 1):
            if isinstance(source, dict):
                lines.append("  <div class='source'>")
                title = source.get("title", "Source")
                url = source.get("url", "")
                lines.append(f"    {i}. <a href='{url}'>{title}</a>")
                lines.append("  </div>")

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines)


def _to_text(data: dict[str, Any]) -> str:
    """Convert data to plain text format."""
    lines = []

    if "query" in data:
        lines.append(f"RESEARCH: {data['query']}")
        lines.append("=" * 80)
        lines.append("")

    if "summary" in data:
        lines.append("SUMMARY:")
        lines.append(data["summary"])
        lines.append("")

    if "detailed_answer" in data:
        lines.append("DETAILED ANSWER:")
        lines.append(data["detailed_answer"])
        lines.append("")

    if "results" in data:
        lines.append("RESULTS:")
        lines.append("-" * 80)
        for i, result in enumerate(data["results"], 1):
            if isinstance(result, dict):
                lines.append(f"\n{i}. {result.get('title', 'Result')}")
                if "url" in result:
                    lines.append(f"   URL: {result['url']}")
                if "snippet" in result:
                    lines.append(f"   {result['snippet']}")

    if "sources" in data:
        lines.append("\nSOURCES:")
        lines.append("-" * 80)
        for i, source in enumerate(data["sources"], 1):
            if isinstance(source, dict):
                lines.append(f"{i}. {source.get('title', 'Source')}")
                lines.append(f"   {source.get('url', '')}")

    return "\n".join(lines)
