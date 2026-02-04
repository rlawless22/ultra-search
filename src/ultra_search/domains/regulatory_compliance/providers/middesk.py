"""Middesk KYB (Know Your Business) API provider.

Middesk provides comprehensive business verification including:
- Entity verification
- Liens and judgments
- Bankruptcy filings
- Litigation history
- Watchlist screening
- FMCSA registration data

Documentation: https://docs.middesk.com/
API Reference: https://docs.middesk.com/api-reference

Pricing: Paid service, requires Middesk account
"""

from __future__ import annotations

from typing import Any

import httpx

from ultra_search.core.base import BaseProvider
from ultra_search.domains.regulatory_compliance.domain import BusinessVerificationInfo


class MiddeskProvider(BaseProvider):
    """Middesk KYB API provider.

    Provides comprehensive business verification and risk assessment.

    API Key: Requires paid Middesk account
    Set: ULTRA_MIDDESK_API_KEY=your-secret-key
    """

    provider_name = "middesk"
    base_url = "https://api.middesk.com/v1"
    requires_auth = True

    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with API key authentication."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Middesk requires an API key. "
                    "Sign up at https://www.middesk.com/ "
                    "Then set: ULTRA_MIDDESK_API_KEY"
                )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(60.0),  # KYB can be slow
            )
        return self._client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make authenticated request to Middesk API."""
        client = await self.get_client()
        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def verify_business(
        self,
        business_name: str,
        address: str | None = None,
        tax_id: str | None = None,
        dot_number: str | None = None,
    ) -> BusinessVerificationInfo:
        """Verify business and assess risk.

        Creates a Middesk business verification request.

        Args:
            business_name: Legal business name
            address: Business address
            tax_id: EIN/Tax ID
            dot_number: DOT number if carrier

        Returns:
            Business verification information with risk signals
        """
        # Create verification request
        payload = {
            "name": business_name,
        }

        if address:
            payload["address"] = {"full": address}

        if tax_id:
            payload["tin"] = tax_id

        # Middesk can fetch FMCSA data if DOT provided
        if dot_number:
            payload["registrations"] = {
                "fmcsa": {"dot_number": dot_number}
            }

        # POST to businesses endpoint
        data = await self._make_request("POST", "/businesses", json=payload)

        # Get business ID for detailed data
        business_id = data.get("id")

        # Fetch full verification details
        # (In production, may need to poll until verification completes)
        details = await self._make_request("GET", f"/businesses/{business_id}")

        return self._parse_verification_data(details)

    def _parse_verification_data(self, data: dict[str, Any]) -> BusinessVerificationInfo:
        """Parse Middesk API response into structured model.

        Note: Field paths based on Middesk API schema from docs.
        May need adjustment based on actual responses.
        """
        # Extract core business info
        business_name = data.get("name", "")
        addresses = data.get("addresses", [])
        primary_address = addresses[0].get("full") if addresses else None

        # Extract verification results
        verifications = data.get("verifications", {})
        tin_verified = verifications.get("tin", {}).get("status") == "verified"

        # Extract risk signals
        liens = data.get("liens", {})
        has_liens = liens.get("count", 0) > 0

        bankruptcies = data.get("bankruptcies", {})
        has_bankruptcies = bankruptcies.get("count", 0) > 0

        litigation = data.get("litigation", {})
        has_litigation = litigation.get("count", 0) > 0

        # Watchlist screening
        watchlists = data.get("watchlists", {})
        watchlist_hits = [
            w.get("list_name")
            for w in watchlists.get("hits", [])
        ]

        # FMCSA data (if carrier)
        registrations = data.get("registrations", {})
        fmcsa_data = registrations.get("fmcsa", {})
        dot_number = fmcsa_data.get("dot_number")
        fmcsa_verified = fmcsa_data.get("status") == "verified"

        # Overall verification status
        verification_status = data.get("status", "unknown")

        # Calculate risk score (0-100, higher = riskier)
        risk_score = 0.0
        if has_liens:
            risk_score += 20
        if has_bankruptcies:
            risk_score += 30
        if has_litigation:
            risk_score += 15
        if watchlist_hits:
            risk_score += 40
        if not tin_verified:
            risk_score += 10

        return BusinessVerificationInfo(
            business_name=business_name,
            legal_entity_type=data.get("entity_type"),
            tax_id_verified=tin_verified,
            business_address=primary_address,
            formation_date=data.get("formation_date"),
            state_of_incorporation=data.get("state_of_incorporation"),
            has_liens=has_liens,
            has_bankruptcies=has_bankruptcies,
            has_litigation=has_litigation,
            watchlist_hits=watchlist_hits,
            fmcsa_dot_number=dot_number,
            fmcsa_verified=fmcsa_verified,
            verification_status=verification_status,
            risk_score=min(risk_score, 100.0),
            metadata=data,
        )
