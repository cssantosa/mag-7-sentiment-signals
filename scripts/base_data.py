"""
Build data/cleaned/base_data.jsonl from all raw headline files.

Pipeline:
1. Load data/raw/headlines_*.csv (and legacy *.jsonl).
2. Run ticker + AI matching (same as run_process).
3. Keep rows where is_ai_related is True.
4. Dedupe by (posted_at, url, ticker), first row kept.
5. Sort by posted_at, ticker, url — overwrite base_data.jsonl.

Run after scrapers (or via CI). Full rebuild each run so config changes stay consistent.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.matching import run_matching_to_rows
from src.utils import BASE_DATA_PATH, DATA_CLEANED, iter_raw_headline_paths, write_jsonl


def _row_key(r: dict) -> tuple:
    return (r.get("posted_at", ""), r.get("url", ""), r.get("ticker", ""))


def main() -> None:
    raw_paths = iter_raw_headline_paths()
    if not raw_paths:
        print("No data/raw/headlines_*.csv or headlines_*.jsonl found. Run scrapers first.")
        sys.exit(1)

    matched = run_matching_to_rows(raw_paths)
    ai_rows = [r for r in matched if r.get("is_ai_related") is True]

    seen: set[tuple] = set()
    deduped: list[dict] = []
    for r in ai_rows:
        k = _row_key(r)
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)

    deduped.sort(key=lambda r: _row_key(r))

    DATA_CLEANED.mkdir(parents=True, exist_ok=True)
    write_jsonl(deduped, BASE_DATA_PATH)

    print(
        f"Wrote {BASE_DATA_PATH.name}: {len(matched)} matched rows -> "
        f"{len(ai_rows)} is_ai_related -> {len(deduped)} after (posted_at, url, ticker) dedupe "
        f"({len(raw_paths)} raw file(s))."
    )


if __name__ == "__main__":
    main()
