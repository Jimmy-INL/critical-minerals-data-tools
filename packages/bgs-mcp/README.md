# BGS World Mineral Statistics Server

Access British Geological Survey World Mineral Statistics data on critical minerals production and trade. Works with **any LLM** via REST API or with Claude via MCP.

## Two Interfaces

| Interface | Command | Use Case |
|-----------|---------|----------|
| **REST API** | `bgs-api` | OpenAI, Anthropic, Google, Ollama, any HTTP client |
| **MCP Server** | `bgs-mcp` | Claude Desktop, Claude Code |

Both interfaces are **LLM-agnostic** - no API keys required, direct access to BGS open data.

## Features

- **REST API** - Works with any LLM or HTTP client
- **MCP Server** - Native Claude Desktop/Code integration
- **No API keys required** - Direct access to BGS open data
- **Critical minerals focus** - Pre-configured list of 28 strategic minerals
- **Flexible queries** - Filter by commodity, country, year range
- **OpenAI function definitions** - Ready-to-use tool schemas

## Data Coverage

| Attribute | Details |
|-----------|---------|
| Time Range | 1970 - 2023 |
| Commodities | 70+ minerals |
| Statistics | Production, Imports, Exports |
| Geographic | Country-level worldwide |
| Source | British Geological Survey |
| License | Open Government Licence |

## Installation

```bash
cd BGS_MCP
uv sync
```

## Quick Start

### REST API

```bash
# Start the API server
uv run bgs-api

# Test it
curl http://localhost:8000/production/ranking?commodity=lithium%20minerals&top_n=5
```

### MCP Server (Claude)

```bash
uv run bgs-mcp
```

## REST API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and available endpoints |
| `/commodities` | GET | List all mineral commodities |
| `/countries` | GET | List countries with data |
| `/production/search` | GET | Search production data |
| `/production/ranking` | GET | Top producing countries |
| `/production/timeseries` | GET | Historical time series |
| `/production/compare` | GET | Compare countries |
| `/countries/{iso}/profile` | GET | Country production profile |
| `/openai/functions` | GET | OpenAI function definitions |

### Interactive Documentation

When the API is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Endpoint Details

#### `GET /commodities`
List available mineral commodities.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `critical_only` | bool | false | Only return critical minerals |

```bash
curl "http://localhost:8000/commodities?critical_only=true"
```

#### `GET /countries`
List countries with production data.

```bash
curl "http://localhost:8000/countries"
```

#### `GET /production/search`
Search production data with filters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `commodity` | string | Commodity name (e.g., "lithium minerals") |
| `country` | string | Country name or ISO3 code |
| `year_from` | int | Start year |
| `year_to` | int | End year |
| `statistic_type` | string | Production, Imports, or Exports |
| `limit` | int | Max results (default 100) |

```bash
curl "http://localhost:8000/production/search?commodity=cobalt,%20mine&country=COD&year_from=2020"
```

#### `GET /production/ranking`
Get top producing countries for a commodity.

| Parameter | Type | Description |
|-----------|------|-------------|
| `commodity` | string | Commodity name (required) |
| `year` | int | Year (defaults to most recent) |
| `top_n` | int | Number of countries (default 15) |

```bash
curl "http://localhost:8000/production/ranking?commodity=lithium%20minerals&top_n=5"
```

**Response:**
```json
{
  "commodity": "lithium minerals",
  "year": 2023,
  "units": "tonnes (metric)",
  "rankings": [
    {"rank": 1, "country": "Australia", "country_iso": "AUS", "quantity": 3386775, "share_percent": 65.38},
    {"rank": 2, "country": "Zimbabwe", "country_iso": "ZWE", "quantity": 788785, "share_percent": 15.23},
    {"rank": 3, "country": "Namibia", "country_iso": "NAM", "quantity": 300877, "share_percent": 5.81}
  ]
}
```

#### `GET /production/timeseries`
Get historical production data.

| Parameter | Type | Description |
|-----------|------|-------------|
| `commodity` | string | Commodity name (required) |
| `country` | string | Country name or ISO3 (required) |
| `year_from` | int | Start year |
| `year_to` | int | End year |

```bash
curl "http://localhost:8000/production/timeseries?commodity=graphite&country=CHN"
```

#### `GET /production/compare`
Compare production across countries.

| Parameter | Type | Description |
|-----------|------|-------------|
| `commodity` | string | Commodity name (required) |
| `countries` | string | Comma-separated ISO3 codes (required) |
| `year` | int | Year (defaults to most recent) |

```bash
curl "http://localhost:8000/production/compare?commodity=rare%20earth%20minerals&countries=CHN,AUS,USA"
```

#### `GET /countries/{iso}/profile`
Get all commodities produced by a country.

```bash
curl "http://localhost:8000/countries/AUS/profile"
```

#### `GET /openai/functions`
Get OpenAI-compatible function definitions for all endpoints.

```bash
curl "http://localhost:8000/openai/functions"
```

## LLM Integration Examples

### OpenAI (GPT-4)

```python
import json
import httpx
from openai import OpenAI

API_BASE = "http://localhost:8000"
client = OpenAI()

# Get function definitions
functions = httpx.get(f"{API_BASE}/openai/functions").json()

# Create chat with tools
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Who are the top cobalt producers?"}],
    tools=[{"type": "function", "function": f} for f in functions],
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    func_name = tool_call.function.name
    func_args = json.loads(tool_call.function.arguments)

    # Call the API
    result = httpx.get(
        f"{API_BASE}/production/ranking",
        params={"commodity": func_args["commodity"], "top_n": func_args.get("top_n", 15)}
    ).json()
```

