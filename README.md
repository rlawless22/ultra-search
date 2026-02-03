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
│   ├── web_search/    # SerpAPI, Tavily, Brave
│   ├── deep_research/ # OpenAI, Perplexity
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

# Domain settings
ULTRA_DOMAINS__WEB_SEARCH__ENABLED=true
ULTRA_DOMAINS__WEB_SEARCH__DEFAULT_PROVIDER=serpapi
```

## Available Tools

- `search_web` - Web search via SerpAPI, Tavily, or Brave
- `search_news` - News article search
- `deep_research` - AI-powered comprehensive research
- `quick_answer` - Fast factual answers

## License

MIT
