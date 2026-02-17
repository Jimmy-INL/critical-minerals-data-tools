# USGS MCS MCP Server

MCP server and REST API for **USGS Mineral Commodity Summaries (MCS)** data releases.

This package focuses on the MCS **data release CSV** published by USGS on ScienceBase
and exposes simple tools for commodity lists, rankings, time series, and country profiles.

## Features

- MCP server for Claude Desktop/Code
- REST API for any HTTP client or LLM tool use
- On-demand download + local caching of the MCS data release
- Simple rankings and time-series queries

## Data Source

USGS Mineral Commodity Summaries data releases (ScienceBase).

## Installation

```bash
cd USGS_MCP
uv sync
```

## Run

### REST API
```bash
uv run usgs-api
```

### MCP Server
```bash
uv run usgs-mcp
```

## Quick Test

```bash
# Top producers (defaults to most recent year)
curl "http://localhost:8011/production/ranking?commodity=copper"

# Time series
curl "http://localhost:8011/production/timeseries?commodity=lithium"
```

Note: first run downloads the MCS data release and caches it in `USGS_MCP/.cache`.

## Mines Endpoint

The `/mines/search` endpoint combines:
- **USGS MRDS** (Mineral Resources Data System) for deposit points.
- **OpenStreetMap** mines/quarries via Overpass API (if `source=osm` or `source=both`).

Example:
```bash
curl "http://localhost:8011/mines/search?country=Australia&commodity=gold&source=both&limit=200"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USGS_MCS_ITEM_ID` | ScienceBase item id for the MCS data release | built-in default |
| `USGS_CACHE_DIR` | Cache directory for downloaded files | `USGS_MCP/.cache` |

## REST Endpoints

- `GET /` - API info
- `GET /commodities` - list commodities
- `GET /countries` - list countries
- `GET /production/ranking` - top producers
- `GET /production/timeseries` - time series by commodity (and country)
- `GET /countries/{country}/profile` - commodity profile by country
- `GET /mines/search` - mine/deposit points (MRDS + OSM)
- `GET /openai/functions` - OpenAI-compatible function definitions

## MCP Tools

- `list_commodities`
- `list_countries`
- `get_commodity_ranking`
- `get_time_series`
- `get_country_profile`

## Notes

- The MCS data release schema can shift year to year. The loader uses
  a heuristic column mapping and will raise a clear error if required
  columns are missing. If that happens, update the column mapping in
  `src/usgs_mcp/usgs_client.py`.
