"""
Run full pipeline: raw headlines -> match -> sentiment -> one processed file.

Reads data/raw/headlines_*.jsonl (latest file by default), runs matching and sentiment
(VADER + phi3, llama3.2:3b, deepseek-r1:1.5b), writes data/processed/processed_<suffix>.jsonl.
No intermediate matched_ or sentiment_ files.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import (
    DATA_RAW,
    DATA_PROCESSED,
    get_latest_raw_path,
    load_jsonl_paths,
    processed_output_path,
    write_jsonl,
)
from src.matching import run_matching_to_rows
from src.sentiment import add_sentiment_to_rows

# Default: all backends. Set to ["vader"] for fast run without LLMs.
DEFAULT_BACKENDS = ["vader", "phi3", "llama3.2:3b", "deepseek-r1:1.5b"]


def main() -> None:
    argv = sys.argv[1:]
    backends = DEFAULT_BACKENDS
    if "--backends" in argv:
        i = argv.index("--backends")
        if i + 1 < len(argv):
            backends = [b.strip() for b in argv[i + 1].split(",") if b.strip()]
        argv = argv[:i] + argv[i + 2 :]
    raw_glob = argv[0] if argv else None

    if raw_glob:
        raw_paths = sorted(ROOT.glob(raw_glob))
        raw_paths = [p for p in raw_paths if p.is_file()]
        if not raw_paths:
            raw_paths = sorted(DATA_RAW.glob(Path(raw_glob).name))
    else:
        raw_path = get_latest_raw_path()
        if not raw_path:
            print("No data/raw/headlines_*.jsonl found. Run scrapers first.")
            sys.exit(1)
        raw_paths = [raw_path]
        print(f"Using latest raw file: {raw_path.name}")

    # Suffix from first raw file (e.g. headlines_20260226_15 -> 20260226_15)
    stem = raw_paths[0].stem
    suffix = stem.replace("headlines_", "", 1)
    output_path = processed_output_path(suffix)

    print(f"Sentiment backends: {', '.join(backends)}")
    if "vader" in backends and len(backends) == 1:
        print("  (VADER-only run; use no --backends for full LLM run.)")
    elif any(b != "vader" for b in backends):
        print("  (Ensure Ollama is running with phi3, llama3.2:3b, deepseek-r1:1.5b for LLM scores.)")

    raw_count = len(load_jsonl_paths(raw_paths))
    matched = run_matching_to_rows(raw_paths)
    full = add_sentiment_to_rows(matched, backends=backends)
    write_jsonl(full, output_path)

    print(f"Raw headlines read: {raw_count}")
    print(f"Matched rows:      {len(matched)}")
    print(f"Output:            {output_path}")
    print(f"Rows written:      {len(full)}")


if __name__ == "__main__":
    main()
