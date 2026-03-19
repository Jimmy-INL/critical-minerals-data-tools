"""USGS MCS MCP Server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .usgs_client import USGSMCSClient

mcp = FastMCP(
    name="USGS Mineral Commodity Summaries",
    instructions=(
        "Access USGS Mineral Commodity Summaries (MCS) data releases for commodity rankings, "
        "time series, and country profiles."
    ),
)


def get_client() -> USGSMCSClient:
    return USGSMCSClient()


@mcp.tool()
async def list_commodities() -> str:
    """List all mineral commodities available in the USGS MCS data release."""
    client = get_client()
    commodities = client.list_commodities()
    output = f"Total: {len(commodities)} commodities\n\n"
    output += "\n".join(f"- {c}" for c in commodities)
    return output


@mcp.tool()
async def list_countries() -> str:
    """List all countries with data in the USGS MCS release."""
    client = get_client()
    countries = client.list_countries()
    output = f"Total: {len(countries)} countries\n\n"
    output += "\n".join(f"- {c}" for c in countries)
    return output


@mcp.tool()
async def get_commodity_ranking(
    commodity: str,
    year: int | None = None,
    statistic_type: str = "Production",
    top_n: int = 10,
) -> str:
    """Get top producing countries for a commodity."""
    client = get_client()
    result = client.get_country_ranking(
        commodity=commodity,
        year=year,
        statistic_type=statistic_type,
        top_n=top_n,
    )

    lines = [
        f"Commodity: {result['commodity']}",
        f"Year: {result['year']}",
        f"Statistic: {result['statistic_type']}",
        f"Total: {result['total_quantity']:.2f} {result['units'] or ''}".strip(),
        "",
    ]

    for row in result["rankings"]:
        lines.append(
            f"{row['rank']}. {row['country']} — {row['quantity']:.2f} "
            f"({row['share_percent']:.2f}%)"
        )

    return "\n".join(lines)


@mcp.tool()
async def get_time_series(
    commodity: str,
    country: str | None = None,
    statistic_type: str = "Production",
) -> str:
    """Get a time series for a commodity (optionally filtered by country)."""
    client = get_client()
    result = client.get_time_series(
        commodity=commodity,
        country=country,
        statistic_type=statistic_type,
    )

    header = f"Commodity: {result['commodity']}"
    if result["country"]:
        header += f" | Country: {result['country']}"
    header += f" | Statistic: {result['statistic_type']}"

    lines = [header, f"Units: {result['units'] or 'n/a'}", ""]
    for point in result["series"]:
        lines.append(f"{point['year']}: {point['quantity']:.2f}")

    return "\n".join(lines)


@mcp.tool()
async def get_country_profile(
    country: str,
    year: int | None = None,
    statistic_type: str = "Production",
    limit: int = 20,
) -> str:
    """Get a commodity profile for a country in a given year."""
    client = get_client()
    result = client.get_country_profile(
        country=country,
        year=year,
        statistic_type=statistic_type,
        limit=limit,
    )

    lines = [
        f"Country: {result['country']}",
        f"Year: {result['year']}",
        f"Statistic: {result['statistic_type']}",
        "",
    ]
    for row in result["commodities"]:
        qty = f"{row['quantity']:.2f}"
        unit = row["units"] or ""
        lines.append(f"- {row['commodity']}: {qty} {unit}".strip())

    return "\n".join(lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
