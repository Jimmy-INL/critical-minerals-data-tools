# Critical Minerals Data Tools - Project Log

## Session: January 9, 2026

### Contributors
- **Human**: Project direction, requirements, testing, review
- **Claude (Opus 4.5)**: Architecture design, code implementation, documentation, git operations

---

## Project Overview

Built a suite of MCP servers and REST APIs for accessing critical minerals data from two authoritative sources:
- **CLAIMM (NETL EDX)**: US Critical Minerals and Materials datasets
- **BGS World Mineral Statistics**: Global mineral production data (1970-2023)

---

## What Claude Built

### 1. CLAIMM MCP Server (`CLaiMM/`)

**Files created by Claude:**
- `src/claimm_mcp/server.py` - Standard MCP server with LLM integration
- `src/claimm_mcp/server_agnostic.py` - LLM-agnostic MCP server (10 tools)
- `src/claimm_mcp/edx_client.py` - Async EDX API client using httpx
- `src/claimm_mcp/llm_client.py` - LiteLLM wrapper for multi-provider support
- `src/claimm_mcp/header_detector.py` - CSV/Excel schema detection
- `src/claimm_mcp/config.py` - Configuration management
- `pyproject.toml` - Project configuration with uv
- `README.md` - Comprehensive documentation

**Features implemented:**
- Natural language search with AI summarization (standard server)
- Direct data access without LLM dependencies (agnostic server)
- Multi-LLM support: OpenAI, Anthropic, Google AI, xAI (Grok)
- Schema detection for CSV/Excel files without full download
- 8 tools (standard) / 10 tools (agnostic) for data access

### 2. BGS MCP Server + REST API (`BGS_MCP/`)

**Files created by Claude:**
- `src/bgs_mcp/bgs_client.py` - BGS OGC API client
- `src/bgs_mcp/server.py` - MCP server for Claude Desktop/Code
- `src/bgs_mcp/api.py` - FastAPI REST server for any LLM
- `test_openai.py` - OpenAI GPT-4o integration test
- `test_ollama.py` - Ollama local LLM integration test
- `pyproject.toml` - Project configuration
- `README.md` - Full API documentation with examples

**Features implemented:**
- Dual interface: MCP server + REST API
- 8 MCP tools for mineral data access
- RESTful endpoints with OpenAPI documentation
- OpenAI-compatible function definitions at `/openai/functions`
- Critical minerals filter (28 strategic minerals)
- Production rankings, time series, country comparisons

**Data downloaded by Claude:**
- 59,718 production records
- 16,499 trade records (imports/exports)
- Coverage: 1970-2023, 70+ commodities, worldwide

### 3. Unified CMM API (`CMM_API/`)

**Files created by Claude:**
- `src/cmm_api/clients.py` - Unified client combining BGS + CLAIMM
- `src/cmm_api/server.py` - FastAPI REST server with unified endpoints
- `src/cmm_api/mcp_server.py` - MCP server wrapper
- `test_openai.py` - OpenAI integration test
- `test_ollama.py` - Ollama integration test
- `pyproject.toml` - Project configuration
- `README.md` - Documentation

**Features implemented:**
- Single API for both CLAIMM and BGS data
- Unified search across sources
- REST API at `http://localhost:8000`
- MCP server for Claude Desktop/Code
- OpenAI function definitions for tool use

### 4. Documentation

**Files created by Claude:**
- `Data_Needs/README.md` - Overview documentation with:
  - Architecture diagram
  - Project comparison tables
  - Installation instructions
  - Quick start guide
  - LLM integration examples (OpenAI, Anthropic, Ollama, LangChain)
  - Use case examples
- `demo.ipynb` - Interactive Jupyter notebook demonstrating:
  - API usage patterns
  - BGS production rankings
  - CLAIMM dataset search
  - Data visualizations
  - LLM integration code

### 5. Git & GitHub Operations

**Performed by Claude:**
- Initialized git repository
- Created `.gitignore` with appropriate exclusions
- Identified and removed accidentally committed API key
- Pushed to GitHub: https://github.com/Redliana/critical-minerals-data-tools
- Added repository topics: `critical-minerals`, `mcp-server`, `materials-science`, etc.
- Created release tag v0.1.0 with release notes
- Packaged and uploaded BGS data as release asset (`bgs_data.tar.gz`)

### 6. Claude Desktop Configuration

