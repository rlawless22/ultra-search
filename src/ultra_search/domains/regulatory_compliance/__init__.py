"""Regulatory Compliance domain - Business verification and carrier authority.

Providers:
- fmcsa: FMCSA QCMobile API (DOT numbers, safety ratings, authority)
- middesk: Middesk KYB API (business verification, liens, watchlists)

Tools:
- check_fmcsa_authority: Lookup carrier by DOT number
- verify_business: Verify business legitimacy via KYB
"""

from ultra_search.domains.regulatory_compliance import domain  # noqa: F401

__all__ = []
