"""
Aggregate all data/raw/headlines_*.jsonl into data/cleaned/headlines_master_orig.jsonl.

- If headlines_master_orig.jsonl does not exist: create it from all raw files (deduped by headline+url).
- If it exists: append only new rows (headline, url) not already in the master.
No sentiment or matching; raw data only. Run after scrapers to keep master up to date.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import DATA_RAW, DATA_CLEANED, RAW_MASTER_PATH, load_jsonl, load_jsonl_paths, write_jsonl


def main() -> None:
    raw_paths = sorted(DATA_RAW.glob("headlines_*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not raw_paths:
        print("No data/raw/headlines_*.jsonl found. Run scrapers first.")
        sys.exit(1)

    all_raw = load_jsonl_paths(raw_paths)
    if not all_raw:
        print("No rows in raw files.")
        sys.exit(0)

    def key(r: dict) -> tuple:
        return (r.get("headline", ""), r.get("url", ""))

    if not RAW_MASTER_PATH.exists():
        seen: set = set()
        deduped = []
        for r in all_raw:
            k = key(r)
            if k in seen:
                continue
            seen.add(k)
            deduped.append(r)
        DATA_CLEANED.mkdir(parents=True, exist_ok=True)
        write_jsonl(deduped, RAW_MASTER_PATH)
        print(f"Created {RAW_MASTER_PATH.name} with {len(deduped)} rows (from {len(raw_paths)} raw files).")
        return

    existing = load_jsonl(RAW_MASTER_PATH)
    seen = {key(r) for r in existing}
    new_rows = [r for r in all_raw if key(r) not in seen]
    if not new_rows:
        print(f"Master up to date. No new rows from {len(raw_paths)} raw file(s).")
        return

    combined = existing + new_rows
    combined.sort(key=lambda r: (r.get("posted_at") or "", r.get("headline", "")))
    write_jsonl(combined, RAW_MASTER_PATH)
    print(f"Appended {len(new_rows)} new rows. Master now has {len(combined)} rows.")


if __name__ == "__main__":
    main()
