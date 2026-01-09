"""CLAIMM MCP Server - Search NETL EDX CLAIMM data with LLM support."""

from mcp.server.fastmcp import FastMCP

try:
    from .edx_client import EDXClient
    from .llm_client import LLMClient
    from .header_detector import HeaderDetector
except ImportError:
    # Handle direct execution (e.g., mcp dev)
    from claimm_mcp.edx_client import EDXClient
    from claimm_mcp.llm_client import LLMClient
    from claimm_mcp.header_detector import HeaderDetector

# Initialize the MCP server
mcp = FastMCP(
    name="CLAIMM Data Search",
    instructions="Search and explore NETL's CLAIMM (Critical Minerals and Materials) data with AI-powered assistance",
)


def get_edx_client() -> EDXClient:
    """Get or create EDX client instance."""
    return EDXClient()


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    return LLMClient()


def get_header_detector() -> HeaderDetector:
    """Get or create HeaderDetector instance."""
    return HeaderDetector()


@mcp.tool()
async def detect_file_schema(
    resource_id: str,
    format: str | None = None,
) -> str:
    """
    Detect column headers and data types from a CSV or Excel file without downloading
    the entire file. Uses HTTP Range requests to fetch only the first portion.

    Args:
        resource_id: The resource ID of the file to analyze
        format: Optional file format hint (CSV, XLSX). Auto-detected if not provided.

    Returns:
        Detected schema including column names, types, and sample data
    """
    detector = get_header_detector()

    # Detect format if not provided
    if not format:
        edx = get_edx_client()
        try:
            resource = await edx.get_resource(resource_id)
            format = resource.format
        except Exception:
            format = "CSV"  # Default to CSV

    result = await detector.detect_headers(resource_id, format)

    if not result.get("success"):
        return f"**Error detecting schema:** {result.get('error', 'Unknown error')}\n\nResource ID: `{resource_id}`"

    # Get download URL
    edx = get_edx_client()
    download_url = edx.get_download_url(resource_id)

    # Format output
    output = f"**File Schema Detection**\n\n"
    output += f"- Resource ID: `{resource_id}`\n"
    output += f"- Format: {result.get('format', format)}\n"
    output += f"- Bytes fetched: {result.get('bytes_fetched', 'N/A'):,}\n"
    output += f"- 📥 Download: {download_url}\n"

    if result.get("format") == "CSV" or "column_count" in result:
        output += f"- Columns: {result.get('column_count', 0)}\n"
        output += f"- Delimiter: `{result.get('delimiter', ',')}`\n\n"

        output += "**Column Schema:**\n\n"
        output += "| # | Column Name | Type | Nullable | Sample Values |\n"
        output += "|---|-------------|------|----------|---------------|\n"

        for i, col in enumerate(result.get("column_types", [])[:50], 1):
            name = col.get("name", "")[:30]
            col_type = col.get("type", "unknown")
            nullable = "Yes" if col.get("nullable") else "No"
            samples = ", ".join(str(v)[:15] for v in col.get("sample_values", [])[:2])
            output += f"| {i} | {name} | {col_type} | {nullable} | {samples} |\n"

        if len(result.get("column_types", [])) > 50:
            output += f"\n*... and {len(result['column_types']) - 50} more columns*\n"

    elif result.get("sheets"):
        output += f"- Sheets: {len(result.get('sheet_names', []))}\n\n"

        for sheet_name, sheet_data in result.get("sheets", {}).items():
            output += f"**Sheet: {sheet_name}**\n"
            output += f"- Columns: {sheet_data.get('column_count', 0)}\n"
            headers = sheet_data.get("headers", [])[:10]
            output += f"- Headers: {', '.join(h for h in headers if h)}\n\n"

    return output


@mcp.tool()
async def detect_dataset_schemas(
    dataset_id: str,
    formats: str = "CSV,XLSX",
) -> str:
    """
    Detect schemas for all tabular files in a dataset. Analyzes CSV and Excel
    files to extract column headers and data types.

    Args:
        dataset_id: The dataset ID or name
        formats: Comma-separated list of formats to analyze (default: "CSV,XLSX")

    Returns:
        Summary of detected schemas for all tabular resources in the dataset
    """
    edx = get_edx_client()
    detector = get_header_detector()

    # Get dataset details
    submission = await edx.get_submission(dataset_id)

    # Filter to requested formats
    format_list = [f.strip().upper() for f in formats.split(",")]
    tabular_resources = [
        r for r in submission.resources
        if r.format and r.format.upper() in format_list
    ]

    if not tabular_resources:
        return f"No tabular files ({formats}) found in dataset: {submission.title}"

    output = f"**Schema Detection for: {submission.title}**\n\n"
    output += f"Found {len(tabular_resources)} tabular file(s)\n\n"

    for resource in tabular_resources:
        download_url = edx.get_download_url(resource.id)
        output += f"---\n\n### {resource.name}\n\n"
        output += f"- **Resource ID:** `{resource.id}`\n"
        output += f"- **📥 Download:** {download_url}\n"

        result = await detector.detect_headers(resource.id, resource.format)

        if result.get("success"):
            if "column_count" in result:
                output += f"- **Columns:** {result['column_count']}\n"
                headers = result.get("headers", [])[:10]
                output += f"- **Headers:** {', '.join(headers)}"
                if len(result.get("headers", [])) > 10:
                    output += f" ... (+{len(result['headers']) - 10} more)"
                output += "\n"

                # Show column types summary
                types = {}
                for col in result.get("column_types", []):
                    t = col.get("type", "unknown")
                    types[t] = types.get(t, 0) + 1
                output += f"- **Types:** {', '.join(f'{t}: {c}' for t, c in types.items())}\n"

            elif result.get("sheets"):
                for sheet, data in result.get("sheets", {}).items():
                    output += f"- **Sheet '{sheet}':** {data.get('column_count', 0)} columns\n"
        else:
            output += f"- **Error:** {result.get('error', 'Unknown')[:50]}\n"

        output += "\n"

    return output


