"""OpenSanctions API provider for sanctions and watchlist screening.

OpenSanctions is an open-source sanctions and PEP database.
Docs: https://www.opensanctions.org/docs/api/

FREE TIER AVAILABLE - Requires API key (free with business email)
Sign up: https://www.opensanctions.org/api/

Coverage:
- OFAC (US Treasury)
- UN Security Council
- EU sanctions
- UK sanctions
- Interpol red notices
- PEP databases
- Criminal watchlists
"""

from __future__ import annotations

from typing import Any

import httpx

from ultra_search.core.base import BaseProvider
from ultra_search.domains.risk_screening.domain import (
    SanctionsMatch,
    SanctionsScreeningResult,
)


class OpenSanctionsProvider(BaseProvider):
    """OpenSanctions API provider.

    FREE TIER: Sign up with business email at https://www.opensanctions.org/api/
    Set: ULTRA_OPENSANCTIONS_API_KEY=your-free-key

    Rate limits: 100 requests/hour (free tier)
    """

    provider_name = "opensanctions"
    base_url = "https://api.opensanctions.org"
    requires_auth = True  # Now requires API key (but free tier available!)

    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with API key authentication."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "OpenSanctions requires a free API key. "
                    "Sign up at: https://www.opensanctions.org/api/ "
                    "Then set: ULTRA_OPENSANCTIONS_API_KEY"
                )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"ApiKey {self.api_key}",
                    "Accept": "application/json",
                    "User-Agent": "UltraSearch/1.0 (Research Tool)",
                },
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make request to OpenSanctions API."""
        client = await self.get_client()
        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def screen_entity(
        self,
        entity_name: str,
        entity_type: str = "organization",
        countries: list[str] | None = None,
        fuzzy: bool = True,
    ) -> SanctionsScreeningResult:
        """Screen entity against sanctions databases.

        Args:
            entity_name: Name to screen
            entity_type: organization, person, or vessel
            countries: Optional country filters
            fuzzy: Enable fuzzy matching

        Returns:
            Sanctions screening results with matches
        """
        # Build query params
        params = {
            "q": entity_name,
            "schema": entity_type if entity_type != "organization" else "Company",
            "limit": 50,
        }

        if countries:
            params["countries"] = ",".join(countries)

        if not fuzzy:
            params["fuzzy"] = "false"

        # Search OpenSanctions
        data = await self._make_request("GET", "/search/default", params=params)

        return self._parse_results(entity_name, data)

    def _parse_results(
        self,
        query_name: str,
        data: dict[str, Any],
    ) -> SanctionsScreeningResult:
        """Parse OpenSanctions API response."""
        results = data.get("results", [])

        matches: list[SanctionsMatch] = []
        datasets_found = set()

        for result in results:
            # Extract entity data
            properties = result.get("properties", {})
            score = result.get("score", 0.0)

            # Get all names/aliases
            names = properties.get("name", [])
            aliases = properties.get("alias", [])
            all_names = names + aliases

            # Get countries
            countries = properties.get("country", [])

            # Get datasets this entity appears in
            datasets = result.get("datasets", [])
            for ds in datasets:
                datasets_found.add(ds)

            # Primary name
            primary_name = names[0] if names else query_name

            # Sanction reason
            reason = properties.get("reason", [])
            reason_text = reason[0] if reason else None

            # Listed date
            listed_dates = properties.get("listedAt", [])
            listed_date = listed_dates[0] if listed_dates else None

            matches.append(
                SanctionsMatch(
                    entity_name=primary_name,
                    match_score=score,
                    dataset=", ".join(datasets),
                    entity_type=result.get("schema"),
                    aliases=all_names[1:],  # Exclude primary name
                    countries=countries,
                    listed_date=listed_date,
                    reason=reason_text,
                    metadata=result,
                )
            )

        # Calculate highest match score
        highest_score = max([m.match_score for m in matches], default=0.0)

        # Determine risk level
        if highest_score > 0.9:
            risk_level = "high"
        elif highest_score > 0.7:
            risk_level = "medium"
        elif highest_score > 0.5:
            risk_level = "low"
        else:
            risk_level = "clear"

        return SanctionsScreeningResult(
            query_name=query_name,
            total_matches=len(matches),
            matches=matches,
            highest_match_score=highest_score,
            risk_level=risk_level,
            provider=self.provider_name,
            screened_datasets=list(datasets_found),
        )
