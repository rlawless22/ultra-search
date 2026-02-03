# Parallel AI Integration Guide

Parallel AI has been integrated into Ultra Search in two domains:

## 1. Web Search (Search API)

The Parallel Search API provides AI-native web search with token-efficient results.

### Features
- Token-efficient results optimized for AI consumption
- Handles JavaScript-rendered content
- Extracts content from complex PDFs
- Evidence-based search results
- Low cost compared to traditional search APIs

### Configuration

```bash
# Set your Parallel API key
export ULTRA_PARALLEL_API_KEY=your-api-key-here

# Use Parallel for web search
export ULTRA_DOMAINS__WEB_SEARCH__DEFAULT_PROVIDER=parallel
```

### Usage via MCP

```python
# Claude Code will automatically use Parallel when configured
search_web(query="latest AI research 2026", num_results=10)
```

### API Endpoints Used
- `POST /v1/search` - Main search endpoint

---

## 2. Deep Research (Tasks API)

The Parallel Tasks API enables comprehensive multi-step research with source citations.

### Features
- Comprehensive web research
- Multi-step task execution
- Evidence-based analysis with credibility scoring
- Automatic source citation
- Long-running task support with polling

### Configuration

```bash
# Same API key as search (shared)
export ULTRA_PARALLEL_API_KEY=your-api-key-here

# Use Parallel for deep research
export ULTRA_DOMAINS__DEEP_RESEARCH__DEFAULT_PROVIDER=parallel
```

### Usage via MCP

```python
# Research with depth control
deep_research(
    query="Impact of quantum computing on cryptography",
    depth="comprehensive"  # or "quick", "standard"
)
```

### Research Depth Levels

| Depth | Complexity | Max Sources | Use Case |
|-------|-----------|-------------|----------|
| `quick` | simple | 10 | Fast factual lookups |
| `standard` | moderate | 20 | Balanced research |
| `comprehensive` | complex | 50 | In-depth analysis |

### API Endpoints Used
- `POST /v1/tasks` - Create research task
- `GET /v1/tasks/{task_id}` - Poll task status

---

## Getting a Parallel API Key

1. Visit [https://parallel.ai/](https://parallel.ai/)
2. Sign up for an account
3. Navigate to API settings
4. Generate an API key
5. Add to your `.env` file:
   ```bash
   ULTRA_PARALLEL_API_KEY=your-key-here
   ```

---

## Benefits of Parallel AI

### Token Efficiency
Parallel's responses are optimized for AI consumption, reducing token usage compared to raw web scraping.

### Reliability
Purpose-built for AI agents, handling edge cases like:
- JavaScript-heavy sites
- Complex PDFs
- Paywalled content (where allowed)
- Dynamic content

### Cost-Effective
Lower cost per query compared to traditional search APIs while providing higher quality results for AI use cases.

### Evidence-Based
All results include credibility scoring and source citations, making it ideal for research applications.

---

## Example Outputs

### Web Search Response
```json
{
  "title": "AI Research Paper Title",
  "url": "https://arxiv.org/paper/...",
  "snippet": "Token-efficient summary...",
  "content": "Full extracted content...",
  "relevance_score": 0.95,
  "metadata": {
    "token_count": 150,
    "domain": "arxiv.org",
    "published_date": "2026-01-15"
  }
}
```

### Research Response
```json
{
  "query": "Impact of quantum computing...",
  "summary": "Brief 500-char summary...",
  "detailed_answer": "Comprehensive analysis...",
  "sources": [...],
  "confidence_score": 0.89,
  "metadata": {
    "task_id": "task_123",
    "total_sources_found": 45,
    "processing_time_ms": 12500
  }
}
```

---

## Troubleshooting

### API Key Not Working
- Verify the key is set: `echo $ULTRA_PARALLEL_API_KEY`
- Check the key is valid in your Parallel dashboard
- Ensure no extra whitespace in the key

### Timeout Errors
For deep research tasks, increase timeout:
```bash
ULTRA_DEFAULT_TIMEOUT=120.0  # 2 minutes
```

### Rate Limiting
Parallel has rate limits based on your plan. Consider:
- Implementing exponential backoff (already built-in)
- Upgrading your plan
- Caching results

---

## Documentation Links

- [Parallel AI Official Docs](https://docs.parallel.ai/)
- [Search API Reference](https://docs.parallel.ai/search)
- [Tasks API Reference](https://docs.parallel.ai/tasks)
- [Pricing](https://parallel.ai/pricing)

---

## Next Steps

1. Get your Parallel API key
2. Add it to `.env`
3. Test with: `search_web(query="test", num_results=3)`
4. Use for production research tasks
