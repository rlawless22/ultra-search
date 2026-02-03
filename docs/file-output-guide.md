# File Output Guide

Ultra Search tools now support automatic file output, allowing you to save research results directly to disk in multiple formats.

## Supported Tools

The following tools support file output:
- `search_web` - Web search results
- `search_news` - News search results
- `deep_research` - AI-powered comprehensive research
- `quick_answer` - Quick factual answers

## Supported Formats

| Format | Extension | Best For |
|--------|-----------|----------|
| **JSON** | `.json` | Structured data, API integration, parsing |
| **Markdown** | `.md` | Documentation, readable reports, GitHub |
| **HTML** | `.html` | Web viewing, formatted reports, sharing |
| **Plain Text** | `.txt` | Simple logs, basic reports |

## Usage

### Basic Usage

Simply add the `output_file` parameter to any supported tool call:

```python
# Save as JSON (auto-detected from extension)
search_web(
    query="AI research trends 2026",
    num_results=10,
    output_file="results/ai_research.json"
)

# Save as Markdown
deep_research(
    query="Impact of quantum computing",
    depth="comprehensive",
    output_file="reports/quantum_computing.md"
)
```

### Format Override

You can override the format detection with `output_format`:

```python
# Force markdown format even with .txt extension
search_web(
    query="machine learning papers",
    output_file="research.txt",
    output_format="md"
)
```

### Claude Code Examples

When calling from Claude Code via MCP, you can request file output:

```
Please search for "climate change solutions" and save the results
to climate_research.md in markdown format.
```

I (Claude) will call:
```python
search_web(
    query="climate change solutions",
    num_results=20,
    output_file="climate_research.md"
)
```

## Output Features

### Automatic Timestamps

All files include generation timestamps:

**JSON:**
```json
{
  "_generated_at": "2026-02-03T01:05:46.211365",
  "query": "...",
  ...
}
```

**Markdown:**
```markdown
# Generated: 2026-02-03T01:05:46

# Research: Your Query
...
```

### Directory Creation

Directories are created automatically if they don't exist:

```python
# Creates results/2026/february/ if needed
output_file="results/2026/february/report.md"
```

### Result Confirmation

The tool output includes confirmation of the saved file:

```python
result = search_web(query="test", output_file="output.json")
print(result.output_file_path)  # "output.json"
```

## Format Examples

### JSON Format

**Structure:**
```json
{
  "_generated_at": "2026-02-03T01:05:46.211365",
  "query": "AI trends",
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "...",
      "source": "...",
      "metadata": {...}
    }
  ],
  "total_results": 10,
  "provider": "parallel",
  "search_type": "web"
}
```

**Best for:**
- Programmatic processing
- Database import
- API integration
- Data analysis with Python/JS

### Markdown Format

**Structure:**
```markdown
# Generated: 2026-02-03T01:05:46

# Research: AI trends

## Summary
Brief overview of findings...

## Detailed Answer
Comprehensive analysis...

## Results

### 1. Result Title
**URL:** https://example.com

Result snippet and description...

### 2. Another Result
...

## Sources
1. [Source Title](https://source-url.com)
2. [Another Source](https://another-url.com)

## Follow-up Questions
- Related question 1
- Related question 2
```

**Best for:**
- Human-readable reports
- GitHub/GitLab documentation
- Note-taking apps
- Easy sharing

### HTML Format

**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Research Results</title>
  <style>
    /* Nicely formatted styling included */
  </style>
</head>
<body>
  <h1>Research: AI trends</h1>
  <h2>Summary</h2>
  <p>...</p>
  ...
</body>
</html>
```

**Best for:**
- Web viewing
- Email sharing
- Presentations
- Client deliverables

### Plain Text Format

**Structure:**
```
Generated: 2026-02-03T01:05:46

RESEARCH: AI trends
================================================================================

SUMMARY:
Brief overview...

DETAILED ANSWER:
Comprehensive analysis...

RESULTS:
--------------------------------------------------------------------------------

1. Result Title
   URL: https://example.com
   Result snippet...