See `test_openai.py` for a complete working example.

### Ollama (Local LLMs)

For local LLMs that don't support function calling, use the simple query approach:

```python
import json
import httpx

API_BASE = "http://localhost:8000"
OLLAMA_BASE = "http://localhost:11434"

# Fetch data first
data = httpx.get(f"{API_BASE}/production/ranking",
                 params={"commodity": "lithium minerals", "top_n": 5}).json()

# Ask LLM to analyze
response = httpx.post(
    f"{OLLAMA_BASE}/api/chat",
    json={
        "model": "phi4",  # or llama3, mistral, etc.
        "messages": [
            {"role": "system", "content": "You are a minerals analyst."},
            {"role": "user", "content": f"Analyze this lithium production data:\n{json.dumps(data, indent=2)}"}
        ],
        "stream": False
    },
    timeout=120.0
)
print(response.json()["message"]["content"])
```

See `test_ollama.py` for a complete working example.

### Anthropic Claude (via API)

```python
import anthropic
import httpx

API_BASE = "http://localhost:8000"
client = anthropic.Anthropic()

# Get and convert function definitions
functions = httpx.get(f"{API_BASE}/openai/functions").json()
tools = [
    {
        "name": f["name"],
        "description": f["description"],
        "input_schema": f["parameters"]
    }
    for f in functions
]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What are the top nickel producers?"}]
)
```

### LangChain

```python
from langchain.tools import Tool
import httpx

def get_mineral_ranking(query: str) -> str:
    """Get top producing countries for a mineral."""
    response = httpx.get(
        "http://localhost:8000/production/ranking",
        params={"commodity": query, "top_n": 10}
    )
    return response.json()

bgs_tool = Tool(
    name="BGS_Mineral_Ranking",
    func=get_mineral_ranking,
    description="Get top producing countries for a mineral commodity"
)
```

### Plain HTTP (curl)

```bash
# Top lithium producers
curl "http://localhost:8000/production/ranking?commodity=lithium%20minerals&top_n=10"

# Cobalt production in DRC
curl "http://localhost:8000/production/search?commodity=cobalt,%20mine&country=COD"

# Compare rare earth production
curl "http://localhost:8000/production/compare?commodity=rare%20earth%20minerals&countries=CHN,AUS,USA"

# Australia's mineral profile
curl "http://localhost:8000/countries/AUS/profile"
```

## Critical Minerals Available

### Battery Minerals
- `lithium minerals`
- `cobalt, mine` / `cobalt, refined`
- `nickel, mine` / `nickel, smelter/refinery`
- `graphite`
- `manganese ore`

### Rare Earth Elements
- `rare earth minerals`
- `rare earth oxides`

### Strategic Metals
- `platinum group metals, mine`
- `tungsten, mine`
- `vanadium, mine`
- `chromium ores and concentrates`
- `tantalum and niobium minerals`
- `titanium minerals`

### Technology Minerals
- `gallium, primary`
- `germanium metal`
- `indium, refinery`
- `beryl` (beryllium)

### Base Metals
- `copper, mine` / `copper, refined`
- `zinc, mine`
- `lead, mine`
- `gold, mine`
- `silver, mine`
- `antimony, mine`
- `molybdenum, mine`
- `iron ore`

## MCP Server (Claude Desktop/Code)

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "bgs": {
      "command": "uv",
      "args": ["--directory", "/path/to/BGS_MCP", "run", "bgs-mcp"]
    }
  }
}
```

### Claude Code Integration

```bash
claude mcp add bgs -s user -- uv --directory /path/to/BGS_MCP run bgs-mcp
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `list_commodities` | List all/critical minerals |
| `list_countries` | List countries with data |
| `search_production` | Search by commodity/country/year |
| `get_commodity_ranking` | Top producing countries |
| `get_time_series` | Historical production trends |
| `compare_countries` | Compare multiple countries |
| `get_country_profile` | All commodities for a country |
| `get_api_info` | API documentation |

## Project Structure

```
BGS_MCP/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── test_openai.py          # OpenAI integration test
├── test_ollama.py          # Ollama integration test
└── src/bgs_mcp/
    ├── __init__.py
    ├── bgs_client.py       # BGS API client
    ├── server.py           # MCP server (Claude)
    └── api.py              # REST API (Any LLM)
```

## Running Both Servers

You can run both the REST API and MCP server simultaneously:

```bash
# Terminal 1: REST API
uv run bgs-api

# Terminal 2: MCP Server (for Claude)
uv run bgs-mcp
```

## Data Source

- **API**: https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics
- **Website**: https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/
- **License**: Open Government Licence

## Related Projects

| Project | Description |
|---------|-------------|
| **CLaiMM** | MCP servers for NETL EDX CLAIMM data (standard + agnostic) |
| **CMM_API** | Unified REST API + MCP combining CLAIMM and BGS |

## Testing

### Test REST API

```bash
# Start the server
uv run bgs-api

# In another terminal
curl http://localhost:8000/production/ranking?commodity=lithium%20minerals
```

### Test with OpenAI

```bash
export OPENAI_API_KEY=your_key
uv run python test_openai.py
```

### Test with Ollama

```bash
# Ensure Ollama is running
ollama run phi4

# In another terminal
uv run python test_ollama.py
```

## License

MIT