@mcp.tool()
async def search_claimm_data(
    query: str,
    format_filter: str | None = None,
    max_results: int = 10,
) -> str:
    """
    Search CLAIMM data using natural language. The query is interpreted by AI
    to find relevant datasets about critical minerals, mine waste, and related topics.

    Args:
        query: Natural language search query (e.g., "lithium data from coal ash")
        format_filter: Optional file format filter (CSV, JSON, PDF, XLSX, etc.)
        max_results: Maximum number of results to return (default: 10)

    Returns:
        AI-generated summary of search results with dataset details
    """
    edx = get_edx_client()
    llm = get_llm_client()

    # Interpret the query using LLM
    interpreted = await llm.interpret_search_query(query)

    # Search EDX - prepend "claimm" to ensure we search CLAIMM data
    search_query = f"claimm {interpreted['query']}"
    results = await edx.search_submissions(
        query=search_query,
        tags=interpreted.get("tags"),
        limit=max_results,
    )

    # If format filter provided, apply it (override LLM interpretation)
    if format_filter:
        # Filter results by format
        filtered = []
        for sub in results:
            matching_resources = [
                r for r in sub.resources
                if r.format and r.format.upper() == format_filter.upper()
            ]
            if matching_resources:
                sub.resources = matching_resources
                filtered.append(sub)
        results = filtered

    # Generate summary
    summary = await llm.summarize_search_results(results, query)

    # Add interpretation note
    if interpreted.get("explanation"):
        summary = f"**Search interpretation:** {interpreted['explanation']}\n\n{summary}"

    # Add download URLs section
    download_section = "\n\n---\n\n**📥 Direct Download Links:**\n\n"
    for i, sub in enumerate(results[:10], 1):  # Limit to top 10 for readability
        download_section += f"{i}. **{sub.title or sub.name}**\n"
        download_section += f"   - Dataset ID: `{sub.id}`\n"
        
        # Add links for each resource in the dataset
        if sub.resources:
            if len(sub.resources) == 1:
                # Single resource - show direct link
                resource = sub.resources[0]
                download_url = edx.get_download_url(resource.id)
                format_info = f" ({resource.format})" if resource.format else ""
                download_section += f"   - Download{format_info}: {download_url}\n"
            else:
                # Multiple resources - list them
                download_section += f"   - Files ({len(sub.resources)}):\n"
                for resource in sub.resources[:5]:  # Limit to first 5 files
                    download_url = edx.get_download_url(resource.id)
                    format_info = f" ({resource.format})" if resource.format else ""
                    file_name = resource.name[:50] + "..." if len(resource.name) > 50 else resource.name
                    download_section += f"     - {file_name}{format_info}: {download_url}\n"
                if len(sub.resources) > 5:
                    download_section += f"     - *... and {len(sub.resources) - 5} more files*\n"
        download_section += "\n"
    
    summary += download_section

    return summary


@mcp.tool()
async def list_claimm_datasets(
    category: str | None = None,
    max_results: int = 20,
) -> str:
    """
    List available datasets in the CLAIMM collection.

    Args:
        category: Optional category/tag filter (e.g., "lithium", "rare-earth", "coal-ash")
        max_results: Maximum number of results (default: 20)

    Returns:
        List of CLAIMM datasets with basic information
    """
    edx = get_edx_client()

    tags = [category] if category else None
    # Always search for "claimm" to ensure we get CLAIMM data
    submissions = await edx.search_submissions(
        query="claimm",
        tags=tags,
        limit=max_results,
    )

    if not submissions:
        return f"No datasets found in CLAIMM{f' with category {category}' if category else ''}."

    output_lines = [f"**CLAIMM Datasets** ({len(submissions)} found)\n"]

    for sub in submissions:
        formats = set(r.format for r in sub.resources if r.format)
        output_lines.append(
            f"- **{sub.title or sub.name}**\n"
            f"  - ID: `{sub.id}`\n"
            f"  - Files: {len(sub.resources)} ({', '.join(formats) if formats else 'unknown formats'})\n"
            f"  - Tags: {', '.join(sub.tags[:5]) if sub.tags else 'None'}"
        )
        # Add download links for resources
        if sub.resources:
            for resource in sub.resources[:3]:  # Show first 3 files
                download_url = edx.get_download_url(resource.id)
                format_info = f" ({resource.format})" if resource.format else ""
                file_name = resource.name[:40] + "..." if len(resource.name) > 40 else resource.name
                output_lines.append(f"  - 📥 {file_name}{format_info}: {download_url}")
            if len(sub.resources) > 3:
                output_lines.append(f"  - *... +{len(sub.resources) - 3} more files*")
        output_lines.append("")  # Add blank line between datasets

    return "\n".join(output_lines)


