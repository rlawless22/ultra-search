"""MCP Server implementation for Ultra Search.

This server exposes all registered tools as MCP tools that Claude Code can call.
Tools are dynamically discovered from the domains package.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from ultra_search.core.config import Settings, get_settings
from ultra_search.core.registry import discover_domains, get_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("ultra-search")


def get_tool_schema(tool_cls: type) -> dict[str, Any]:
    """Get JSON schema for a tool's input model.

    Args:
        tool_cls: Tool class with input_model attribute

    Returns:
        JSON schema dictionary
    """
    if hasattr(tool_cls, "input_model"):
        return tool_cls.input_model.model_json_schema()
    return {"type": "object", "properties": {}}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools from enabled domains.

    Returns tools dynamically based on:
    1. Which domains are enabled in settings
    2. Which tools are registered in those domains
    """
    settings = get_settings()
    enabled_domains = settings.get_enabled_domains()
    tools = get_tools(enabled_domains)

    logger.info(f"Listing tools for domains: {enabled_domains}")
    logger.info(f"Found {len(tools)} tools")

    mcp_tools = []
    for name, tool_cls in tools.items():
        try:
            mcp_tools.append(
                Tool(
                    name=name,
                    description=getattr(tool_cls, "description", f"Tool: {name}"),
                    inputSchema=get_tool_schema(tool_cls),
                )
            )
        except Exception as e:
            logger.error(f"Error creating tool schema for {name}: {e}")

    return mcp_tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool and return results.

    Args:
        name: Tool name to execute
        arguments: Tool input arguments

    Returns:
        List of TextContent with the tool result
    """
    settings = get_settings()
    enabled_domains = settings.get_enabled_domains()
    tools = get_tools(enabled_domains)

    if name not in tools:
        error_msg = f"Tool '{name}' not found or not enabled. Available: {list(tools.keys())}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    try:
        tool_cls = tools[name]
        tool = tool_cls(settings)

        # Validate and execute
        validated_input = tool.input_model(**arguments)
        result = await tool.execute(validated_input)

        # Serialize result
        if hasattr(result, "model_dump_json"):
            result_json = result.model_dump_json(indent=2)
        else:
            result_json = json.dumps(result, indent=2, default=str)

        logger.info(f"Tool '{name}' executed successfully")
        return [TextContent(type="text", text=result_json)]

    except Exception as e:
        error_msg = f"Error executing tool '{name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]


async def serve() -> None:
    """Start the MCP server.

    This function:
    1. Discovers all domain tools
    2. Starts the stdio server for MCP communication
    """
    # Discover all domains and their tools
    discover_domains()

    settings = get_settings()
    enabled = settings.get_enabled_domains()
    tools = get_tools(enabled)

    logger.info("=" * 50)
    logger.info("Ultra Search MCP Server Starting")
    logger.info(f"Enabled domains: {enabled}")
    logger.info(f"Available tools: {list(tools.keys())}")
    logger.info("=" * 50)

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Entry point for the MCP server."""
    asyncio.run(serve())


if __name__ == "__main__":
    main()
