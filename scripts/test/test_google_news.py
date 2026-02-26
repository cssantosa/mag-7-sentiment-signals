"""Run only the Google News artificial intelligence RSS scraper."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scrapers.google_news_rss import scrape_google_news_tech


def main():
    import argparse
    p = argparse.ArgumentParser(description="Test Google News AI (artificial intelligence) RSS")
    p.add_argument("-n", "--limit", type=int, default=15, help="Max articles (default 15)")
    args = p.parse_args()

    print("Fetching Google News artificial intelligence RSS...")
    articles = scrape_google_news_tech(limit=args.limit)
    print(f"  Got {len(articles)} articles\n")

    for i, a in enumerate(articles[:10], 1):
        print(f"  {i}. {a.headline}")
        print(f"     {a.timestamp} | {a.source} | {a.url[:60]}...")
    if len(articles) > 10:
        print(f"  ... and {len(articles) - 10} more")
    print("\nDone.")


if __name__ == "__main__":
    main()
