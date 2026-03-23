"""Shared I/O and path helpers for the pipeline."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEANED = ROOT / "data" / "cleaned"
BASE_DATA_PATH = DATA_CLEANED / "base_data.jsonl"

# Raw scrape files: daily CSV (headlines_YYYYMMDD.csv); legacy per-run JSONL still readable.
RAW_HEADLINE_CSV_GLOB = "headlines_*.csv"
RAW_HEADLINE_JSONL_GLOB = "headlines_*.jsonl"


def load_csv(path: Path) -> list[dict]:
    """Load a UTF-8 CSV as list of dicts. Empty/missing file -> []."""
    if not path.exists() or path.stat().st_size == 0:
        return []
    df = pd.read_csv(
        path, encoding="utf-8", dtype=str, keep_default_na=False, na_filter=False
    )
    return df.to_dict(orient="records")


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file as list of dicts. Skips blank lines and invalid JSON."""
    rows = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def load_jsonl_paths(paths: list[Path]) -> list[dict]:
    """Load one or more JSONL files and return concatenated list of dicts."""
    out = []
    for p in paths:
        out.extend(load_jsonl(p))
    return out


def load_headline_paths(paths: list[Path]) -> list[dict]:
    """Load raw headline files: .csv via read_csv, .jsonl via load_jsonl."""
    out: list[dict] = []
    for p in paths:
        suf = p.suffix.lower()
        if suf == ".csv":
            out.extend(load_csv(p))
        elif suf == ".jsonl":
            out.extend(load_jsonl(p))
        else:
            raise ValueError(f"Unsupported raw headline format: {p}")
    return out


def iter_raw_headline_paths() -> list[Path]:
    """All data/raw/headlines_*.csv and legacy headlines_*.jsonl, oldest first by mtime."""
    csv_paths = list(DATA_RAW.glob(RAW_HEADLINE_CSV_GLOB))
    jsonl_paths = list(DATA_RAW.glob(RAW_HEADLINE_JSONL_GLOB))
    return sorted(csv_paths + jsonl_paths, key=lambda p: p.stat().st_mtime)


def write_jsonl(rows: list[dict], path: Path) -> None:
    """Write list of dicts to JSONL. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def get_latest_raw_path() -> Path | None:
    """Return path to most recently modified raw headline file (.csv or legacy .jsonl), or None."""
    files = iter_raw_headline_paths()
    return files[-1] if files else None


def processed_output_path(suffix: str) -> Path:
    """Return path for single processed file: data/cleaned/processed_<suffix>.jsonl."""
    DATA_CLEANED.mkdir(parents=True, exist_ok=True)
    return DATA_CLEANED / f"processed_{suffix}.jsonl"
