"""Test NewsAPI scraper (Top Headlines, category=technology). Requires NEWSAPI_API_KEY."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.scrapers.newsapi_tech import scrape_newsapi_tech


def main():
    import argparse
    p = argparse.ArgumentParser(description="Test NewsAPI (Top Headlines, category=technology)")
    p.add_argument("-n", "--limit", type=int, default=10, help="Max articles")
    p.add_argument("--api-key", type=str, default=None, help="NewsAPI key (else NEWSAPI_API_KEY)")
    args = p.parse_args()
    print("Fetching NewsAPI (category=technology)...")
    try:
        articles = scrape_newsapi_tech(limit=args.limit, api_key=args.api_key)
    except ValueError as e:
        print("  Error:", e)
        print("  Put key in config/secrets.env, set NEWSAPI_API_KEY, or pass --api-key. Get a key at https://newsapi.org/")
        return
    print(f"  Got {len(articles)} articles\n")
    for i, a in enumerate(articles[:10], 1):
        print(f"  {i}. {a.headline}")
        print(f"     {a.timestamp} | {a.source} | {a.url[:55]}...")
    if len(articles) > 10:
        print(f"  ... and {len(articles) - 10} more")
    print("\nDone.")


if __name__ == "__main__":
    main()