```

**Best for:**
- Terminal viewing
- Simple logs
- Email (plain text)
- Version control diffs

## Advanced Usage

### Parallel Execution with File Output

You can run multiple searches and save each to a different file:

```python
# In parallel via Claude Code:
search_web(query="AI safety", output_file="research/ai_safety.md")
search_web(query="quantum computing", output_file="research/quantum.md")
search_web(query="climate tech", output_file="research/climate.md")
deep_research(query="biotech advances", output_file="research/biotech.md")
```

All files will be written concurrently!

### Organizing Research

Use subdirectories to organize output:

```bash
research/
├── 2026/
│   ├── q1/
│   │   ├── ai_trends.md
│   │   ├── quantum_advances.md
│   │   └── climate_solutions.md
│   └── q2/
│       └── ...
└── archive/
```

### Integration with Workflows

**Example: Daily Research Digest**

```python
from datetime import date

today = date.today().strftime("%Y-%m-%d")

deep_research(
    query="Latest AI developments",
    depth="comprehensive",
    output_file=f"daily_digest/{today}_ai_digest.md"
)
```

## File Output vs. API Response

When you specify `output_file`, the tool:

1. ✅ **Still returns** the full result via MCP
2. ✅ **Also saves** the result to the specified file
3. ✅ **Includes** the file path in the response

This means you get both:
- Immediate result in Claude Code conversation
- Persistent file for later reference

## Error Handling

### Missing Directories
✅ **Automatically created** - The tool creates all parent directories

### Invalid Path
❌ **Returns error** - The tool will fail gracefully and report the issue

### Permission Denied
❌ **Returns error** - Check file/directory permissions

### Disk Full
❌ **Returns error** - Free up disk space

## Configuration

No special configuration needed! File output works out of the box with all tools.

### Default Settings

```python
# These are the defaults (can't be changed currently):
{
    "append": false,           # Overwrites existing files
    "add_timestamp": true,     # Adds generation time
    "create_dirs": true,       # Creates missing directories
}
```

## Real-World Examples

### Example 1: Market Research Report

```python
deep_research(
    query="Electric vehicle market trends 2026",
    depth="comprehensive",
    include_sources=True,
    output_file="reports/ev_market_2026.html"
)
```

**Result:** Professional HTML report ready to share with clients

### Example 2: Competitive Analysis

```python
# Search for multiple competitors
for company in ["OpenAI", "Anthropic", "Google DeepMind"]:
    search_web(
        query=f"{company} latest developments",
        num_results=20,
        output_file=f"competitive_analysis/{company.lower()}.json"
    )
```

**Result:** JSON files ready for data analysis

### Example 3: Research Paper Collection

```python
search_web(
    query="quantum computing error correction papers",
    num_results=50,
    output_file="research_papers/quantum_error_correction.md"
)
```

**Result:** Markdown list of papers with links and summaries

## Tips & Best Practices

### 1. Use Descriptive Filenames
```
✅ "2026_q1_ai_safety_research.md"
❌ "output.md"
```

### 2. Choose the Right Format
- **Analysis/Processing?** → JSON
- **Reading/Sharing?** → Markdown or HTML
- **Archiving/Logging?** → Plain Text

### 3. Organize by Date/Topic
```
research/
├── by_topic/
│   ├── ai/
│   ├── quantum/
│   └── climate/
└── by_date/
    └── 2026/
```

### 4. Include Metadata in Filenames
```
{date}_{topic}_{depth}_{provider}.{ext}
2026-02-03_ai_trends_comprehensive_parallel.md
```

### 5. Version Control Integration
JSON and Markdown formats work great with Git:
```bash
git add research/*.md
git commit -m "Add Feb 2026 research reports"
```

## Limitations

- **No append mode** (yet) - Files are always overwritten
- **No compression** - Large result sets create large files
- **No encryption** - Files are saved in plain text
- **Local filesystem only** - No S3/cloud storage (yet)

## Future Enhancements

Planned features:
- Append mode for continuous logging
- Custom templates for formatting
- Cloud storage integration (S3, GCS)
- Automatic compression for large files
- Encrypted output option
- Custom timestamp formats

---

## Quick Reference

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `output_file` | `string` | No | File path to save results |
| `output_format` | `string` | No | Format override: `json`, `md`, `txt`, `html` |

**Supported Tools:**
- `search_web`
- `search_news`
- `deep_research`
- `quick_answer`

**Auto-detected Extensions:**
`.json`, `.md`, `.txt`, `.html`
