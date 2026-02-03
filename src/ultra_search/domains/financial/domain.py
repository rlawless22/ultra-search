"""Financial domain tools - STUB.

This is a template showing how to add a new domain.
Implement the tools and providers to enable this domain.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from ultra_search.core.base import BaseTool
from ultra_search.core.registry import register_tool


class StockQuoteInput(BaseModel):
    """Input for stock quote lookup."""

    symbol: str = Field(..., description="Stock ticker symbol (e.g., AAPL, GOOGL)")


class StockQuoteOutput(BaseModel):
    """Output from stock quote lookup."""

    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int | None
    provider: str


# UNCOMMENT AND IMPLEMENT TO ENABLE:
# @register_tool(domain="financial")
class GetStockQuote(BaseTool[StockQuoteInput, StockQuoteOutput]):
    """Get current stock quote for a ticker symbol.

    TODO: Implement with a provider (Polygon, Alpha Vantage, etc.)
    """

    name: ClassVar[str] = "get_stock_quote"
    description: ClassVar[str] = (
        "Get current stock price and trading data for a ticker symbol."
    )
    domain: ClassVar[str] = "financial"
    input_model: ClassVar[type[BaseModel]] = StockQuoteInput
    output_model: ClassVar[type[BaseModel]] = StockQuoteOutput

    async def execute(self, input_data: StockQuoteInput) -> StockQuoteOutput:
        raise NotImplementedError(
            "Financial domain not yet implemented. "
            "Add a provider and uncomment @register_tool decorator."
        )


# Example providers to implement:
# - Polygon.io: https://polygon.io/docs/stocks
# - Alpha Vantage: https://www.alphavantage.co/documentation/
# - IEX Cloud: https://iexcloud.io/docs/api/
# - Yahoo Finance: yfinance library (unofficial)
