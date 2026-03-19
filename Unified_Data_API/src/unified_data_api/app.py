from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


def _repo_root() -> Path:
    # app.py -> unified_data_api -> src -> Unified_Data_API -> repo root
    return Path(__file__).resolve().parents[3]


def _registry_path() -> Path:
    return _repo_root() / "Unified_Data_API" / "registry.json"


def _data_path(rel: str) -> Path:
    root = _repo_root()
    return (root / rel).resolve()


def _load_registry() -> dict[str, Any]:
    path = _registry_path()
    if not path.exists():
        return {"datasets": []}
    return json.loads(path.read_text())


def _canonical_response(source: str, dataset: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": source,
        "dataset": dataset,
        "count": len(records),
        "records": records,
    }


def _normalize_str(value: Any) -> str:
    return str(value or "").strip()


def _normalize_lower(value: Any) -> str:
    return _normalize_str(value).lower()


_COMMODITY_SYNONYMS = {
    "rare earth elements": "rare earths",
    "rare earth": "rare earths",
    "ree": "rare earths",
    "uranium, mine": "uranium",
    "cobalt mine": "cobalt",
    "nickel mine": "nickel",
    "copper mine": "copper",
}


def _normalize_commodity(value: Any) -> str:
    raw = _normalize_lower(value)
    if raw in _COMMODITY_SYNONYMS:
        return _COMMODITY_SYNONYMS[raw]
    return raw


def _normalize_units(value: Any) -> str:
    raw = _normalize_lower(value)
    if not raw:
        return ""
    if "tonne" in raw or "ton" in raw:
        return "tonnes"
    if "kg" in raw:
        return "kg"
    if raw == "t":
        return "tonnes"
    return raw


def _find_lat_lon(header: list[str]) -> tuple[str | None, str | None]:
    lat = None
    lon = None
    for col in header:
        lower = col.lower()
        if lat is None and "lat" in lower:
            lat = col
        if lon is None and ("lon" in lower or "long" in lower):
            lon = col
    return lat, lon


def _commodity_columns(header: list[str]) -> list[str]:
    keys = ["commod", "mineral", "ore", "element", "primary", "secondary", "deposit"]
    cols = []
    for col in header:
        lower = col.lower()
        if any(k in lower for k in keys):
            cols.append(col)
    return cols


def _parse_float(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def _in_bbox(lat: float, lon: float, bbox: list[float] | None) -> bool:
    if not bbox:
        return True
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _load_points_from_csv(
    path: Path,
    commodity: str | None,
    limit: int,
    bbox: list[float] | None,
) -> list[dict[str, Any]]:
    import csv

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        lat_col, lon_col = _find_lat_lon(header)
        if not lat_col or not lon_col:
            return []

        commodity_cols = _commodity_columns(header)
        results: list[dict[str, Any]] = []
        for row in reader:
            lat = _parse_float(row.get(lat_col))
            lon = _parse_float(row.get(lon_col))
            if lat is None or lon is None:
                continue
            if not _in_bbox(lat, lon, bbox):
                continue

            if commodity and commodity_cols:
                blob = " ".join(_normalize_str(row.get(c)) for c in commodity_cols).lower()
                if _normalize_commodity(commodity) not in blob:
                    continue

            results.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "commodity": _normalize_commodity(commodity) if commodity else None,
                    "source": path.stem,
                    "dataset": "4_Jason_260126",
                }
            )
            if len(results) >= limit:
                break

    return results


def _load_documents(q: str | None, commodity: str | None, limit: int) -> list[dict[str, Any]]:
    path = _data_path("data/OSTI_retrieval/document_catalog.json")
    if not path.exists():
        return []

    data = json.loads(path.read_text())
    if not isinstance(data, list):
        return []

    query = (q or "").lower().strip()
    commodity_q = _normalize_commodity(commodity or "")

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        hay = " ".join(str(v) for v in item.values()).lower()
        if query and query not in hay:
            continue
        if commodity_q and commodity_q not in hay:
            continue
        results.append(item)
        if len(results) >= limit:
            break
    return results


app = FastAPI(
    title="Unified Data API",
    version="0.1.0",
    description="Unified API across critical-minerals datasets (Step 1).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8085", "http://127.0.0.1:8085"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


@app.get("/catalog")
def get_catalog() -> dict[str, Any]:
    return _load_registry()


@app.get("/catalog/{dataset_id}")
def get_catalog_entry(dataset_id: str) -> dict[str, Any]:
    registry = _load_registry().get("datasets", [])
    for entry in registry:
        if entry.get("id") == dataset_id:
            return entry
    raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset_id}")