@mcp.tool()
async def get_dataset_details(dataset_id: str) -> str:
    """
    Get detailed information about a specific CLAIMM dataset.

    Args:
        dataset_id: The dataset ID or name

    Returns:
        Detailed dataset information including all resources
    """
    edx = get_edx_client()

    submission = await edx.get_submission(dataset_id)

    output = f"""**{submission.title or submission.name}**

**Description:**
{submission.notes or 'No description available.'}

**Metadata:**
- ID: `{submission.id}`
- Author: {submission.author or 'Unknown'}
- Organization: {submission.organization or 'Unknown'}
- Created: {submission.metadata_created or 'Unknown'}
- Modified: {submission.metadata_modified or 'Unknown'}
- Tags: {', '.join(submission.tags) if submission.tags else 'None'}

**Resources ({len(submission.resources)} files):**
"""

    for r in submission.resources:
        size_str = f"{r.size:,} bytes" if r.size else "Unknown size"
        output += f"""
- **{r.name}**
  - ID: `{r.id}`
  - Format: {r.format or 'Unknown'}
  - Size: {size_str}
  - Download: {edx.get_download_url(r.id)}
"""

    return output


@mcp.tool()
async def get_resource_details(resource_id: str) -> str:
    """
    Get detailed information about a specific resource (file) in CLAIMM.

    Args:
        resource_id: The resource ID

    Returns:
        Detailed resource information including download URL
    """
    edx = get_edx_client()

    resource = await edx.get_resource(resource_id)

    size_str = f"{resource.size:,} bytes" if resource.size else "Unknown"

    return f"""**{resource.name}**

**Details:**
- ID: `{resource.id}`
- Format: {resource.format or 'Unknown'}
- Size: {size_str}
- Created: {resource.created or 'Unknown'}
- Last Modified: {resource.last_modified or 'Unknown'}

**Description:**
{resource.description or 'No description available.'}

**Download URL:**
{edx.get_download_url(resource.id)}
"""


@mcp.tool()
async def ask_about_data(
    question: str,
    dataset_id: str | None = None,
    resource_id: str | None = None,
) -> str:
    """
    Ask a question about CLAIMM data. Provide either a dataset_id or resource_id
    for specific questions, or ask general questions about the CLAIMM collection.

    Args:
        question: Your question about the data
        dataset_id: Optional dataset ID for dataset-specific questions
        resource_id: Optional resource ID for file-specific questions

    Returns:
        AI-generated answer based on available metadata
    """
    edx = get_edx_client()
    llm = get_llm_client()

    if resource_id:
        resource = await edx.get_resource(resource_id)
        submission = None
        if resource.package_id:
            try:
                submission = await edx.get_submission(resource.package_id)
            except Exception:
                pass
        return await llm.answer_about_resource(resource, submission, question)

    if dataset_id:
        submission = await edx.get_submission(dataset_id)
        # Use the first resource as context if available
        resource = submission.resources[0] if submission.resources else None
        if resource:
            return await llm.answer_about_resource(resource, submission, question)
        else:
            # Answer based on submission only
            try:
                from .edx_client import Resource
            except ImportError:
                from claimm_mcp.edx_client import Resource
            dummy_resource = Resource(
                id=submission.id,
                name=submission.name,
                description=submission.notes,
            )
            return await llm.answer_about_resource(dummy_resource, submission, question)

    # General question - search for relevant data first
    results = await edx.search_submissions(query=f"claimm {question}", limit=5)
    if results:
        context = "\n".join([
            f"- {s.title or s.name}: {(s.notes or '')[:200]}"
            for s in results
        ])
        return f"""Based on searching CLAIMM for "{question}", here are relevant datasets:

{context}

To get more specific information, please provide a dataset_id or resource_id."""

    return "I couldn't find relevant data to answer your question. Try rephrasing or use search_claimm_data first."


@mcp.tool()
async def get_download_url(resource_id: str) -> str:
    """
    Get the direct download URL for a CLAIMM resource.

    Args:
        resource_id: The resource ID

    Returns:
        Direct download URL for the resource
    """
    edx = get_edx_client()
    return edx.get_download_url(resource_id)


def main():
    """Run the CLAIMM MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
