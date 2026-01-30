"""MCP server for UN Comtrade international trade data."""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from .client import ComtradeClient
from .models import CRITICAL_MINERAL_HS_CODES, MINERAL_NAMES

# Initialize MCP server
mcp = FastMCP(
    name="UN Comtrade",
    instructions="""UN Comtrade MCP Server provides access to international trade data
from the United Nations Comtrade database. This server specializes in critical
minerals trade data (lithium, cobalt, rare earths, graphite, nickel, manganese,
gallium, germanium) but can query any HS-coded commodity.

Key capabilities:
- Query bilateral trade flows between countries
- Get import/export data for specific commodities
- Access pre-configured queries for critical minerals
- List available reporters, partners, and commodity codes

Trade flow codes:
- M = Imports
- X = Exports

Country codes use UN M49 standard (e.g., 842 = USA, 156 = China, 0 = World).
Commodity codes use HS (Harmonized System) classification.""",
)


def get_client() -> ComtradeClient:
    """Get ComtradeClient instance."""
    return ComtradeClient()


# =============================================================================
# Overview Tools
# =============================================================================


@mcp.tool()
async def get_api_status() -> dict:
    """
    Check UN Comtrade API connectivity and API key validity.

    Returns status information about the API connection.
    """
    client = get_client()
    return await client.check_status()


@mcp.tool()
async def list_critical_minerals() -> dict:
    """
    List available critical minerals with their HS codes.

    Returns the pre-configured critical minerals and their associated
    HS commodity codes for easy querying.
    """
    minerals = []
    for key, codes in CRITICAL_MINERAL_HS_CODES.items():
        minerals.append(
            {
                "id": key,
                "name": MINERAL_NAMES.get(key, key),
                "hs_codes": codes,
            }
        )
    return {
        "count": len(minerals),
        "minerals": minerals,
        "usage": "Use get_critical_mineral_trade(mineral='lithium', ...) to query",
    }


@mcp.tool()
async def list_reporters(search: Optional[str] = None, limit: int = 50) -> dict:
    """
    List available reporter countries.

    Args:
        search: Optional search term to filter countries
        limit: Maximum number of results to return

    Returns:
        List of reporter countries with their codes
    """
    client = get_client()
    reporters = await client.get_reporters()

    if search:
        search_lower = search.lower()
        reporters = [
            r for r in reporters if search_lower in r.get("text", "").lower()
        ]

    reporters = reporters[:limit]
    return {
        "count": len(reporters),
        "reporters": reporters,
        "note": "Use 'id' field as reporterCode in queries",
    }


@mcp.tool()
async def list_partners(search: Optional[str] = None, limit: int = 50) -> dict:
    """
    List available partner countries/areas.

    Args:
        search: Optional search term to filter
        limit: Maximum number of results to return

    Returns:
        List of partner areas with their codes
    """
    client = get_client()
    partners = await client.get_partners()

    if search:
        search_lower = search.lower()
        partners = [
            p for p in partners if search_lower in p.get("text", "").lower()
        ]

    partners = partners[:limit]
    return {
        "count": len(partners),
        "partners": partners,
        "note": "Use 'id' field as partnerCode in queries. Code 0 = World total.",
    }


@mcp.tool()
async def list_commodities(
    search: Optional[str] = None,
    hs_level: int = 4,
    limit: int = 50,
) -> dict:
    """
    List available HS commodity codes.

    Args:
        search: Optional search term to filter commodities
        hs_level: HS code digit level (2, 4, or 6)
        limit: Maximum number of results to return

    Returns:
        List of commodity codes with descriptions
    """
    client = get_client()
    commodities = await client.get_commodities()

    # Filter by HS level (code length)
    if hs_level in [2, 4, 6]:
        commodities = [
            c for c in commodities
            if len(str(c.get("id", ""))) == hs_level
        ]

    if search:
        search_lower = search.lower()
        commodities = [
            c for c in commodities
            if search_lower in c.get("text", "").lower()
            or search_lower in str(c.get("id", ""))
        ]

    commodities = commodities[:limit]
    return {
        "count": len(commodities),
        "commodities": commodities,
        "note": f"Showing HS-{hs_level} codes. Use 'id' field as cmdCode in queries.",
    }


# =============================================================================
# Data Query Tools
# =============================================================================


@mcp.tool()
async def get_trade_data(
    reporter: str,
    commodity: str,
    partner: str = "0",
    flow: str = "M",
    year: str = "2023",
    max_records: int = 100,
) -> dict:
    """
    Get trade data from UN Comtrade.

    Args:
        reporter: Reporter country code (e.g., "842" for USA, "156" for China)
        commodity: HS commodity code (e.g., "2602" for manganese ores)
        partner: Partner country code or "0" for world total
        flow: Trade flow - "M" (imports), "X" (exports), or "M,X" (both)
        year: Year or comma-separated years (e.g., "2023" or "2020,2021,2022,2023")
        max_records: Maximum records to return (up to 500)

    Returns:
        Trade records with values in USD and quantities
    """
    client = get_client()
    records = await client.get_trade_data(
        reporter=reporter,
        partner=partner,
        commodity=commodity,
        flow=flow,
        period=year,
        max_records=min(max_records, 500),
    )

    return {
        "count": len(records),
        "query": {
            "reporter": reporter,
            "partner": partner,
            "commodity": commodity,
            "flow": flow,
            "year": year,
        },
        "records": [r.model_dump() for r in records],
    }