@app.get("/production/ranking")
def production_ranking(
    commodity: str = Query(...),
    year: int | None = Query(None),
    source: str = Query("bgs"),
    top_n: int = Query(10, ge=1, le=50),
) -> dict[str, Any]:
    base = os.environ.get("UNIFIED_DATA_BGS_BASE", "http://127.0.0.1:8000")
    if source.lower() == "usgs":
        base = os.environ.get("UNIFIED_DATA_USGS_BASE", "http://127.0.0.1:8011")

    params = {"commodity": commodity, "top_n": top_n}
    if year is not None:
        params["year"] = year

    try:
        resp = httpx.get(f"{base}/production/ranking", params=params, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        payload["commodity_normalized"] = _normalize_commodity(commodity)
        payload["units_normalized"] = _normalize_units(payload.get("units"))
        return payload
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}") from exc


@app.get("/production/timeseries")
def production_timeseries(
    commodity: str = Query(...),
    country: str | None = Query(None),
    source: str = Query("bgs"),
) -> dict[str, Any]:
    base = os.environ.get("UNIFIED_DATA_BGS_BASE", "http://127.0.0.1:8000")
    if source.lower() == "usgs":
        base = os.environ.get("UNIFIED_DATA_USGS_BASE", "http://127.0.0.1:8011")

    params = {"commodity": commodity}
    if country:
        params["country"] = country

    try:
        resp = httpx.get(f"{base}/production/timeseries", params=params, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        payload["commodity_normalized"] = _normalize_commodity(commodity)
        payload["units_normalized"] = _normalize_units(payload.get("units"))
        return payload
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}") from exc


@app.get("/commodities")
def list_commodities(
    source: str = Query("all", description="bgs, usgs, or all"),
) -> dict[str, Any]:
    sources = []
    if source in ("all", "bgs"):
        sources.append(os.environ.get("UNIFIED_DATA_BGS_BASE", "http://127.0.0.1:8000"))
    if source in ("all", "usgs"):
        sources.append(os.environ.get("UNIFIED_DATA_USGS_BASE", "http://127.0.0.1:8011"))

    commodities: set[str] = set()
    for base in sources:
        try:
            resp = httpx.get(f"{base}/commodities", timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("commodities", []):
                commodities.add(_normalize_commodity(item))
        except Exception:
            continue

    return {
        "total": len(commodities),
        "commodities": sorted(commodities),
        "source": source,
    }


@app.get("/deposits/search")
def deposits_search(
    commodity: str | None = Query(None),
    dataset: str | None = Query(None),
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(200, ge=1, le=2000),
) -> dict[str, Any]:
    base = _data_path("data/4_Jason_260126")
    files = {
        "mrds": base / "MRDS_critical_minerals.csv",
        "mincan": base / "MinCan_mines_critical_minerals.csv",
        "ausmines": base / "AusMines_operating_critical_minerals.csv",
        "icmm": base / "ICMM_global-mining-dataset_critical_minerals.csv",
        "fineprint": base / "fineprint_facilities_critical_minerals.csv",
    }

    bbox_vals = None
    if bbox:
        try:
            bbox_vals = [float(v) for v in bbox.split(",")]
            if len(bbox_vals) != 4:
                bbox_vals = None
        except Exception:
            bbox_vals = None

    targets = [files[dataset]] if dataset in files else list(files.values())
    records: list[dict[str, Any]] = []
    for path in targets:
        remaining = max(0, limit - len(records))
        if remaining == 0:
            break
        records.extend(_load_points_from_csv(path, commodity, remaining, bbox_vals))

    return _canonical_response("local", "4_Jason_260126", records)


@app.get("/mines/search")
def mines_search(
    commodity: str | None = Query(None),
    dataset: str | None = Query(None),
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(200, ge=1, le=2000),
) -> dict[str, Any]:
    # For now, reuse the same files as deposits, which include mine/facility points.
    return deposits_search(commodity=commodity, dataset=dataset, bbox=bbox, limit=limit)


@app.get("/documents/search")
def documents_search(
    q: str | None = Query(None),
    commodity: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    records = _load_documents(q=q, commodity=commodity, limit=limit)
    return _canonical_response("osti", "document_catalog", records)


def main() -> None:
    port = int(os.environ.get("UNIFIED_DATA_API_PORT", "8090"))
    import uvicorn

    uvicorn.run("unified_data_api.app:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
