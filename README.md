# Ultra Search

Modular multi-domain research tool with MCP integration for Claude Code.

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Run MCP server
python -m ultra_search.mcp_server.server
```

## Architecture

```
src/ultra_search/
├── core/           # Framework core
│   ├── base.py     # Abstract base classes
│   ├── registry.py # Tool auto-registration
│   ├── config.py   # Pydantic settings
│   └── executor.py # Async execution
│
├── domains/        # Plug-and-play domains
│   ├── web_search/    # SerpAPI, Tavily, Brave, Parallel
│   ├── deep_research/ # OpenAI, Perplexity, Parallel Tasks
│   ├── financial/     # Polygon, Alpha Vantage
│   ├── academic/      # Semantic Scholar, arXiv
│   └── ...
│
└── mcp_server/     # MCP server for Claude Code
```

## Adding a New Domain

1. Create a folder in `domains/`
2. Create `domain.py` with tools using `@register_tool(domain="name")`
3. Create `providers/` with API implementations
4. Enable in config: `ULTRA_DOMAINS__NAME__ENABLED=true`

## Configuration

Environment variables use the `ULTRA_` prefix:

```bash
# API Keys
ULTRA_OPENAI_API_KEY=sk-...
ULTRA_SERPAPI_API_KEY=...
ULTRA_PARALLEL_API_KEY=...

# Domain settings
ULTRA_DOMAINS__WEB_SEARCH__ENABLED=true
ULTRA_DOMAINS__WEB_SEARCH__DEFAULT_PROVIDER=parallel  # or serpapi, tavily, brave
ULTRA_DOMAINS__DEEP_RESEARCH__DEFAULT_PROVIDER=parallel  # or openai, perplexity
```

## Available Tools

### Synchronous Tools (Return Results Immediately)
- `search_web` - Web search via SerpAPI, Tavily, Brave, or Parallel
- `search_news` - News article search
- `deep_research` - AI-powered research (use for quick/standard depth, < 5 minutes)
- `quick_answer` - Fast factual answers

### Async Tools (For Long-Running Research)
**NEW!** Background research that can run for hours without timeout:

- `start_deep_research_async` - Start research in background, returns task_id immediately
- `check_research_status` - Check progress and status of a running task
- `list_research_tasks` - List all research tasks (running, completed, failed)
- `get_research_result` - Get full results when task completes
- `cancel_research_task` - Cancel a running task

**Use async tools for comprehensive research that takes 5+ minutes!**

See [Async Research Guide](docs/async-research-guide.md) for details.

### File Output Support

All tools support saving results to files in multiple formats:

```python
# Save research to markdown
deep_research(
    query="AI trends 2026",
    output_file="research/ai_trends.md"
)

# Save search results as JSON
search_web(
    query="quantum computing",
    output_file="results.json"
)
```

**Supported formats:** JSON (`.json`), Markdown (`.md`), HTML (`.html`), Plain Text (`.txt`)

See [File Output Guide](docs/file-output-guide.md) for details.

## License

MIT
