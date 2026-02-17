from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

MRDS_ZIP_URL = "https://mrdata.usgs.gov/mrds/mrds-csv.zip"


def _cache_dir() -> Path:
    override = os.environ.get("USGS_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / ".cache"


def _normalize(col: str) -> str:
    return (
        col.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("__", "_")
    )


def _find_column(columns: list[str], keywords: list[str]) -> str | None:
    for col in columns:
        lower = col.lower()
        if all(k in lower for k in keywords):
            return col
    return None


@dataclass
class MRDSColumns:
    latitude: str
    longitude: str
    country: str | None
    site_name: str | None
    commodity_fields: list[str]


class MRDSClient:
    def __init__(self) -> None:
        self._df: pd.DataFrame | None = None
        self._cols: MRDSColumns | None = None

    def _download_zip(self) -> Path:
        cache = _cache_dir() / "mrds"
        cache.mkdir(parents=True, exist_ok=True)
        dest = cache / "mrds-csv.zip"
        if dest.exists():
            return dest

        with httpx.Client(timeout=120) as client:
            resp = client.get(MRDS_ZIP_URL)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        return dest

    def _extract_csv(self, zip_path: Path) -> Path:
        cache = zip_path.parent
        with zipfile.ZipFile(zip_path) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise RuntimeError("MRDS zip does not contain a CSV file.")
            csv_name = csv_names[0]
            out = cache / csv_name
            if not out.exists():
                zf.extract(csv_name, cache)
            return out

    def _load_dataframe(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df

        zip_path = self._download_zip()
        csv_path = self._extract_csv(zip_path)
        df = pd.read_csv(csv_path, low_memory=False)
        df.columns = [_normalize(c) for c in df.columns]
        self._df = df
        self._cols = self._infer_columns(df)
        return df

    def _infer_columns(self, df: pd.DataFrame) -> MRDSColumns:
        cols = list(df.columns)
        lat = _find_column(cols, ["latitude"]) or _find_column(cols, ["lat"])
        lon = _find_column(cols, ["longitude"]) or _find_column(cols, ["lon"]) or _find_column(
            cols, ["long"]
        )
        if not lat or not lon:
            raise RuntimeError(
                "MRDS data is missing latitude/longitude columns. "
                "Update MRDS column inference."
            )

        country = _find_column(cols, ["country"])
        site_name = _find_column(cols, ["site_name"]) or _find_column(cols, ["name"])

        commodity_fields = [c for c in cols if "commod" in c]
        if not commodity_fields:
            commodity_fields = [c for c in cols if "mineral" in c or "resource" in c]

        if not commodity_fields:
            raise RuntimeError("MRDS data is missing commodity fields.")

        return MRDSColumns(
            latitude=lat,
            longitude=lon,
            country=country,
            site_name=site_name,
            commodity_fields=commodity_fields,
        )

    def search(
        self,
        commodity: str | None = None,
        country: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        df = self._load_dataframe()
        cols = self._cols
        assert cols

        work = df.copy()
        if country and cols.country:
            normalized = _normalize_country(country)
            work = work[
                work[cols.country].astype(str).str.contains(normalized, case=False, na=False, regex=False)
            ]
            if work.empty:
                for alt in _country_aliases(normalized):
                    work = df[
                        df[cols.country]
                        .astype(str)
                        .str.contains(alt, case=False, na=False, regex=False)
                    ]
                    if not work.empty:
                        break

        # Combine commodity fields into a single string for filtering
        commodity_df = work[cols.commodity_fields].astype(str).fillna("")
        commodity_blob = commodity_df.apply(
            lambda r: " ; ".join(r.values.astype(str)), axis=1
        )
        commodity_blob = commodity_blob.astype(str).str.lower()
        if commodity:
            work = work[commodity_blob.str.contains(commodity.lower(), na=False)]
            commodity_blob = commodity_blob[work.index]

        # Coordinates
        work = work.dropna(subset=[cols.latitude, cols.longitude])
        work[cols.latitude] = pd.to_numeric(work[cols.latitude], errors="coerce")
        work[cols.longitude] = pd.to_numeric(work[cols.longitude], errors="coerce")
        work = work.dropna(subset=[cols.latitude, cols.longitude])

        results: list[dict[str, Any]] = []
        for idx, row in work.head(limit).iterrows():
            name = None
            if cols.site_name and pd.notna(row.get(cols.site_name)):
                name = str(row.get(cols.site_name))

            commodities = [
                c.strip()
                for c in str(commodity_blob.loc[idx]).replace(",", ";").split(";")
                if c.strip()
            ]

            results.append(
                {
                    "name": name or "Unknown",
                    "lat": float(row.get(cols.latitude)),
                    "lng": float(row.get(cols.longitude)),
                    "country": str(row.get(cols.country)) if cols.country else None,
                    "commodities": commodities[:10],
                    "source": "mrds",
                }
            )

        return results


def _normalize_country(name: str) -> str:
    return name.replace(",", "").replace("  ", " ").strip()


def _country_aliases(name: str) -> list[str]:
    key = name.lower()
    aliases = {
        "congo democratic republic": ["Congo (Kinshasa)", "Democratic Republic of the Congo"],
        "congo republic": ["Congo (Brazzaville)", "Republic of the Congo"],
        "russia": ["Russian Federation"],
        "bolivia": ["Bolivia (Plurinational State of)"],
        "iran": ["Iran (Islamic Republic of)"],
        "tanzania": ["Tanzania, United Republic of"],
        "south korea": ["Korea, Republic of", "Republic of Korea"],
        "north korea": ["Korea, Democratic People's Republic of"],
        "vietnam": ["Viet Nam"],
        "laos": ["Lao People's Democratic Republic"],
    }
    return aliases.get(key, [])
