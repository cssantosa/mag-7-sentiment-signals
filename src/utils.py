"""Shared I/O and path helpers for the pipeline."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"


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


def write_jsonl(rows: list[dict], path: Path) -> None:
    """Write list of dicts to JSONL. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def get_latest_raw_path() -> Path | None:
    """Return path to most recently modified data/raw/headlines_*.jsonl, or None."""
    files = sorted(DATA_RAW.glob("headlines_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def processed_output_path(suffix: str) -> Path:
    """Return path for single processed file: data/processed/processed_<suffix>.jsonl."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED / f"processed_{suffix}.jsonl"
