from ddgs import DDGS

SKILL_NAME = "get_weather"
SKILL_DESCRIPTION = "Use this skill to get current weather for a city using internet. Returns a short weather summary with temperature in Celsius."


def run(city: str) -> str:
    try:
        results = DDGS().text(f"current weather in {city} temperature today", max_results=3)
        if not results:
            return f"Could not find weather for {city}"
        lines = []
        for r in results:
            lines.append(f"**{r['title']}**")
            lines.append(r["body"])
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Weather lookup error: {e}"