**Configured by Claude:**
Added 5 MCP servers to Claude Desktop:
```json
{
  "mcpServers": {
    "cmm": "Unified API (CLAIMM + BGS)",
    "bgs": "BGS World Mineral Statistics",
    "claimm": "CLAIMM with LLM features",
    "claimm-agnostic": "CLAIMM without LLM dependencies",
    "edx": "Original EDX server"
  }
}
```

---

## Testing Performed

| Test | Status | Notes |
|------|--------|-------|
| CLAIMM MCP with Claude Desktop | Passed | Natural language search working |
| BGS REST API | Passed | All endpoints functional |
| BGS MCP with Claude Desktop | Passed | 8 tools available |
| CMM unified API with OpenAI GPT-4o | Passed | Function calling works |
| CMM unified API with Ollama phi4 | Passed | Local LLM analysis works |
| CLAIMM agnostic server | Passed | 10 tools, no LLM required |

---

## Errors Encountered & Resolved

1. **Missing README.md for hatchling build**
   - Cause: pyproject.toml referenced non-existent README
   - Fix: Created README.md files for each project

2. **FastMCP constructor argument error**
   - Cause: Incorrect initialization syntax
   - Fix: Updated to correct FastMCP API

3. **EDX API 500 error**
   - Cause: Invalid search parameters
   - Fix: Adjusted query format for CKAN API

4. **GitHub push protection blocked**
   - Cause: API key in `.claude/settings.local.json`
   - Fix: Removed file from git, added `.claude/` to `.gitignore`

5. **GitHub collaborator invite by email**
   - Cause: GitHub API requires usernames for personal repos
   - Fix: Shared repository link directly instead

---

## Repository Structure

```
Data_Needs/
├── README.md              # Overview documentation
├── demo.ipynb             # Interactive demo notebook
├── PROJECT_LOG.md         # This file
├── .gitignore             # Git exclusions
├── CLaiMM/                # CLAIMM MCP servers
│   ├── src/claimm_mcp/
│   │   ├── server.py           # Standard server (LLM-powered)
│   │   ├── server_agnostic.py  # Agnostic server (no LLM)
│   │   ├── edx_client.py       # EDX API client
│   │   ├── llm_client.py       # Multi-provider LLM wrapper
│   │   └── header_detector.py  # Schema detection
│   ├── pyproject.toml
│   └── README.md
├── BGS_MCP/               # BGS MCP server + REST API
│   ├── src/bgs_mcp/
│   │   ├── bgs_client.py       # BGS OGC API client
│   │   ├── server.py           # MCP server
│   │   └── api.py              # REST API
│   ├── test_openai.py
│   ├── test_ollama.py
│   ├── pyproject.toml
│   └── README.md
└── CMM_API/               # Unified API
    ├── src/cmm_api/
    │   ├── clients.py          # Unified data clients
    │   ├── server.py           # REST API
    │   └── mcp_server.py       # MCP server
    ├── test_openai.py
    ├── test_ollama.py
    ├── pyproject.toml
    └── README.md
```

---

## GitHub Release

**Tag**: v0.1.0 - Initial Release
**URL**: https://github.com/Redliana/critical-minerals-data-tools/releases/tag/v0.1.0

**Assets:**
- Source code (zip, tar.gz)
- `bgs_data.tar.gz` - Pre-downloaded BGS data (59,718 production + 16,499 trade records)

---

## For Collaborators

Collaborators can use the tools without LLM API keys:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Redliana/critical-minerals-data-tools.git
   cd critical-minerals-data-tools
   ```

2. **Install dependencies**
   ```bash
   cd CMM_API && uv sync
   ```

3. **Start the REST API**
   ```bash
   uv run cmm-api
   ```

4. **Query data**
   ```bash
   curl "http://localhost:8000/bgs/ranking/lithium%20minerals?top_n=10"
   ```

5. **Use with any LLM** (OpenAI, Ollama, etc.)
   - Fetch data from REST API
   - Pass to LLM for analysis
   - See `demo.ipynb` for examples

---

## Technologies Used

| Component | Technology |
|-----------|------------|
| MCP Framework | FastMCP (mcp[cli]) |
| HTTP Client | httpx (async) |
| REST API | FastAPI + Uvicorn |
| Multi-LLM | LiteLLM |
| Data Validation | Pydantic |
| Package Manager | uv |
| Version Control | Git + GitHub |

---

## License

MIT License - All projects open source.
