# UN Comtrade MCP Server

MCP server for accessing international trade data from the UN Comtrade database, with a focus on critical minerals.

## Features

- Query bilateral trade flows between any countries
- Pre-configured HS codes for critical minerals (CMM focus):
  - Lithium, Cobalt, Rare Earth Elements (HREE/LREE)
  - Graphite, Nickel, Manganese, Gallium, Germanium
- Get import/export summaries and country trade profiles
- List available reporters, partners, and commodity codes

## Installation

```bash
cd UNComtrade_MCP
uv sync
```

## Configuration

1. Register at [UN Comtrade Plus](https://comtradeplus.un.org/)
2. Subscribe to the "comtrade - v1" product at [Developer Portal](https://comtradedeveloper.un.org/)
3. Create a `.env` file with your API key:

```bash
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Run the MCP server

```bash
uv run uncomtrade-mcp
```

### Add to Claude Code

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "uncomtrade": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/UNComtrade_MCP", "uncomtrade-mcp"],
      "env": {
        "UNCOMTRADE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### Overview Tools

| Tool | Description |
|------|-------------|
| `get_api_status` | Check API connectivity and key validity |
| `list_critical_minerals` | List available critical minerals with HS codes |
| `list_reporters` | List available reporter countries |
| `list_partners` | List available partner countries |
| `list_commodities` | List HS commodity codes |

### Data Query Tools

| Tool | Description |
|------|-------------|
| `get_trade_data` | Query trade data with custom parameters |
| `get_critical_mineral_trade` | Query trade data for a critical mineral |
| `get_commodity_trade_summary` | Get top importers/exporters for a commodity |
| `get_country_trade_profile` | Get a country's critical minerals trade profile |

## Examples

### Query lithium imports to the USA

```python
get_critical_mineral_trade(
    mineral="lithium",
    reporter="842",  # USA
    flow="M",        # Imports
    year="2023"
)
```

### Get top cobalt exporters globally

```python
get_commodity_trade_summary(
    commodity="2605",  # Cobalt ores
    year="2023",
    flow="X",          # Exports
    top_n=10
)
```

### Get China's critical minerals trade profile

```python
get_country_trade_profile(
    country="156",  # China
    year="2023"
)
```

## Country Codes (Common)

| Code | Country |
|------|---------|
| 0 | World (aggregate) |
| 156 | China |
| 842 | United States |
| 36 | Australia |
| 76 | Brazil |
| 124 | Canada |
| 180 | DR Congo |
| 152 | Chile |
| 392 | Japan |
| 410 | South Korea |
| 276 | Germany |

## Critical Minerals HS Codes

| Mineral | HS Codes |
|---------|----------|
| Lithium | 282520, 283691, 850650 |
| Cobalt | 2605, 810520, 810590 |
| Rare Earth (all) | 2846 |
| Graphite | 250410, 250490 |
| Nickel | 2604, 750210, 750220 |
| Manganese | 2602, 811100 |
| Gallium | 811292 |
| Germanium | 811299 |

## API Rate Limits

- Without API key: 500 records per call, unlimited calls
- With API key: 100,000 records per call, 500 calls/day

## License

MIT
