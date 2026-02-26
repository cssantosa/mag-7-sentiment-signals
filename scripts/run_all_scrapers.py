"""Run all 3 scrapers (TechCrunch, NewsAPI, Google News RSS) and save output to data/raw/."""
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.scrapers import scrape_all_sources

DATA_RAW = ROOT / "data" / "raw"


def main():
    print("Running all sources (TechCrunch, NewsAPI, Google News RSS)...")
    articles = scrape_all_sources(save=True)
    print(f"\nOutput saved to: {DATA_RAW}")
    print("  - headlines_YYYYMMDD.jsonl     (combined, deduped: source, fetched_at, headline, posted_at, reporter, url)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
