"""Base scraper: fetch, parse, timestamp extraction, rate limiting, dedup, save to JSONL."""
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_RAW = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)


@dataclass
class RawArticle:
    url: str
    headline: str
    timestamp: str  # ISO format
    source: str  # reporter/outlet name (e.g. TechCrunch, The Verge)
    snippet: str = ""
    pipeline_source: str = ""  # pipeline source: TechCrunch, NewsAPI Tech, Google News RSS

    def to_dict(self):
        return asdict(self)


def _normalize_headline(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")
    return url


def deduplicate(articles: list[RawArticle]) -> list[RawArticle]:
    """Drop duplicates by (reporter, date, canonical headline)."""
    seen = set()
    out = []
    for a in articles:
        date = a.timestamp[:10] if len(a.timestamp) >= 10 else a.timestamp
        key = (a.source, date, _normalize_headline(a.headline))
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def save_raw_jsonl(articles: list[RawArticle], suffix: str = "") -> Path:
    """Save to data/raw/headlines_YYYYMMDD_HH[suffix].jsonl. Schema: source, fetched_at, headline, posted_at, reporter, url (no snippet). One file per run (hour in UTC) for two runs per day."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H")
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = f"headlines_{date_str}{suffix}.jsonl"
    path = DATA_RAW / name
    with open(path, "w", encoding="utf-8") as f:
        for a in articles:
            row = {
                "source": a.pipeline_source or "unknown",
                "fetched_at": fetched_at,
                "headline": a.headline,
                "posted_at": a.timestamp,
                "reporter": a.source,
                "url": a.url,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def fetch_html(url: str, delay_seconds: float = 1.0, timeout: int = 15) -> str:
    """GET URL and return text. Respects a short delay to avoid hammering."""
    time.sleep(delay_seconds)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def parse_feed_date(date_str: str) -> str:
    """Convert feed date string to ISO format for storage."""
    if not date_str or not hasattr(date_str, "strip"):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    s = date_str.strip()
    s_clean = re.sub(r"\s*[+-]\d{4}$", "", re.sub(r"\s*GMT$", "", s))
    for fmt in (
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s_clean.strip(), fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            continue
    try:
        dt = datetime.strptime(s_clean[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        pass
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def scrape_all_sources(save: bool = True, limit_per_source: int = 100) -> list[RawArticle]:
    """Run all configured scrapers, dedupe, optionally save. Returns combined list."""
    from .techcrunch import scrape_techcrunch
    from .newsapi_tech import scrape_newsapi_tech
    from .google_news_rss import scrape_google_news_tech
    all_articles = []
    tc = scrape_techcrunch(limit=limit_per_source)
    all_articles.extend(tc)
    time.sleep(1.0)
    try:
        newsapi = scrape_newsapi_tech(limit=limit_per_source)
    except ValueError:
        newsapi = []
    all_articles.extend(newsapi)
    time.sleep(1.0)
    google_news = scrape_google_news_tech(limit=limit_per_source)
    all_articles.extend(google_news)
    n_tc, n_newsapi, n_google = len(tc), len(newsapi), len(google_news)
    all_articles = deduplicate(all_articles)
    if save:
        save_raw_jsonl(all_articles)
    print(f"  Before dedup: TechCrunch {n_tc}, NewsAPI {n_newsapi}, Google News {n_google}  |  After dedup: {len(all_articles)}")
    return all_articles
