# OSTI MCP Server

MCP (Model Context Protocol) server for accessing OSTI (Office of Scientific and Technical Information) documents related to critical minerals and materials science.

## Overview

This server provides LLM-accessible tools for searching and retrieving DOE technical reports and publications. The data comes from the OSTI document retrieval system which contains 1,100+ documents across critical mineral categories.

## Installation

```bash
cd OSTI_MCP
pip install -e .
```

## Configuration

Set the path to your OSTI data directory:

```bash
export OSTI_DATA_PATH="/path/to/OSTI_retrieval"
```

Or the server will attempt to find it relative to the project structure.

## Usage

### Running the Server

```bash
osti-mcp
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "osti": {
      "command": "osti-mcp",
      "env": {
        "OSTI_DATA_PATH": "/path/to/OSTI_retrieval"
      }
    }
  }
}
```

## Available Tools

### Overview Tools

- **get_osti_overview** - Get collection statistics (total documents, commodities, product types, year range)
- **list_commodities** - List available commodity categories with descriptions

### Search Tools

- **search_osti_documents** - Search with filters:
  - `query`: Text search in title/description
  - `commodity`: Filter by category (HREE, LREE, CO, LI, GA, GR, NI, CU, GE, OTH)
  - `product_type`: "Technical Report" or "Journal Article"
  - `year_from`/`year_to`: Publication year range
  - `limit`: Maximum results

- **get_osti_document** - Get specific document by OSTI ID

### Browse Tools

- **get_documents_by_commodity** - Get documents for a specific commodity
- **get_recent_documents** - Get most recently published documents

## Commodity Categories

| Code | Description |
|------|-------------|
| HREE | Heavy Rare Earth Elements |
| LREE | Light Rare Earth Elements |
| CO   | Cobalt |
| LI   | Lithium |
| GA   | Gallium |
| GR   | Graphite |
| NI   | Nickel |
| CU   | Copper |
| GE   | Germanium |
| OTH  | Other Critical Materials |

## Example Queries

Search for lithium extraction research:
```
search_osti_documents(query="lithium extraction", commodity="LI")
```

Get recent cobalt-related publications:
```
get_documents_by_commodity(commodity="CO", limit=20)
```

Find technical reports on rare earths from 2023:
```
search_osti_documents(
    commodity="HREE",
    product_type="Technical Report",
    year_from=2023
)
```

## Data Source

Documents are retrieved from https://www.osti.gov/api/v1/records and stored locally in the OSTI_retrieval directory. The retrieval system is maintained separately in `Globus_Sharing/OSTI_retrieval/osti_retrieval.py`.
