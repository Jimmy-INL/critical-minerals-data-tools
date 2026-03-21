from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from usgs_mcp.mrds_client import MRDSClient
from usgs_mcp.osm_client import search_osm_mines
from usgs_mcp.usgs_client import USGSMCSClient


app = FastAPI(
    title="USGS Mineral Commodity Summaries API",
    version="0.1.0",
    description="REST API for USGS MCS data (local or ScienceBase-backed).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8085", "http://127.0.0.1:8085"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_mcs_client: USGSMCSClient | None = None
_mrds_client: MRDSClient | None = None


def _get_mcs_client() -> USGSMCSClient:
    global _mcs_client
    if _mcs_client is None:
        _mcs_client = USGSMCSClient()
    return _mcs_client


def _get_mrds_client() -> MRDSClient:
    global _mrds_client
    if _mrds_client is None:
        _mrds_client = MRDSClient()
    return _mrds_client


@app.get("/config")
def get_config() -> dict[str, Any]:
    return {
        "llm_model": os.environ.get("OPENAI_MODEL", ""),
        "cache_dir": os.environ.get("USGS_CACHE_DIR", ""),
        "data_source": "local" if os.environ.get("USGS_MCS_LOCAL_CSV") else "sciencebase",
    }


@app.get("/commodities")
def list_commodities() -> dict[str, Any]:
    client = _get_mcs_client()
    try:
        commodities = client.list_commodities()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"total": len(commodities), "commodities": commodities}


@app.get("/countries/{country}/profile")
def get_country_profile(
    country: str,
    year: int | None = Query(None, description="Year (defaults to most recent)"),
    statistic_type: str = Query("Production", description="Production, Imports, or Exports"),
    limit: int = Query(20, ge=1, le=50),
) -> dict[str, Any]:
    client = _get_mcs_client()
    try:
        return client.get_country_profile(country=country, year=year, statistic_type=statistic_type, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/production/ranking")
def get_commodity_ranking(
    commodity: str = Query(..., description="Commodity name"),
    year: int | None = Query(None, description="Year (defaults to most recent)"),
    statistic_type: str = Query("Production", description="Production, Imports, or Exports"),
    top_n: int = Query(15, ge=1, le=50, description="Number of top countries"),
) -> dict[str, Any]:
    client = _get_mcs_client()
    try:
        result = client.get_country_ranking(
            commodity=commodity,
            year=year,
            statistic_type=statistic_type,
            top_n=top_n,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Always return a valid payload to keep the UI stable.
    if not result.get("rankings"):
        return {
            "commodity": commodity,
            "year": result.get("year"),
            "statistic_type": statistic_type,
            "units": result.get("units"),
            "total_quantity": 0.0,
            "rankings": [],
        }

    return result


@app.get("/production/timeseries")
def get_time_series(
    commodity: str = Query(..., description="Commodity name"),
    country: str | None = Query(None, description="Country name (omit for global)"),
    statistic_type: str = Query("Production", description="Production, Imports, or Exports"),
) -> dict[str, Any]:
    client = _get_mcs_client()
    try:
        return client.get_time_series(commodity=commodity, country=country, statistic_type=statistic_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/mines/search")
def search_mines(
    country: str = Query(..., description="Country name"),
    commodity: str | None = Query(None, description="Commodity name"),
    source: str = Query("both", description="mrds, osm, or both"),
    limit: int = Query(200, ge=1, le=500),
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    if source in ("mrds", "both"):
        client = _get_mrds_client()
        try:
            results.extend(client.search(commodity=commodity, country=country, limit=limit))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    if source in ("osm", "both") and len(results) < limit:
        try:
            results.extend(search_osm_mines(country=country, commodity=commodity, limit=limit - len(results)))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return results[:limit]


@app.get("/uranium/deposits")
def get_uranium_deposits(
    country: str | None = Query(None, description="Country name"),
    limit: int = Query(200, ge=1, le=1000),
) -> list[dict[str, Any]]:
    client = _get_mrds_client()
    try:
        return client.search(commodity="uranium", country=country, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def main() -> None:
    port = int(os.environ.get("USGS_PORT", "8011"))
    uvicorn.run("usgs_mcp.api:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
