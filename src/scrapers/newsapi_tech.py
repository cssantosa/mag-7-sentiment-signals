"""Technology / Mag-7 / AI headlines via NewsAPI.org. Query built from config entities."""
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .base import RawArticle

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config" / "entities.yaml"
_SECRETS_ENV = _PROJECT_ROOT / "config" / "secrets.env"


def _load_api_key_from_file() -> str | None:
    """Read NEWSAPI_API_KEY from config/secrets.env if present."""
    if not _SECRETS_ENV.exists():
        return None
    try:
        with open(_SECRETS_ENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("NEWSAPI_API_KEY=") and "your_key" not in line:
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def _load_search_terms() -> list[str]:
    """Load Mag-7 tickers/aliases and AI buzz from config for NewsAPI q= query."""
    if not _CONFIG_PATH.exists():
        return ["AI", "artificial intelligence"]
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    terms = []
    mag7 = data.get("mag7") or {}
    terms.extend(mag7.get("tickers") or [])
    for aliases in (mag7.get("aliases") or {}).values():
        terms.extend(aliases)
    terms.extend(data.get("ai_buzz_phrases") or [])
    terms.extend(data.get("ai_buzz_entities") or [])
    seen = set()
    out = []
    for t in terms:
        t = (t or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _build_query(terms: list[str], max_len: int = 500) -> str:
    """Build NewsAPI q= string: "term1" OR "term2" ... (phrases in quotes if space)."""
    if not terms:
        return "AI"
    def part(t: str) -> str:
        t = t.strip()
        if not t:
            return ""
        return f'"{t}"' if " " in t or "-" in t else t
    parts = []
    for t in terms:
        p = part(t)
        if not p:
            continue
        if len(" OR ".join(parts + [p])) > max_len:
            break
        parts.append(p)
    return " OR ".join(parts) if parts else "AI"


def _normalize_ts(published_at: str | None) -> str:
    """Normalize to ISO with Z."""
    if not (published_at or "").strip():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = (published_at or "").strip()
    if s.endswith("Z") or re.search(r"[+-]\d{2}:?\d{2}$", s):
        return s if s.endswith("Z") else s.replace(" ", "T") + "Z"
    if "T" in s:
        return s + "Z" if not s.endswith("Z") else s
    return s[:10] + "T12:00:00Z"


def scrape_newsapi_tech(
    limit: int = 50,
    *,
    api_key: str | None = None,
    country: str = "us",
) -> list[RawArticle]:
    """
    Fetch headlines from NewsAPI Top Headlines with category=technology only (no q).
    Requires country when using category (default: us). Key: NEWSAPI_API_KEY or api_key=.
    """
    key = api_key or os.environ.get("NEWSAPI_API_KEY") or _load_api_key_from_file()
    if not key:
        raise ValueError(
            "NewsAPI needs an API key. Put it in config/secrets.env, set NEWSAPI_API_KEY, or pass api_key=."
        )

    from newsapi import NewsApiClient

    client = NewsApiClient(api_key=key)
    all_articles: list[RawArticle] = []
    page = 1
    page_size = min(100, max(limit, 20))

    while True:
        resp = client.get_top_headlines(
            category="technology",
            country=country,
            page_size=page_size,
            page=page,
        )
        status = resp.get("status") if isinstance(resp, dict) else getattr(resp, "status", None)
        if status != "ok":
            break
        articles = (resp.get("articles") if isinstance(resp, dict) else getattr(resp, "articles", None)) or []
        if not articles:
            break
        for a in articles:
            def _g(k: str, default: str = ""):
                return (a.get(k) if isinstance(a, dict) else getattr(a, k, default)) or default
            title = _g("title").strip()
            if not title:
                continue
            url = _g("url").strip()
            if not url:
                continue
            desc = _g("description").strip()
            src = a.get("source") if isinstance(a, dict) else getattr(a, "source", None)
            source_name = "newsapi_tech"
            if src:
                source_name = (src.get("name") if isinstance(src, dict) else getattr(src, "name", None)) or source_name
                source_name = (source_name or "").strip() or "newsapi_tech"
            ts = _normalize_ts(_g("publishedAt"))
            all_articles.append(
                RawArticle(url=url, headline=title, timestamp=ts, source=source_name, snippet=desc, pipeline_source="NewsAPI Tech")
            )
            if len(all_articles) >= limit:
                break
        if len(all_articles) >= limit:
            break
        if len(articles) < page_size:
            break
        page += 1
        if page > 10:
            break

    return all_articles[:limit]
