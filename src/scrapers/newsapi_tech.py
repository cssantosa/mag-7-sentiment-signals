"""Technology / Mag-7 / AI headlines via NewsAPI.org. Query built from config entities."""
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .base import RawArticle

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RELATIONSHIPS_DIR = _PROJECT_ROOT / "config" / "relationships"
_GLOBAL_CONFIG_PATH = _PROJECT_ROOT / "config" / "entities_global.yaml"
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
    """
    Load Mag-7 tickers/aliases and AI buzz from the new YAML layout:

    - Tickers and aliases from config/relationships/<ticker>.yaml
    - AI buzz phrases/entities from config/entities_global.yaml
    """
    terms: list[str] = []

    # 1) Per-ticker relationships: tickers, aliases, products, subsidiaries.
    if _RELATIONSHIPS_DIR.exists():
        for path in _RELATIONSHIPS_DIR.glob("*.yaml"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except OSError:
                continue

            metadata = data.get("metadata") or {}
            identity = data.get("identity") or {}

            ticker = metadata.get("target_ticker") or identity.get("ticker")
            if ticker:
                terms.append(str(ticker))

            for alias in identity.get("aliases", []):
                terms.append(alias)

            for section in ("subsidiaries", "products"):
                for name, meta in (data.get(section) or {}).items():
                    terms.append(str(name))
                    for alias in (meta or {}).get("aliases", []):
                        terms.append(alias)

    # 2) Global AI buzzwords / entities.
    if _GLOBAL_CONFIG_PATH.exists():
        try:
            with open(_GLOBAL_CONFIG_PATH, encoding="utf-8") as f:
                g = yaml.safe_load(f) or {}
        except OSError:
            g = {}
        terms.extend(g.get("ai_buzz_phrases") or [])
        terms.extend(g.get("ai_buzz_entities") or [])

    # Fallback if config is missing or empty.
    if not terms:
        terms = ["AI", "artificial intelligence"]

    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
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