@mcp.tool()
async def get_critical_mineral_trade(
    mineral: str,
    reporter: str = "0",
    partner: str = "0",
    flow: str = "M,X",
    year: str = "2023",
    max_records: int = 100,
) -> dict:
    """
    Get trade data for a critical mineral using preset HS codes.

    Available minerals: lithium, cobalt, hree, lree, rare_earth, graphite,
    nickel, manganese, gallium, germanium

    Args:
        mineral: Mineral name (e.g., "lithium", "cobalt", "rare_earth")
        reporter: Reporter country code or "0" for all countries
        partner: Partner country code or "0" for world
        flow: Trade flow - "M" (imports), "X" (exports), or "M,X" (both)
        year: Year or comma-separated years
        max_records: Maximum records to return

    Returns:
        Trade records for the specified mineral
    """
    client = get_client()

    try:
        records = await client.get_critical_mineral_trade(
            mineral=mineral,
            reporter=reporter,
            partner=partner,
            flow=flow,
            period=year,
            max_records=min(max_records, 500),
        )
    except ValueError as e:
        return {"error": str(e)}

    mineral_lower = mineral.lower().replace(" ", "_")
    hs_codes = CRITICAL_MINERAL_HS_CODES.get(mineral_lower, [])

    return {
        "count": len(records),
        "mineral": MINERAL_NAMES.get(mineral_lower, mineral),
        "hs_codes_queried": hs_codes,
        "query": {
            "reporter": reporter,
            "partner": partner,
            "flow": flow,
            "year": year,
        },
        "records": [r.model_dump() for r in records],
    }


@mcp.tool()
async def get_commodity_trade_summary(
    commodity: str,
    year: str = "2023",
    flow: str = "M",
    top_n: int = 20,
) -> str:
    """
    Get a global trade summary for a commodity showing top importers/exporters.

    Args:
        commodity: HS commodity code (e.g., "2602" for manganese ores)
        year: Year to query
        flow: Trade flow - "M" (imports) or "X" (exports)
        top_n: Number of top countries to show

    Returns:
        Markdown-formatted summary table
    """
    client = get_client()

    # Query all reporters for this commodity
    records = await client.get_trade_data(
        reporter="all",
        partner="0",  # World
        commodity=commodity,
        flow=flow,
        period=year,
        max_records=500,
    )

    if not records:
        return f"No {flow} data found for commodity {commodity} in {year}"

    # Aggregate by reporter
    country_totals: dict[str, float] = {}
    units = None
    commodity_name = None

    for r in records:
        if r.trade_value:
            country = r.reporter
            country_totals[country] = country_totals.get(country, 0) + r.trade_value
            if commodity_name is None:
                commodity_name = r.commodity

    # Sort and get top N
    sorted_countries = sorted(
        country_totals.items(), key=lambda x: x[1], reverse=True
    )[:top_n]

    total = sum(v for _, v in sorted_countries)
    flow_name = "Imports" if flow == "M" else "Exports"

    # Format as markdown table
    output = f"**{commodity_name or commodity} - Top {flow_name} ({year})**\n\n"
    output += "| Rank | Country | Value (USD) | Share |\n"
    output += "|------|---------|-------------|-------|\n"

    for i, (country, value) in enumerate(sorted_countries, 1):
        share = (value / total * 100) if total > 0 else 0
        output += f"| {i} | {country} | ${value:,.0f} | {share:.1f}% |\n"

    output += f"\n**Total (top {len(sorted_countries)}): ${total:,.0f}**\n"

    return output


@mcp.tool()
async def get_country_trade_profile(
    country: str,
    year: str = "2023",
    commodity_type: str = "critical_minerals",
) -> dict:
    """
    Get a country's import/export profile for critical minerals.

    Args:
        country: Country code (e.g., "842" for USA)
        year: Year to query
        commodity_type: "critical_minerals" for CMM focus or "all" for general

    Returns:
        Summary of country's trade in critical minerals
    """
    client = get_client()
    profile = {
        "country_code": country,
        "year": year,
        "imports": {},
        "exports": {},
    }

    if commodity_type == "critical_minerals":
        for mineral, hs_codes in CRITICAL_MINERAL_HS_CODES.items():
            commodity = ",".join(hs_codes)

            # Get imports
            imports = await client.get_trade_data(
                reporter=country,
                partner="0",
                commodity=commodity,
                flow="M",
                period=year,
                max_records=100,
            )
            import_total = sum(r.trade_value or 0 for r in imports)

            # Get exports
            exports = await client.get_trade_data(
                reporter=country,
                partner="0",
                commodity=commodity,
                flow="X",
                period=year,
                max_records=100,
            )
            export_total = sum(r.trade_value or 0 for r in exports)

            mineral_name = MINERAL_NAMES.get(mineral, mineral)
            if import_total > 0:
                profile["imports"][mineral_name] = import_total
            if export_total > 0:
                profile["exports"][mineral_name] = export_total

    profile["total_imports"] = sum(profile["imports"].values())
    profile["total_exports"] = sum(profile["exports"].values())
    profile["trade_balance"] = profile["total_exports"] - profile["total_imports"]

    return profile


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
