"""Research domains for Ultra Search.

Each subdirectory is a self-contained domain that can be:
- Enabled/disabled via configuration
- Swapped out entirely (plug and play)
- Extended with new providers

Available domains:
- web_search: General web search (SerpAPI, Tavily, Brave, Parallel)
- deep_research: AI-powered research (OpenAI, Perplexity, Parallel)
- regulatory_compliance: Carrier authority and business verification (FMCSA, Middesk)
- reviews: Multi-platform review aggregation (Google Places, Yelp)
- risk_screening: Sanctions screening and adverse media (OpenSanctions, NewsAPI)
- financial: Financial data and market research
- legal: Legal documents and case law
- academic: Academic papers and research
- social_media: Social media search
- business_intel: Business and company information
- people_search: People lookup and contact finding
- news: News article search
- scraping: Web scraping and content extraction
"""

# Import domains to trigger registration
# These imports are intentionally here to auto-register tools when the package loads

try:
    from ultra_search.domains import web_search
except ImportError:
    pass

try:
    from ultra_search.domains import deep_research
except ImportError:
    pass

try:
    from ultra_search.domains import regulatory_compliance
except ImportError:
    pass

try:
    from ultra_search.domains import reviews
except ImportError:
    pass

try:
    from ultra_search.domains import risk_screening
except ImportError:
    pass
