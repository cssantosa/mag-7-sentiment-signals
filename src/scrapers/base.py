"""Base scraper: fetch, parse, timestamp extraction, rate limiting, dedup, save daily CSV."""
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

DATA_RAW = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

RAW_ROW_COLUMNS = ["source", "fetched_at", "headline", "posted_at", "reporter", "url"]


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


def save_raw_daily_csv(articles: list[RawArticle], suffix: str = "") -> Path:
    """
    Append-merge into data/raw/headlines_YYYYMMDD[suffix].csv (UTC calendar day).
    Schema: source, fetched_at, headline, posted_at, reporter, url.
    If the file exists, read it, concat new rows, dedupe by (headline, url) keeping first,
    sort by posted_at then headline, then atomically overwrite.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    fetched_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    path = DATA_RAW / f"headlines_{date_str}{suffix}.csv"

    new_rows = [
        {
            "source": a.pipeline_source or "unknown",
            "fetched_at": fetched_at,
            "headline": a.headline,
            "posted_at": a.timestamp,
            "reporter": a.source,
            "url": a.url,
        }
        for a in articles
    ]
    new_df = pd.DataFrame(new_rows, columns=RAW_ROW_COLUMNS)

    if not new_rows and path.exists():
        return path

    if path.exists() and path.stat().st_size > 0:
        old_df = pd.read_csv(
            path, encoding="utf-8", dtype=str, keep_default_na=False, na_filter=False
        )
        for col in RAW_ROW_COLUMNS:
            if col not in old_df.columns:
                old_df[col] = ""
        old_df = old_df[RAW_ROW_COLUMNS]
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["headline", "url"], keep="first")
        combined = combined.sort_values(
            by=["posted_at", "headline"], kind="mergesort"
        ).reset_index(drop=True)
    else:
        combined = new_df

    tmp_path = path.parent / f"{path.name}.tmp"
    combined.to_csv(tmp_path, index=False, encoding="utf-8")
    tmp_path.replace(path)
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
        save_raw_daily_csv(all_articles)
    print(f"  Before dedup: TechCrunch {n_tc}, NewsAPI {n_newsapi}, Google News {n_google}  |  After dedup: {len(all_articles)}")
    return all_articles
