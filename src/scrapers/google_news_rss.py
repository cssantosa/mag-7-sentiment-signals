"""Google News artificial intelligence headlines via RSS (topic: Artificial intelligence)."""
from datetime import datetime

import feedparser

from .base import RawArticle, parse_feed_date

# Google News topic: Artificial intelligence (not general TECHNOLOGY)
GOOGLE_NEWS_AI_RSS = (
    "https://news.google.com/rss/topics/CAAqIAgKIhpDQkFTRFFvSEwyMHZNRzFyZWhJQ1pXNG9BQVAB?hl=en-US&gl=US&ceid=US:en"
)


def _parse_date(entry) -> str:
    """Get ISO timestamp from feed entry."""
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            if hasattr(val, "strip"):
                return parse_feed_date(val)
            if hasattr(val, "tm_year"):
                try:
                    dt = datetime(
                        val.tm_year, val.tm_mon, val.tm_mday,
                        val.tm_hour, val.tm_min, min(val.tm_sec, 59),
                    )
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, TypeError):
                    pass
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def scrape_google_news_tech(limit: int = 50) -> list[RawArticle]:
    """Fetch Google News Artificial intelligence topic RSS and return RawArticle list."""
    articles = []
    feed = feedparser.parse(
        GOOGLE_NEWS_AI_RSS,
        request_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"},
    )
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
        if "<" in summary:
            from bs4 import BeautifulSoup
            summary = BeautifulSoup(summary, "lxml").get_text(separator=" ").strip()[:500]
        ts = _parse_date(entry)
        source_name = "google_news_ai"
        src = entry.get("source")
        if src:
            source_name = (src.get("title") if isinstance(src, dict) else getattr(src, "title", None)) or source_name
        articles.append(
            RawArticle(
                url=link,
                headline=title,
                timestamp=ts,
                source=source_name,
                snippet=summary[:500] if summary else "",
                pipeline_source="Google News RSS",
            )
        )
    return articles
