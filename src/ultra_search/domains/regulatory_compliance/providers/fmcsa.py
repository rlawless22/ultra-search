"""FMCSA QCMobile API provider for carrier authority and safety data.

Official API documentation: https://mobile.fmcsa.dot.gov/developer/home.page
Registration: https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx

The FMCSA provides free API access to motor carrier data including:
- Operating authority and status
- Safety ratings and inspections
- Out-of-service percentages
- Insurance status
- Cargo classifications
"""

from __future__ import annotations

from typing import Any

import httpx

from ultra_search.core.base import BaseProvider
from ultra_search.domains.regulatory_compliance.domain import FMCSAAuthorityInfo


class FMCSAProvider(BaseProvider):
    """FMCSA QCMobile API provider.

    Provides access to official DOT carrier data via the FMCSA web services.

    API Key: Free, register at https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx
    Base URL: https://mobile.fmcsa.dot.gov/qc/services/carriers

    Key endpoints:
    - /docket-number/{docket} - Lookup by docket number
    - /name/{name} - Search by carrier name
    - /safety-data/{dot} - Safety ratings and data
    """

    provider_name = "fmcsa"
    base_url = "https://mobile.fmcsa.dot.gov/qc/services/carriers"
    requires_auth = True

    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with API key authentication."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "FMCSA API requires an API key. Register at: "
                    "https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx "
                    "Then set: ULTRA_FMCSA_API_KEY"
                )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
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
        """Make authenticated request to FMCSA API."""
        client = await self.get_client()
        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def lookup_by_dot(self, dot_number: str) -> FMCSAAuthorityInfo | None:
        """Lookup carrier by DOT number.

        Args:
            dot_number: USDOT number

        Returns:
            Carrier information or None if not found
        """
        try:
            # FMCSA API endpoint (adjust based on actual API docs)
            data = await self._make_request("GET", f"/{dot_number}")
            return self._parse_carrier_data(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def lookup_by_mc(self, mc_number: str) -> FMCSAAuthorityInfo | None:
        """Lookup carrier by MC/MX/FF number.

        Args:
            mc_number: MC, MX, or FF number

        Returns:
            Carrier information or None if not found
        """
        try:
            data = await self._make_request("GET", f"/docket-number/{mc_number}")
            return self._parse_carrier_data(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def lookup_by_name(self, legal_name: str) -> FMCSAAuthorityInfo | None:
        """Search carrier by legal name.

        Args:
            legal_name: Legal business name

        Returns:
            First matching carrier or None if not found
        """
        try:
            data = await self._make_request(
                "GET",
                "/name",
                params={"name": legal_name}
            )

            # API may return array of matches, take first
            if isinstance(data, list) and len(data) > 0:
                return self._parse_carrier_data(data[0])
            elif isinstance(data, dict):
                return self._parse_carrier_data(data)
            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def _parse_carrier_data(self, data: dict[str, Any]) -> FMCSAAuthorityInfo:
        """Parse FMCSA API response into structured model.

        Note: Field names based on FMCSA API schema. Adjust as needed when
        testing with real API responses.
        """
        return FMCSAAuthorityInfo(
            dot_number=str(data.get("dotNumber", data.get("usdotNumber", ""))),
            legal_name=data.get("legalName", ""),
            dba_name=data.get("dbaName"),
            physical_address=self._format_address(data.get("phyStreet"), data.get("phyCity"),
                                                  data.get("phyState"), data.get("phyZipcode")),
            phone=data.get("telephone"),
            email=data.get("emailAddress"),
            operating_status=data.get("carrierOperation"),
            out_of_service_date=data.get("oosDate"),
            authority_status=data.get("commonAuthorityStatus"),
            safety_rating=data.get("safetyRating"),
            safety_rating_date=data.get("safetyRatingDate"),
            unsafe_driving_pct=data.get("unsafeDrivingPct"),
            hours_of_service_pct=data.get("hoursOfServicePct"),
            vehicle_maintenance_pct=data.get("vehicleMaintenancePct"),
            controlled_substances_pct=data.get("controlledSubstancesPct"),
            crash_indicator=data.get("crashIndicator"),
            insurance_on_file=data.get("bipInsuranceOnFile") == "Y",
            insurance_required=data.get("bipInsuranceRequired"),
            cargo_carried=data.get("cargoCarried", []),
            operation_classification=data.get("operationClassification", []),
            carrier_type=data.get("entityType"),
            docket_numbers=data.get("docketNumbers", []),
            mc_number=data.get("mcNumber"),
            metadata=data,
        )

    def _format_address(
        self,
        street: str | None,
        city: str | None,
        state: str | None,
        zipcode: str | None,
    ) -> str | None:
        """Format address components into single string."""
        parts = [p for p in [street, city, state, zipcode] if p]
        return ", ".join(parts) if parts else None


@register_tool(domain="regulatory_compliance")
class VerifyBusinessKYB(BaseTool[VerifyBusinessInput, VerifyBusinessOutput]):
    """Verify business legitimacy via KYB (Know Your Business) checks.

    Uses business verification APIs (Middesk, D&B, etc.) to:
    - Verify entity exists and is active
    - Check for liens, bankruptcies, litigation
    - Screen against watchlists
    - Verify FMCSA registration (for carriers)
    - Assess overall business risk

    Returns detailed verification results and risk signals.
    """

    name: ClassVar[str] = "verify_business_kyb"
    description: ClassVar[str] = (
        "Verify business legitimacy via KYB (Know Your Business). "
        "Checks for entity validity, liens, bankruptcies, litigation, watchlists. "
        "Includes FMCSA verification for carriers. "
        "Returns detailed risk assessment."
    )
    domain: ClassVar[str] = "regulatory_compliance"
    input_model: ClassVar[type[BaseModel]] = VerifyBusinessInput
    output_model: ClassVar[type[BaseModel]] = VerifyBusinessOutput

    async def execute(self, input_data: VerifyBusinessInput) -> VerifyBusinessOutput:
        """Execute business verification."""
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.regulatory_compliance.providers import get_regulatory_provider

        # Get Middesk provider
        provider = get_regulatory_provider("middesk", self.settings)

        verification_info = await provider.verify_business(
            business_name=input_data.business_name,
            address=input_data.address,
            tax_id=input_data.tax_id,
            dot_number=input_data.dot_number,
        )

        output = VerifyBusinessOutput(
            verification_info=verification_info,
            provider=provider.provider_name,
            output_file_path=None,
        )

        # Write to file if requested
        if input_data.output_file:
            if input_data.output_format:
                format_str = input_data.output_format.lower()
            else:
                ext = Path(input_data.output_file).suffix.lstrip(".")
                format_str = ext if ext in ["json", "md", "txt", "html"] else "json"

            try:
                output_format = OutputFormat(format_str)
            except ValueError:
                output_format = OutputFormat.JSON

            config = FileOutputConfig(
                path=input_data.output_file,
                format=output_format,
                append=False,
                add_timestamp=True,
                create_dirs=True,
            )

            written_path = await write_result_to_file(output, config)
            output.output_file_path = str(written_path)

        return output
