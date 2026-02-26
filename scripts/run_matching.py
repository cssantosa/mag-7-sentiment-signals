"""Run headline-to-ticker matching on raw JSONL and write data/processed/matched_*.jsonl."""
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

sys.path.insert(0, str(ROOT))
from src.matching import run_matching


def main() -> None:
    raw_glob = sys.argv[1] if len(sys.argv) > 1 else None
    if raw_glob:
        raw_paths = sorted(ROOT.glob(raw_glob))
        raw_paths = [p for p in raw_paths if p.is_file()]
        if not raw_paths:
            raw_paths = sorted(DATA_RAW.glob(Path(raw_glob).name))
    else:
        raw_paths = sorted(DATA_RAW.glob("headlines_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not raw_paths:
            print("No data/raw/headlines_*.jsonl files found.")
            sys.exit(1)
        raw_paths = raw_paths[:1]
        print(f"Using latest raw file: {raw_paths[0].name}")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    # Output name aligned with first input (e.g. headlines_20260226_15.jsonl -> matched_20260226_15.jsonl)
    stem = raw_paths[0].stem
    out_name = f"matched_{stem.replace('headlines_', '', 1)}.jsonl"
    output_path = DATA_PROCESSED / out_name

    headlines_read, rows_written = run_matching(raw_paths, output_path)
    print(f"Headlines read: {headlines_read}")
    print(f"Rows written:   {rows_written}")
    print(f"Output:         {output_path}")


if __name__ == "__main__":
    main()
