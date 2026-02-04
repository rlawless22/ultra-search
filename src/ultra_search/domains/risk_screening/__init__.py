"""Risk Screening domain - Sanctions, watchlists, and adverse media monitoring.

Providers:
- opensanctions: OpenSanctions API (free, sanctions/PEP/watchlists)
- newsapi: NewsAPI for adverse media monitoring
- gdelt: GDELT Doc API for global news/event monitoring

Tools:
- screen_sanctions: Check entity against sanctions/watchlists
- search_adverse_media: Search for negative news/complaints
- monitor_entity_risk: Combined screening + adverse media
"""

from ultra_search.domains.risk_screening import domain  # noqa: F401

__all__ = []
