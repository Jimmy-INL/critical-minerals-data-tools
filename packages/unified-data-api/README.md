# Unified Data API (Step 1)

A minimal FastAPI service that exposes a unified catalog and common endpoints across core critical-minerals datasets.

## Run (dev)

```bash
cd Unified_Data_API
uv run unified-data-api
```

Environment variables:
- `UNIFIED_DATA_API_PORT` (default 8090)
- `UNIFIED_DATA_BGS_BASE` (default http://127.0.0.1:8000)
- `UNIFIED_DATA_USGS_BASE` (default http://127.0.0.1:8011)

## Endpoints
- `GET /catalog`
- `GET /catalog/{dataset}`
- `GET /production/ranking`
- `GET /production/timeseries`
- `GET /deposits/search`
- `GET /mines/search`
- `GET /documents/search`
