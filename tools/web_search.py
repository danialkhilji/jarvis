from ddgs import DDGS


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return results. Use this for current events, weather, news, sports scores, prices, or any question needing up-to-date information. For weather queries, always include the city name in the query (e.g. 'weather London today')."""
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return f"No results found for: {query}"
        lines = []
        for r in results:
            lines.append(f"**{r['title']}**")
            lines.append(r["body"])
            lines.append(f"Source: {r['href']}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"
