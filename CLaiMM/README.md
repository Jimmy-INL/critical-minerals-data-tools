# CLAIMM MCP Server

MCP (Model Context Protocol) servers for searching NETL's EDX CLAIMM (Critical Minerals and Materials) data. Available in two variants:

| Variant | Command | LLM Required | Use Case |
|---------|---------|--------------|----------|
| **Standard** | `claimm-mcp` | Yes | AI-powered search with summarization |
| **LLM-Agnostic** | `claimm-mcp-agnostic` | No | Direct data access, bring your own LLM |

## Features

### Standard Server (`claimm-mcp`)
- **Natural language search** - Ask questions in plain English about critical minerals data
- **Multi-LLM support** - Works with OpenAI, Anthropic, Google AI, and xAI (Grok)
- **RAG-style retrieval** - AI interprets queries, searches EDX, and summarizes results
- **Schema detection** - Auto-detect CSV/Excel column headers without full download

### LLM-Agnostic Server (`claimm-mcp-agnostic`)
- **No LLM dependencies** - Returns raw data for your own processing
- **Direct API access** - Query EDX CLAIMM data without AI overhead
- **Full schema detection** - Same header detection capabilities
- **Category organization** - Datasets organized by topic
- **Statistics** - Format and tag frequency analysis

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- EDX API key from [edx.netl.doe.gov](https://edx.netl.doe.gov)
- LLM API key (only for standard server)

## Installation

### Using uv (Recommended)

```bash
cd CLaiMM
uv sync
cp .env.example .env
# Edit .env with your API keys
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

## Configuration

### For LLM-Agnostic Server (Minimal)

```bash
# Required - Get from https://edx.netl.doe.gov (profile page)
EDX_API_KEY=your_edx_key
```

### For Standard Server (Full)

```bash
# Required
EDX_API_KEY=your_edx_key

# At least one LLM provider required
OPENAI_API_KEY=your_openai_key
# or
ANTHROPIC_API_KEY=your_anthropic_key
# or
GOOGLE_API_KEY=your_google_key
# or
XAI_API_KEY=your_xai_key

# Optional: Set default provider
DEFAULT_LLM_PROVIDER=openai
```

## Running the Servers

### LLM-Agnostic Server

```bash
# Run directly
uv run claimm-mcp-agnostic

# Or with MCP dev tools
uv run mcp dev src/claimm_mcp/server_agnostic.py
```

### Standard Server

```bash
# Run directly
uv run claimm-mcp

# Or with MCP dev tools
uv run mcp dev src/claimm_mcp/server.py
```

## Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

### LLM-Agnostic Server

```json
{
  "mcpServers": {
    "claimm-agnostic": {
      "command": "uv",
      "args": ["--directory", "/full/path/to/CLaiMM", "run", "claimm-mcp-agnostic"],
      "env": {
        "EDX_API_KEY": "your_edx_key"
      }
    }
  }
}
```

### Standard Server

```json
{
  "mcpServers": {
    "claimm": {
      "command": "uv",
      "args": ["--directory", "/full/path/to/CLaiMM", "run", "claimm-mcp"],
      "env": {
        "EDX_API_KEY": "your_edx_key",
        "OPENAI_API_KEY": "your_openai_key",
        "DEFAULT_LLM_PROVIDER": "openai"
      }
    }
  }
}
```

## Claude Code Integration

```bash
# LLM-Agnostic
claude mcp add claimm-agnostic -s user -- uv --directory /path/to/CLaiMM run claimm-mcp-agnostic
claude mcp add-env claimm-agnostic EDX_API_KEY your_edx_key

# Standard
claude mcp add claimm -s user -- uv --directory /path/to/CLaiMM run claimm-mcp
claude mcp add-env claimm EDX_API_KEY your_edx_key
claude mcp add-env claimm OPENAI_API_KEY your_openai_key
```

## Available Tools

### LLM-Agnostic Server (10 tools)

| Tool | Description |
|------|-------------|
| `search_claimm_datasets` | Search datasets by query and tags |
| `get_dataset_details` | Full dataset metadata with resources |
| `list_claimm_datasets` | List all CLAIMM datasets |
| `search_resources` | Search files by name and format |
| `get_resource_details` | Detailed resource metadata |
| `get_download_url` | Direct download URL for a resource |
| `detect_file_schema` | Detect CSV/Excel headers without full download |
| `detect_dataset_schemas` | Detect schemas for all files in a dataset |
| `get_claimm_statistics` | Format and tag frequency statistics |
| `get_datasets_by_category` | Datasets organized by category |

### Standard Server (8 tools)

| Tool | Description |
|------|-------------|
| `search_claimm_data` | Natural language search with AI summarization |
| `list_claimm_datasets` | Browse available CLAIMM datasets |
| `get_dataset_details` | Get detailed info about a dataset |
| `get_resource_details` | Get info about a specific file |
| `ask_about_data` | Ask questions about datasets |
| `get_download_url` | Get download URL for a resource |
| `detect_file_schema` | Detect CSV/Excel column headers |
| `detect_dataset_schemas` | Detect schemas for all tabular files |

## Example Usage

### Search for Datasets
```
# LLM-Agnostic: Returns raw search results
search_claimm_datasets(query="rare earth", limit=10)

# Standard: Returns AI-summarized results
"Find lithium data from coal ash studies"
```

### Get Dataset Categories
```
# LLM-Agnostic only
get_datasets_by_category()

# Returns:
# - Rare Earth Elements: 75 datasets
# - Produced Water: 27 datasets
# - Coal & Coal Byproducts: 11 datasets
# - Geology: 33 datasets
# - Geochemistry: 18 datasets
# - Mine Waste: 4 datasets
# - Lithium: 1 dataset
```

### Detect File Schema
```
# Works with both servers
detect_file_schema(resource_id="abc123", format="CSV")

# Returns column names, types, and sample values
```

### Get Statistics
```
# LLM-Agnostic only
get_claimm_statistics()

# Returns format counts, tag frequency, total datasets
```

## Project Structure

```
CLaiMM/
├── pyproject.toml              # Project configuration
├── .env                        # Your API keys (create from .env.example)
├── .env.example                # Environment template
├── README.md                   # This file
└── src/claimm_mcp/
    ├── __init__.py
    ├── server.py               # Standard MCP server (with LLM)
    ├── server_agnostic.py      # LLM-Agnostic MCP server
    ├── config.py               # Configuration management
    ├── edx_client.py           # EDX API client
    ├── llm_client.py           # LiteLLM multi-provider wrapper
    └── header_detector.py      # CSV/Excel schema detection
```

## Generated Data Files

After running analysis scripts, you may have:

| File | Description |
|------|-------------|
| `claimm_datasets.json` | All 201 CLAIMM datasets |
| `claimm_all_schemas.json` | Extracted schemas (17,361 columns) |
| `claimm_complete_schema_report.json` | Comprehensive analysis |
| `schema_documentation_report.json` | Documentation gaps |

## Choosing Between Servers

| Use Case | Recommended Server |
|----------|-------------------|
| Claude Desktop / Claude Code | Either (standard for AI features) |
| Custom LLM integration | LLM-Agnostic |
| No LLM / raw data access | LLM-Agnostic |
| AI-powered search & summarization | Standard |
| Collaborators without LLM keys | LLM-Agnostic |
| Minimal dependencies | LLM-Agnostic |

## Related Projects

| Project | Description |
|---------|-------------|
| **BGS_MCP** | LLM-agnostic MCP server for BGS World Mineral Statistics |
| **CMM_API** | Unified REST API + MCP server combining CLAIMM and BGS |

## Troubleshooting

### Rate Limiting (HTTP 429)
The EDX API has rate limits. If you encounter 429 errors, wait a few seconds between requests.

### Excel Files Require Full Download
Excel files (.xlsx, .xlsm) cannot be partially downloaded due to their ZIP-based format. Schema detection may fail for large Excel files.

### Environment Variables Not Loading
Ensure `.env` file exists in the project root and contains valid API keys.

### LLM-Agnostic Server Not Starting
Check that `mcp[cli]>=1.0.0` is installed. The agnostic server only requires `mcp`, `httpx`, and `pydantic`.

## License

MIT
