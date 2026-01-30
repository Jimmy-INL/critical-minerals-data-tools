"""Pydantic models for UN Comtrade API data structures."""

from pydantic import BaseModel, Field
from typing import Optional


class TradeRecord(BaseModel):
    """A single trade record from UN Comtrade."""

    period: int = Field(description="Year of the trade record")
    reporter_code: int = Field(alias="reporterCode", description="Reporter country code")
    reporter: str = Field(alias="reporterDesc", description="Reporter country name")
    partner_code: int = Field(alias="partnerCode", description="Partner country code")
    partner: str = Field(alias="partnerDesc", description="Partner country name")
    flow_code: str = Field(alias="flowCode", description="Trade flow code (M/X)")
    flow: str = Field(alias="flowDesc", description="Trade flow description")
    commodity_code: str = Field(alias="cmdCode", description="HS commodity code")
    commodity: str = Field(alias="cmdDesc", description="Commodity description")
    trade_value: Optional[float] = Field(
        alias="primaryValue", default=None, description="Trade value in USD"
    )
    net_weight: Optional[float] = Field(
        alias="netWgt", default=None, description="Net weight in kg"
    )
    quantity: Optional[float] = Field(
        alias="qty", default=None, description="Quantity in reported units"
    )
    quantity_unit: Optional[str] = Field(
        alias="qtyUnitAbbr", default=None, description="Quantity unit abbreviation"
    )

    class Config:
        populate_by_name = True


class CountryReference(BaseModel):
    """Country reference data."""

    id: int = Field(description="Country code")
    text: str = Field(description="Country name")
    iso3: Optional[str] = Field(default=None, description="ISO 3-letter code")


class CommodityReference(BaseModel):
    """HS commodity code reference data."""

    id: str = Field(description="HS code")
    text: str = Field(description="Commodity description")
    parent: Optional[str] = Field(default=None, description="Parent HS code")


# Critical Minerals HS Code Mapping (CMM Focus)
CRITICAL_MINERAL_HS_CODES: dict[str, list[str]] = {
    "lithium": ["282520", "283691", "850650"],  # Lithium oxide/hydroxide, carbonate, batteries
    "cobalt": ["2605", "810520", "810590"],  # Cobalt ores, unwrought, articles
    "hree": ["284690"],  # Heavy REE compounds (Dy, Tb, etc.)
    "lree": ["284610"],  # Light REE compounds (Nd, Pr, etc.)
    "rare_earth": ["2846"],  # All REE compounds
    "graphite": ["250410", "250490"],  # Natural graphite (amorphous, crystalline)
    "nickel": ["2604", "750210", "750220"],  # Nickel ores, unwrought, alloys
    "manganese": ["2602", "811100"],  # Manganese ores, unwrought
    "gallium": ["811292"],  # Gallium unwrought
    "germanium": ["811299"],  # Germanium (other base metals)
}

# Friendly names for display
MINERAL_NAMES: dict[str, str] = {
    "lithium": "Lithium (Li)",
    "cobalt": "Cobalt (Co)",
    "hree": "Heavy Rare Earth Elements",
    "lree": "Light Rare Earth Elements",
    "rare_earth": "Rare Earth Elements (all)",
    "graphite": "Graphite (Gr)",
    "nickel": "Nickel (Ni)",
    "manganese": "Manganese (Mn)",
    "gallium": "Gallium (Ga)",
    "germanium": "Germanium (Ge)",
}
