# tools/web_search_tool.py

from duckduckgo_search import DDGS


def web_search(query: str, num_results: int = 5) -> dict:
    """
    Search the web using DuckDuckGo. No API key required.

    Args:
        query:       The search query string
        num_results: Number of results to return (default 5)

    Returns:
        dict with 'results' list and 'raw_text' summary string
    """
    try:
        with DDGS() as ddgs:
            items = list(ddgs.text(query, max_results=num_results))

        if not items:
            return {"query": query, "results": [], "raw_text": "No results found."}

        results = []
        lines = []

        for i, item in enumerate(items, 1):
            result = {
                "rank": i,
                "title": item.get("title", ""),
                "snippet": item.get("body", "").replace("\n", " "),
                "link": item.get("href", ""),
            }
            results.append(result)
            lines.append(
                f"[{i}] {result['title']}\n"
                f"    {result['snippet']}\n"
                f"    {result['link']}"
            )

        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "raw_text": "\n\n".join(lines),
        }

    except Exception as e:
        return {"error": f"Search failed: {e}", "results": [], "raw_text": ""}


# Claude tool schema — unchanged, drop-in compatible
WEB_SEARCH_TOOL_SCHEMA = {
    "name": "web_search",
    "description": (
        "Search the web for current information not available in internal documents. "
        "Use for recent news, facts, or any topic requiring up-to-date data. "
        "Returns structured results with titles, snippets, and source links."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on the web",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of search results to return (default 5, max 10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}