"""
Merge data/raw/headlines_YYYYMMDD_HH.csv (and similar) into headlines_YYYYMMDD.csv.

- Groups files by UTC calendar date parsed from the filename.
- Combines rows, dedupes by (headline, url) keeping first occurrence, sorts like the scraper.
- Deletes per-run CSVs after a successful write; leaves already-daily files untouched if alone.

Usage:
  python scripts/merge_raw_csv_to_daily.py
  python scripts/merge_raw_csv_to_daily.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import DATA_RAW, load_csv

RAW_ROW_COLUMNS = ["source", "fetched_at", "headline", "posted_at", "reporter", "url"]


def date_key_from_stem(stem: str) -> str | None:
    """headlines_20260317 or headlines_20260317_15 -> 20260317."""
    if not stem.startswith("headlines_"):
        return None
    rest = stem[len("headlines_") :]
    m = re.match(r"^(\d{8})(?:_\d+)?$", rest)
    return m.group(1) if m else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge per-run raw CSVs into daily filenames.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only; do not write or delete files.",
    )
    args = parser.parse_args()

    csv_files = sorted(DATA_RAW.glob("headlines_*.csv"))
    if not csv_files:
        print("No headlines_*.csv in data/raw.")
        return 0

    by_date: dict[str, list[Path]] = defaultdict(list)
    for p in csv_files:
        dk = date_key_from_stem(p.stem)
        if dk is None:
            print(f"Skip (unrecognized name): {p.name}", file=sys.stderr)
            continue
        by_date[dk].append(p)

    for date_str in sorted(by_date.keys()):
        paths = sorted(by_date[date_str], key=lambda p: p.name)
        out_path = DATA_RAW / f"headlines_{date_str}.csv"
        only_daily = len(paths) == 1 and paths[0].name == out_path.name
        if only_daily:
            print(f"{date_str}: already daily-only ({out_path.name}), skip.")
            continue

        rows: list[dict] = []
        for p in paths:
            rows.extend(load_csv(p))
        if not rows:
            print(f"{date_str}: no rows from {len(paths)} file(s), skip.")
            continue

        df = pd.DataFrame(rows)
        for col in RAW_ROW_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[RAW_ROW_COLUMNS]
        df = df.drop_duplicates(subset=["headline", "url"], keep="first")
        df = df.sort_values(by=["posted_at", "headline"], kind="mergesort").reset_index(
            drop=True
        )

        to_delete = [p for p in paths if p.resolve() != out_path.resolve()]

        print(
            f"{date_str}: merge {len(paths)} file(s) -> {out_path.name} "
            f"({len(df)} rows); delete {len(to_delete)} old file(s)."
        )
        if args.dry_run:
            continue

        tmp_path = out_path.parent / f"{out_path.name}.tmp"
        df.to_csv(tmp_path, index=False, encoding="utf-8")
        tmp_path.replace(out_path)
        for p in to_delete:
            p.unlink(missing_ok=True)

        # If out_path was merged from only non-daily files, to_delete is all paths; good
        # If out_path was in paths, it wasn't in to_delete; we replaced via tmp; good

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
