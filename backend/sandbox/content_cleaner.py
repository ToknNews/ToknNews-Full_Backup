import re, html

def clean_text(raw: str) -> str:
    """
    Removes HTML, URLs, &amp; entities, and excess whitespace.
    Keeps only readable English text for feed summaries.
    """
    if not raw:
        return ""

    # Decode HTML entities (&amp;, &lt;, etc.)
    s = html.unescape(raw)

    # Remove HTML tags like <p> or <a href=...>
    s = re.sub(r"<[^>]+>", " ", s)

    # Remove full URLs (https:// or http://)
    s = re.sub(r"https?://[^\s)]+", " ", s)

    # Remove links that start with www.
    s = re.sub(r"www\.[^\s)]+", " ", s)

    # Remove leftover HTML entities like &amp;
    s = re.sub(r"&[a-z]+;", " ", s)

    # Collapse multiple spaces into one
    s = re.sub(r"\s+", " ", s).strip()

    # Trim to first 1000 characters for safety
    return s[:1000]
