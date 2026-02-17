"""REST API for USGS Mineral Commodity Summaries (MCS)."""

from __future__ import annotations

from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .mrds_client import MRDSClient
from .osm_client import search_osm_mines
from .usgs_client import USGSMCSClient

app = FastAPI(
    title="USGS Mineral Commodity Summaries API",
    description=(
        "REST API for USGS Mineral Commodity Summaries (MCS) data releases. "
        "Provides commodity rankings, time series, and country profiles."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client() -> USGSMCSClient:
    return USGSMCSClient()


class CommodityList(BaseModel):
    total: int
    commodities: list[str]


class CountryList(BaseModel):
    total: int
    countries: list[str]


class RankedCountry(BaseModel):
    rank: int
    country: str
    quantity: float
    share_percent: float


class RankingResponse(BaseModel):
    commodity: str
    year: int
    statistic_type: str
    units: str | None
    total_quantity: float
    rankings: list[RankedCountry]


class TimeSeriesPoint(BaseModel):
    year: int
    quantity: float


class TimeSeriesResponse(BaseModel):
    commodity: str
    country: str | None
    statistic_type: str
    units: str | None
    series: list[TimeSeriesPoint]


class CountryCommodity(BaseModel):
    commodity: str
    quantity: float
    units: str | None


class CountryProfile(BaseModel):
    country: str
    year: int
    statistic_type: str
    commodities: list[CountryCommodity]


class MinePoint(BaseModel):
    name: str
    lat: float
    lng: float
    country: str | None
    commodities: list[str]
    source: str


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": "USGS Mineral Commodity Summaries API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "openai_functions": "/openai/functions",
        "endpoints": {
            "commodities": "/commodities",
            "countries": "/countries",
            "ranking": "/production/ranking",
            "time_series": "/production/timeseries",
            "country_profile": "/countries/{country}/profile",
        },
    }


@app.get("/commodities", response_model=CommodityList, tags=["Commodities"])
async def list_commodities():
    client = get_client()
    commodities = client.list_commodities()
    return CommodityList(total=len(commodities), commodities=commodities)


@app.get("/countries", response_model=CountryList, tags=["Countries"])
async def list_countries():
    client = get_client()
    countries = client.list_countries()
    return CountryList(total=len(countries), countries=countries)


@app.get("/production/ranking", response_model=RankingResponse, tags=["Production"])
async def get_commodity_ranking(
    commodity: str = Query(..., description="Commodity name"),
    year: int | None = Query(None, description="Year (defaults to most recent)"),
    statistic_type: str = Query("Production", description="Statistic type"),
    top_n: int = Query(10, description="Number of top countries to return"),
):
    client = get_client()
    try:
        return client.get_country_ranking(
            commodity=commodity,
            year=year,
            statistic_type=statistic_type,
            top_n=top_n,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/production/timeseries", response_model=TimeSeriesResponse, tags=["Production"])
async def get_time_series(
    commodity: str = Query(..., description="Commodity name"),
    country: str | None = Query(None, description="Country name (optional)"),
    statistic_type: str = Query("Production", description="Statistic type"),
):
    client = get_client()
    try:
        return client.get_time_series(commodity=commodity, country=country, statistic_type=statistic_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/countries/{country}/profile", response_model=CountryProfile, tags=["Countries"])
async def get_country_profile(
    country: str,
    year: int | None = Query(None, description="Year (defaults to most recent)"),
    statistic_type: str = Query("Production", description="Statistic type"),
    limit: int = Query(20, description="Max commodities to return"),
):
    client = get_client()
    try:
        return client.get_country_profile(country=country, year=year, statistic_type=statistic_type, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/mines/search", response_model=list[MinePoint], tags=["Mines"])
async def search_mines(
    commodity: str | None = Query(None, description="Commodity name"),
    country: str | None = Query(None, description="Country name (optional)"),
    limit: int = Query(200, description="Max points to return"),
    source: str = Query("mrds", description="mrds, osm, or both"),
):
    results: list[dict[str, Any]] = []
    normalized_commodity = None
    if commodity:
        normalized_commodity = commodity.split(",")[0].strip()

    if source in {"mrds", "both"}:
        try:
            results.extend(
                MRDSClient().search(
                    commodity=normalized_commodity, country=country, limit=limit
                )
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if source in {"osm", "both"} and country:
        try:
            results.extend(
                search_osm_mines(country=country, commodity=normalized_commodity, limit=limit)
            )
        except httpx.HTTPError:
            # Overpass can be slow/unavailable; proceed with MRDS-only results.
            if source == "osm":
                raise HTTPException(
                    status_code=502,
                    detail="Overpass API unavailable (timeout). Try again or use source=mrds.",
                )

    # Fallback: if filtering was too strict, retry without commodity
    if not results and normalized_commodity:
        if source in {"mrds", "both"}:
            results.extend(MRDSClient().search(commodity=None, country=country, limit=limit))
        if source in {"osm", "both"} and country:
            try:
                results.extend(search_osm_mines(country=country, commodity=None, limit=limit))
            except httpx.HTTPError:
                if source == "osm":
                    raise HTTPException(
                        status_code=502,
                        detail="Overpass API unavailable (timeout). Try again or use source=mrds.",
                    )

    return results[:limit]


# OpenAI-compatible function definitions
class OpenAIFunction(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


@app.get("/openai/functions", response_model=list[OpenAIFunction], tags=["LLM Integration"])
async def get_openai_functions():
    return [
        OpenAIFunction(
            name="get_usgs_top_producers",
            description="Get top producing countries for a USGS MCS commodity",
            parameters={
                "type": "object",
                "properties": {
                    "commodity": {"type": "string"},
                    "year": {"type": "integer"},
                    "statistic_type": {"type": "string"},
                    "top_n": {"type": "integer"},
                },
                "required": ["commodity"],
            },
        ),
        OpenAIFunction(
            name="get_usgs_time_series",
            description="Get time series for a USGS MCS commodity",
            parameters={
                "type": "object",
                "properties": {
                    "commodity": {"type": "string"},
                    "country": {"type": "string"},
                    "statistic_type": {"type": "string"},
                },
                "required": ["commodity"],
            },
        ),
        OpenAIFunction(
            name="get_usgs_country_profile",
            description="Get commodity profile for a country in USGS MCS data",
            parameters={
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "year": {"type": "integer"},
                    "statistic_type": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["country"],
            },
        ),
    ]


def main() -> None:
    uvicorn.run("usgs_mcp.api:app", host="0.0.0.0", port=8011, reload=False)


if __name__ == "__main__":
    main()
