"""
Run sentiment pipeline from base data to one processed file.

Reads data/cleaned/base_data.csv by default (or a custom CSV path),
runs sentiment (FinBERT + phi3, llama3.2:3b, deepseek-r1:1.5b),
writes data/cleaned/processed_<suffix>.jsonl.
"""
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import (
    DATA_CLEANED,
    load_csv,
    processed_output_path,
    write_jsonl,
)
from src.sentiment import add_sentiment_to_rows

# Default: all backends. Set to ["finbert"] for fast run without LLMs.
DEFAULT_BACKENDS = ["finbert", "phi3", "llama3.2:3b", "deepseek-r1:1.5b"]


def main() -> None:
    argv = sys.argv[1:]
    backends = DEFAULT_BACKENDS
    if "--backends" in argv:
        i = argv.index("--backends")
        if i + 1 < len(argv):
            backends = [b.strip() for b in argv[i + 1].split(",") if b.strip()]
        argv = argv[:i] + argv[i + 2 :]
    input_csv = argv[0] if argv else str(DATA_CLEANED / "base_data.csv")
    input_path = Path(input_csv)
    if not input_path.is_absolute():
        input_path = (ROOT / input_path).resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        print("Run scripts/base_data.py first, or pass a valid CSV path.")
        sys.exit(1)

    stem = input_path.stem
    suffix = stem.replace("headlines_", "", 1)
    output_path = processed_output_path(suffix)
    print(f"Using input file: {input_path.name}")

    print(f"Sentiment backends: {', '.join(backends)}")
    if "finbert" in backends and len(backends) == 1:
        print("  (FinBERT-only run; use no --backends for full LLM run.)")
    elif any(b != "finbert" for b in backends):
        print("  (Ensure Ollama is running with phi3, llama3.2:3b, deepseek-r1:1.5b for LLM scores.)")

    start_time = time.time()
    base_rows = load_csv(input_path)
    full = add_sentiment_to_rows(base_rows, backends=backends)
    write_jsonl(full, output_path)

    print(f"Rows read: {len(base_rows)}")
    print(f"Output: {output_path}")
    print(f"Rows written: {len(full)}")
    print(f"Time taken: {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
