"""Regulatory Compliance domain tools for carrier and business verification."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.registry import register_tool


# === DATA MODELS ===


class FMCSAAuthorityInfo(BaseModel):
    """FMCSA carrier authority information."""

    dot_number: str
    legal_name: str
    dba_name: str | None = None
    physical_address: str | None = None
    phone: str | None = None
    email: str | None = None

    # Authority status
    operating_status: str | None = None
    out_of_service_date: str | None = None
    authority_status: str | None = None

    # Safety ratings
    safety_rating: str | None = None
    safety_rating_date: str | None = None
    unsafe_driving_pct: float | None = None
    hours_of_service_pct: float | None = None
    vehicle_maintenance_pct: float | None = None
    controlled_substances_pct: float | None = None
    crash_indicator: str | None = None

    # Insurance
    insurance_on_file: bool | None = None
    insurance_required: str | None = None

    # Operations
    cargo_carried: list[str] = Field(default_factory=list)
    operation_classification: list[str] = Field(default_factory=list)
    carrier_type: str | None = None

    # Additional
    docket_numbers: list[str] = Field(default_factory=list)
    mc_number: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class BusinessVerificationInfo(BaseModel):
    """Business verification/KYB information."""

    business_name: str
    legal_entity_type: str | None = None
    tax_id_verified: bool | None = None
    business_address: str | None = None
    formation_date: str | None = None
    state_of_incorporation: str | None = None

    # Risk signals
    has_liens: bool | None = None
    has_bankruptcies: bool | None = None
    has_litigation: bool | None = None
    watchlist_hits: list[str] = Field(default_factory=list)

    # FMCSA integration (Middesk includes this)
    fmcsa_dot_number: str | None = None
    fmcsa_verified: bool | None = None

    # Verification status
    verification_status: str | None = None
    risk_score: float | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


# === INPUT/OUTPUT MODELS ===


class CheckFMCSAInput(BaseModel):
    """Input for FMCSA authority check."""

    dot_number: str | None = Field(None, description="DOT number")
    legal_name: str | None = Field(None, description="Legal business name")
    mc_number: str | None = Field(None, description="MC/MX/FF number")

    output_file: str | None = Field(
        None,
        description="Optional file path to save results"
    )
    output_format: str | None = Field(None, description="json|md|txt|html")


class CheckFMCSAOutput(BaseModel):
    """Output from FMCSA authority check."""

    carrier_info: FMCSAAuthorityInfo | None = None
    found: bool
    query_type: str
    provider: str
    output_file_path: str | None = None


class VerifyBusinessInput(BaseModel):
    """Input for business verification."""

    business_name: str = Field(..., description="Business legal name")
    address: str | None = Field(None, description="Business address")
    tax_id: str | None = Field(None, description="EIN/Tax ID")
    dot_number: str | None = Field(None, description="DOT number if carrier")

    output_file: str | None = Field(None, description="Optional file path")
    output_format: str | None = Field(None, description="json|md|txt|html")


class VerifyBusinessOutput(BaseModel):
    """Output from business verification."""

    verification_info: BusinessVerificationInfo
    provider: str
    output_file_path: str | None = None


# === TOOLS ===


@register_tool(domain="regulatory_compliance")
class CheckFMCSAAuthority(BaseTool[CheckFMCSAInput, CheckFMCSAOutput]):
    """Check FMCSA carrier authority and safety information.

    Looks up motor carriers by DOT number, MC number, or legal name.
    Returns operating authority, safety ratings, out-of-service data,
    insurance status, and cargo classifications.

    Critical for vetting moving companies and freight carriers.
    """

    name: ClassVar[str] = "check_fmcsa_authority"
    description: ClassVar[str] = (
        "Check FMCSA carrier authority, safety ratings, and operating status. "
        "Lookup by DOT number, MC number, or legal name. "
        "Returns safety data, out-of-service status, insurance, and cargo types. "
        "Essential for vetting moving companies and carriers."
    )
    domain: ClassVar[str] = "regulatory_compliance"
    input_model: ClassVar[type[BaseModel]] = CheckFMCSAInput
    output_model: ClassVar[type[BaseModel]] = CheckFMCSAOutput

    async def execute(self, input_data: CheckFMCSAInput) -> CheckFMCSAOutput:
        """Execute FMCSA authority check."""
        from pathlib import Path
        from ultra_search.core.file_output import (
            FileOutputConfig,
            OutputFormat,
            write_result_to_file,
        )
        from ultra_search.domains.regulatory_compliance.providers import get_regulatory_provider

        # Get provider
        provider = get_regulatory_provider("fmcsa", self.settings)

        # Determine query type
        if input_data.dot_number:
            query_type = "dot_number"
            carrier_info = await provider.lookup_by_dot(input_data.dot_number)
        elif input_data.mc_number:
            query_type = "mc_number"
            carrier_info = await provider.lookup_by_mc(input_data.mc_number)
        elif input_data.legal_name:
            query_type = "legal_name"
            carrier_info = await provider.lookup_by_name(input_data.legal_name)
        else:
            raise ValueError("Must provide dot_number, mc_number, or legal_name")

        output = CheckFMCSAOutput(
            carrier_info=carrier_info,
            found=carrier_info is not None,
            query_type=query_type,
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


@register_tool(domain="regulatory_compliance")
class VerifyBusiness(BaseTool[VerifyBusinessInput, VerifyBusinessOutput]):
    """Verify business legitimacy via KYB (Know Your Business) checks.

    Checks for:
    - Valid business entity
    - Liens, bankruptcies, litigation
    - Watchlist screening
    - FMCSA registration (for carriers)
    - Principal ownership

    Returns risk score and verification status.
    """

    name: ClassVar[str] = "verify_business"
    description: ClassVar[str] = (
        "Verify business legitimacy via KYB checks. "
        "Checks for valid entity, liens, bankruptcies, litigation, watchlists. "
        "Includes FMCSA verification for carriers. "
        "Returns risk score and verification status."
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

        # Get provider (Middesk)
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
