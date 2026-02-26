"""TechCrunch scraper via RSS feed."""
import time
from datetime import datetime, timezone

import feedparser

from .base import RawArticle, parse_feed_date

TECHCRUNCH_FEED = "https://techcrunch.com/feed/"


def _parse_date(entry) -> str:
    """Get ISO timestamp from feed entry."""
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            if hasattr(val, "strip"):
                return parse_feed_date(val)
            # feedparser can return time.struct_time
            if hasattr(val, "tm_year"):
                try:
                    dt = datetime(
                        val.tm_year, val.tm_mon, val.tm_mday,
                        val.tm_hour, val.tm_min, min(val.tm_sec, 59),
                    )
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, TypeError):
                    pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scrape_techcrunch(limit: int = 50) -> list[RawArticle]:
    """Fetch TechCrunch RSS and return RawArticle list."""
    articles = []
    feed = feedparser.parse(TECHCRUNCH_FEED)
    for i, entry in enumerate(feed.entries):
        if i >= limit:
            break
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            continue
        summary = entry.get("summary", "") or entry.get("description", "")
        if hasattr(summary, "strip"):
            summary = summary.strip()
        else:
            summary = ""
        # Strip HTML from summary
        if "<" in summary:
            from bs4 import BeautifulSoup
            summary = BeautifulSoup(summary, "lxml").get_text(separator=" ").strip()[:500]
        ts = _parse_date(entry)
        articles.append(
            RawArticle(
                url=link,
                headline=title,
                timestamp=ts,
                source="TechCrunch",
                snippet=summary[:500] if summary else "",
                pipeline_source="TechCrunch",
            )
        )
    return articles
