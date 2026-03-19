"""REST API for USGS Mineral Commodity Summaries (MCS)."""

from __future__ import annotations

from typing import Any
import os

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

from .mrds_client import MRDSClient
from .osm_client import search_osm_mines
from .usgs_client import USGSMCSClient

def _get_llm_config() -> dict[str, str]:
    provider = (os.environ.get("LLM_PROVIDER") or "openai").lower()
    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            "base_url": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
            "api_key": os.environ.get("ANTHROPIC_API_KEY") or "",
        }
    model = os.environ.get("OPENAI_MODEL", "gpt-oss-120b")
    if model == "gpt-oss-120b":
        api_key = os.environ.get("OPENAI_API_KEY_OSS") or ""
    elif model == "gpt-5.2-codex":
        api_key = os.environ.get("OPENAI_API_KEY") or ""
    else:
        api_key = os.environ.get("OPENAI_API_KEY") or ""
    return {
        "provider": "openai",
        "model": model,
        "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "api_key": api_key,
    }


def _qa_system_prompt() -> str:
    return (
        "You are a data analyst. Answer using only the provided context. "
        "If the answer is not in the context, say so and suggest what data is missing. "
        "Format: concise markdown with a short title line and bullet points. "
        "Do NOT use tables or ASCII art. Prefer numeric values with units. "
        "Each bullet must be on its own line (newline separated). "
        "End with a one-sentence Insight line."
    )


async def _call_llm(question: str, context: dict[str, Any] | None) -> tuple[str, str, str]:
    cfg = _get_llm_config()
    if not cfg["api_key"]:
        raise HTTPException(status_code=400, detail="Missing API key for LLM provider")

    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": _qa_system_prompt()},
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context or {}}"},
        ],
        "temperature": 0.2,
    }

    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"LLM error: {resp.text}")
        data = resp.json()

    answer = data["choices"][0]["message"]["content"]
    return answer, cfg["model"], cfg["provider"]

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

load_dotenv(find_dotenv(), override=True)


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


class QARequest(BaseModel):
    question: str
    context: dict[str, Any] | None = None


class QAResponse(BaseModel):
    answer: str
    model: str
    provider: str


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


@app.post("/qa", response_model=QAResponse, tags=["LLM"])
async def ask_question(payload: QARequest):
    """
    Ask an LLM question grounded in the provided context.
    """
    answer, model, provider = await _call_llm(payload.question, payload.context)
    return QAResponse(answer=answer, model=model, provider=provider)


def main() -> None:
    uvicorn.run("usgs_mcp.api:app", host="0.0.0.0", port=8011, reload=False)


if __name__ == "__main__":
    main()
