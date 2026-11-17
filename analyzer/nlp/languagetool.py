"""Optional local LanguageTool adapter. It never calls the public API."""
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def _local_tool():
    if os.environ.get("GRAMMAR_ENGINE_LANGUAGETOOL", "1").lower() in {"0", "false", "no", "off"}:
        return None
    import language_tool_python
    return language_tool_python.LanguageTool("en-US")


def check_with_languagetool(text):
    """Return normalized local-server matches; fail closed to custom rules."""
    try:
        tool = _local_tool()
        if tool is None:
            return []
        results = []
        for match in tool.check(text):
            replacements = list(match.replacements or [])
            suggestion = replacements[0] if replacements else ""
            category = getattr(getattr(match, "category", None), "id", "grammar") or "grammar"
            results.append({
                "type": "grammar", "category": f"languagetool:{category.lower()}",
                "rule": getattr(match, "rule_id", "LANGUAGETOOL"),
                "word": text[match.offset:match.offset + match.error_length],
                "original_text": text[match.offset:match.offset + match.error_length],
                "suggestion": suggestion, "suggestions": replacements[:5],
                "start": match.offset, "end": match.offset + match.error_length,
                "explanation": match.message,
                "confidence": 0.88 if suggestion else 0.65,
                "severity": "minor" if "PUNCTUATION" in category.upper() else "moderate",
            })
        return results
    except Exception:
        # Missing Java, unavailable local server, or failed first-time setup must
        # never make the app unavailable; the in-house checker remains active.
        return []
