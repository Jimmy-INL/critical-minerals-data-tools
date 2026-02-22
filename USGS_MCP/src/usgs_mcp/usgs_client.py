from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

SCIENCEBASE_ITEM_ID_DEFAULT = "696a75d5d4be0228872d3bf8"  # MCS 2026 data release
SCIENCEBASE_ITEM_URL = "https://www.sciencebase.gov/catalog/item/{item_id}?format=json"


def _cache_dir() -> Path:
    override = os.environ.get("USGS_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / ".cache"


def _normalize_col(col: str) -> str:
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def _find_column(columns: list[str], keywords: list[str]) -> str | None:
    for col in columns:
        lower = col.lower()
        if all(k in lower for k in keywords):
            return col
    return None


def _parse_year(series: pd.Series) -> pd.Series:
    # Extract the first 4-digit year from strings like "2021–24".
    year_str = series.astype(str).str.extract(r"(\d{4})", expand=False)
    return pd.to_numeric(year_str, errors="coerce")


def _parse_value(series: pd.Series) -> pd.Series:
    # Remove commas and non-numeric characters, keep minus and dot.
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("—", "", regex=False)
        .str.replace("..", "", regex=False)
        .str.replace("…", "", regex=False)
        .str.replace(r"[^0-9.\\-]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


@dataclass
class ColumnMap:
    commodity: str
    country: str
    year: str
    value: str
    unit: str | None = None
    statistic: str | None = None


class USGSMCSClient:
    def __init__(self, item_id: str | None = None) -> None:
        self.item_id = item_id or os.environ.get("USGS_MCS_ITEM_ID", SCIENCEBASE_ITEM_ID_DEFAULT)
        self._df: pd.DataFrame | None = None
        self._col_map: ColumnMap | None = None

    def _get_item_json(self) -> dict[str, Any]:
        url = SCIENCEBASE_ITEM_URL.format(item_id=self.item_id)
        with httpx.Client(timeout=30) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    def _pick_data_file(self, item_json: dict[str, Any]) -> tuple[str, str]:
        files = item_json.get("files", []) or []
        candidates: list[tuple[str, str]] = []
        for f in files:
            name = f.get("name") or f.get("fileName") or f.get("title") or ""
            url = f.get("downloadUri") or f.get("url") or f.get("downloadUrl")
            if name and url:
                candidates.append((name, url))

        # Prefer the commodities data CSV
        for name, url in candidates:
            if "Commodities_Data" in name and name.endswith(".csv"):
                return name, url

        # Fallback to any CSV
        for name, url in candidates:
            if name.endswith(".csv"):
                return name, url

        raise RuntimeError(
            "No CSV files found in ScienceBase item. "
            "Check USGS_MCS_ITEM_ID or update file selection logic."
        )

    def _download_csv(self) -> Path:
        local_override = os.environ.get("USGS_MCS_LOCAL_CSV")
        if local_override:
            path = Path(local_override).expanduser().resolve()
            if path.exists():
                return path

        cache = _cache_dir()
        cache.mkdir(parents=True, exist_ok=True)

        item_json = self._get_item_json()
        filename, url = self._pick_data_file(item_json)
        dest = cache / filename

        if dest.exists():
            return dest

        with httpx.Client(timeout=60) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)

        return dest

    def _load_dataframe(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df

        csv_path = self._download_csv()
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
        except UnicodeDecodeError:
            # USGS data releases sometimes use Windows-1252 encoding.
            df = pd.read_csv(csv_path, encoding="cp1252")
        df.columns = [_normalize_col(c) for c in df.columns]

        if "prod_2023" in df.columns or any(c.startswith("prod_") for c in df.columns):
            df = self._reshape_world_production(df)

        self._df = df
        self._col_map = self._infer_columns(df)
        return df

    def _reshape_world_production(self, df: pd.DataFrame) -> pd.DataFrame:
        # Convert MCS world production wide format into long format.
        colmap = {
            "commodity": _find_column(list(df.columns), ["commodity"]),
            "country": _find_column(list(df.columns), ["country"]),
            "unit": _find_column(list(df.columns), ["unit"]),
        }
        if not colmap["commodity"] or not colmap["country"]:
            return df

        prod_cols: list[tuple[str, int, str]] = []
        for col in df.columns:
            normalized = re.sub(r"_+", "_", col)
            match = re.match(r"prod(_est)?_?(\d{4})", normalized)
            if not match:
                continue
            est = bool(match.group(1))
            year = int(match.group(2))
            statistic = "Production (est)" if est else "Production"
            prod_cols.append((col, year, statistic))

        if not prod_cols:
            return df

        records = []
        for col, year, statistic in prod_cols:
            subset = df[[colmap["commodity"], colmap["country"], col]].copy()
            subset["year"] = year
            subset["value"] = subset[col]
            subset["statistic"] = statistic
            subset["unit"] = df[colmap["unit"]] if colmap["unit"] else None
            subset = subset.rename(
                columns={
                    colmap["commodity"]: "commodity",
                    colmap["country"]: "country",
                }
            )
            records.append(subset[["commodity", "country", "year", "value", "unit", "statistic"]])

        long_df = pd.concat(records, ignore_index=True)
        return long_df

    def _infer_columns(self, df: pd.DataFrame) -> ColumnMap:
        cols = list(df.columns)
        commodity = _find_column(cols, ["commodity"]) or _find_column(cols, ["mineral"])
        country = _find_column(cols, ["country"]) or _find_column(cols, ["nation"])
        year = _find_column(cols, ["year"])
        value = (
            _find_column(cols, ["value"])
            or _find_column(cols, ["quantity"])
            or _find_column(cols, ["production"])
            or _find_column(cols, ["amount"])
        )
        unit = _find_column(cols, ["unit"])
        statistic = _find_column(cols, ["statistic"]) or _find_column(cols, ["measure"])

        missing = [name for name, col in [("commodity", commodity), ("country", country), ("year", year), ("value", value)] if col is None]
        if missing:
            raise RuntimeError(
                f"Missing expected columns: {', '.join(missing)}. "
                "Update the column inference in usgs_client.py for this data release."
            )

        return ColumnMap(
            commodity=commodity,
            country=country,
            year=year,
            value=value,
            unit=unit,
            statistic=statistic,
        )

    def _filtered(self, commodity: str | None = None, country: str | None = None, statistic_type: str | None = None) -> pd.DataFrame:
        df = self._load_dataframe()
        col = self._col_map
        assert col

        out = df
        if commodity:
            out = out[
                out[col.commodity]
                .astype(str)
                .str.contains(commodity, case=False, na=False, regex=False)
            ]
        if country:
            out = out[out[col.country].astype(str).str.contains(country, case=False, na=False)]
        if statistic_type and col.statistic:
            out = out[out[col.statistic].astype(str).str.contains(statistic_type, case=False, na=False)]
        return out

    def list_commodities(self) -> list[str]:
        df = self._load_dataframe()
        col = self._col_map
        assert col
        return sorted(df[col.commodity].dropna().astype(str).unique().tolist())

    def list_countries(self) -> list[str]:
        df = self._load_dataframe()
        col = self._col_map
        assert col
        return sorted(df[col.country].dropna().astype(str).unique().tolist())

    def get_country_ranking(
        self,
        commodity: str,
        year: int | None = None,
        statistic_type: str = "Production",
        top_n: int = 10,
    ) -> dict[str, Any]:
        df = self._filtered(commodity=commodity, statistic_type=statistic_type)
        col = self._col_map
        assert col

        if df.empty:
            return {
                "commodity": commodity,
                "year": year,
                "statistic_type": statistic_type,
                "units": None,
                "total_quantity": 0.0,
                "rankings": [],
            }

        df[col.value] = _parse_value(df[col.value])
        df[col.year] = _parse_year(df[col.year])
        df = df.dropna(subset=[col.value, col.year])

        # Ensure we only use Production rows for rankings
        if col.statistic:
            df = df[df[col.statistic].astype(str).str.contains("Production", case=False, na=False)]

        if df.empty:
            return {
                "commodity": commodity,
                "year": year,
                "statistic_type": statistic_type,
                "units": None,
                "total_quantity": 0.0,
                "rankings": [],
            }

        if year is None:
            year_max = df[col.year].max()
            if pd.isna(year_max):
                return {
                    "commodity": commodity,
                    "year": None,
                    "statistic_type": statistic_type,
                    "units": None,
                    "total_quantity": 0.0,
                    "rankings": [],
                }
            year = int(year_max)
        df = df[df[col.year] == year]
        if df.empty:
            return {
                "commodity": commodity,
                "year": year,
                "statistic_type": statistic_type,
                "units": None,
                "total_quantity": 0.0,
                "rankings": [],
            }

        grouped = df.groupby(col.country, as_index=False)[col.value].sum()
        # Drop aggregate rows if present
        grouped = grouped[
            ~grouped[col.country]
            .astype(str)
            .str.lower()
            .isin(["world total", "other countries"])
        ]
        grouped = grouped.sort_values(col.value, ascending=False)

        total = grouped[col.value].sum()
        rankings = []
        for i, row in grouped.head(top_n).iterrows():
            quantity = float(row[col.value])
            rankings.append(
                {
                    "rank": len(rankings) + 1,
                    "country": str(row[col.country]),
                    "quantity": quantity,
                    "share_percent": float((quantity / total) * 100) if total else 0.0,
                }
            )

        units = None
        if col.unit and not df[col.unit].dropna().empty:
            units = df[col.unit].dropna().astype(str).mode().iloc[0]

        return {
            "commodity": commodity,
            "year": year,
            "statistic_type": statistic_type,
            "units": units,
            "total_quantity": float(total) if total else 0.0,
            "rankings": rankings,
        }

    def get_time_series(
        self,
        commodity: str,
        country: str | None = None,
        statistic_type: str = "Production",
    ) -> dict[str, Any]:
        df = self._filtered(commodity=commodity, country=country, statistic_type=statistic_type)
        col = self._col_map
        assert col

        df[col.value] = _parse_value(df[col.value])
        df[col.year] = _parse_year(df[col.year])
        df = df.dropna(subset=[col.value, col.year])

        grouped = df.groupby(col.year, as_index=False)[col.value].sum().sort_values(col.year)
        points = [{"year": int(r[col.year]), "quantity": float(r[col.value])} for _, r in grouped.iterrows()]

        units = None
        if col.unit and not df[col.unit].dropna().empty:
            units = df[col.unit].dropna().astype(str).mode().iloc[0]

        return {
            "commodity": commodity,
            "country": country,
            "statistic_type": statistic_type,
            "units": units,
            "series": points,
        }

    def get_country_profile(
        self,
        country: str,
        year: int | None = None,
        statistic_type: str = "Production",
        limit: int = 20,
    ) -> dict[str, Any]:
        df = self._filtered(country=country, statistic_type=statistic_type)
        col = self._col_map
        assert col

        df[col.value] = _parse_value(df[col.value])
        df[col.year] = _parse_year(df[col.year])
        df = df.dropna(subset=[col.value, col.year])

        if df.empty:
            return {
                "country": country,
                "year": int(year) if year is not None else 0,
                "statistic_type": statistic_type,
                "commodities": [],
            }

        if year is None:
            year = int(df[col.year].max())
        df = df[df[col.year] == year]

        grouped = df.groupby(col.commodity, as_index=False)[col.value].sum()
        grouped = grouped.sort_values(col.value, ascending=False)

        units = None
        if col.unit and not df[col.unit].dropna().empty:
            units = df[col.unit].dropna().astype(str).mode().iloc[0]

        commodities = [
            {"commodity": str(r[col.commodity]), "quantity": float(r[col.value]), "units": units}
            for _, r in grouped.head(limit).iterrows()
        ]

        return {
            "country": country,
            "year": year,
            "statistic_type": statistic_type,
            "commodities": commodities,
        }
