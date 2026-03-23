"""Convert legacy raw headline JSONL files to CSV under data/csv/raw/ (optional tooling).

Scrapers now write daily `data/raw/headlines_YYYYMMDD.csv` directly; use this only for old `headlines_*_*.jsonl` snapshots.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.utils import DATA_RAW, load_jsonl

CANONICAL_COLS = ["source", "fetched_at", "headline", "posted_at", "reporter", "url"]


def dataframe_from_rows(rows: list[dict]) -> pd.DataFrame:
    """Order columns: canonical schema first, then any extras (sorted)."""
    if not rows:
        return pd.DataFrame(columns=CANONICAL_COLS)
    df = pd.DataFrame(rows)
    ordered = [c for c in CANONICAL_COLS if c in df.columns]
    extras = sorted(c for c in df.columns if c not in CANONICAL_COLS)
    return df[ordered + extras]


def default_csv_path(in_path: Path) -> Path:
    out_dir = ROOT / "data" / "csv" / "raw"
    return (out_dir / in_path.name).with_suffix(".csv")


def convert_one(in_path: Path, out_path: Path) -> int:
    """Write one JSONL to CSV; return row count."""
    rows = load_jsonl(in_path)
    df = dataframe_from_rows(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows -> {out_path}")
    return len(df)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert headline JSONL file(s) to UTF-8 CSV."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=None,
        help="Path to one .jsonl file (one JSON object per line)",
    )
    parser.add_argument(
        "--all-raw",
        action="store_true",
        help="Convert every data/raw/headlines_*.jsonl to data/csv/raw/*.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (single-file mode only; default: data/csv/raw/<basename>.csv)",
    )
    args = parser.parse_args()

    if args.all_raw and args.input is not None:
        parser.error("Do not pass input path together with --all-raw")
    if args.all_raw and args.output is not None:
        parser.error("--output cannot be used with --all-raw")

    if args.all_raw:
        paths = sorted(DATA_RAW.glob("headlines_*.jsonl"))
        if not paths:
            print("No data/raw/headlines_*.jsonl files found.", file=sys.stderr)
            return 1
        total_rows = 0
        for in_path in paths:
            in_path = in_path.resolve()
            out_path = default_csv_path(in_path)
            total_rows += convert_one(in_path, out_path)
        print(f"Done: {len(paths)} file(s), {total_rows} total rows.")
        return 0

    if args.input is None:
        parser.error("Provide a JSONL path or use --all-raw")

    in_path = args.input.resolve()
    if not in_path.exists():
        print(f"Error: file not found: {in_path}", file=sys.stderr)
        return 1
    if not in_path.is_file():
        print(f"Error: not a file: {in_path}", file=sys.stderr)
        return 1

    out_path = (
        args.output.resolve()
        if args.output is not None
        else default_csv_path(in_path)
    )
    convert_one(in_path, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
