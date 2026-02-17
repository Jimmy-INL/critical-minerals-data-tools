from __future__ import annotations

from typing import Any

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _overpass_query(country: str) -> str:
    return f"""
[out:json][timeout:25];
area["name"="{country}"]["admin_level"="2"]->.a;
(
  node(area.a)["man_made"="mine"];
  way(area.a)["man_made"="mine"];
  relation(area.a)["man_made"="mine"];
  node(area.a)["landuse"="quarry"];
  way(area.a)["landuse"="quarry"];
  relation(area.a)["landuse"="quarry"];
);
out center 200;
""".strip()


def _matches_commodity(tags: dict[str, Any], commodity: str | None) -> bool:
    if not commodity:
        return True
    hay = " ".join(str(v) for v in tags.values()).lower()
    return commodity.lower() in hay


def search_osm_mines(country: str, commodity: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    query = _overpass_query(country)
    with httpx.Client(timeout=60) as client:
        resp = client.post(OVERPASS_URL, data=query)
        resp.raise_for_status()
        data = resp.json()

    results: list[dict[str, Any]] = []
    for element in data.get("elements", []):
        tags = element.get("tags") or {}
        if not _matches_commodity(tags, commodity):
            continue

        lat = element.get("lat")
        lng = element.get("lon")
        if lat is None or lng is None:
            # ways/relations return center
            center = element.get("center") or {}
            lat = center.get("lat")
            lng = center.get("lon")
        if lat is None or lng is None:
            continue

        name = tags.get("name") or tags.get("operator") or "Mine / Quarry"
        results.append(
            {
                "name": name,
                "lat": float(lat),
                "lng": float(lng),
                "country": country,
                "commodities": [],
                "source": "osm",
            }
        )
        if len(results) >= limit:
            break

    return results
