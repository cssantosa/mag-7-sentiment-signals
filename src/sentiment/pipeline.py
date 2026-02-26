"""Run sentiment on matched JSONL or rows in memory; score per unique headline, merge back."""
from pathlib import Path
from typing import Any

from .vader_scorer import score_vader
from .ollama_scorer import score_ollama

# Backend id -> (output key, scorer: "vader" | model name for Ollama)
BACKENDS: dict[str, tuple[str, str]] = {
    "vader": ("sentiment_vader", "vader"),
    "phi3": ("sentiment_llm_phi3", "phi3"),
    "llama3.2:3b": ("sentiment_llm_llama3_2", "llama3.2:3b"),
    "deepseek-r1:1.5b": ("sentiment_llm_deepseek_r1", "deepseek-r1:1.5b"),
}


def _score_unique_headlines(
    unique_headlines: list[str],
    backends: list[str],
    headline_to_tickers: dict[str, list[str]] | None = None,
    matching_config: dict | None = None,
) -> dict[str, dict[str, float | None]]:
    """Return map: headline -> { output_key: score or None }. Injects YAML context for LLM when provided."""
    from src.matching import build_context_for_headline

    results: dict[str, dict[str, float | None]] = {h: {} for h in unique_headlines}
    for backend_id in backends:
        if backend_id not in BACKENDS:
            continue
        out_key, scorer_spec = BACKENDS[backend_id]
        for headline in unique_headlines:
            if scorer_spec == "vader":
                score = score_vader(headline)
            else:
                context = None
                if headline_to_tickers and matching_config:
                    tickers = headline_to_tickers.get(headline, [])
                    context = build_context_for_headline(
                        headline.strip().lower(), tickers, matching_config
                    )
                score = score_ollama(headline, model=scorer_spec, context=context)
            results[headline][out_key] = score
    return results


def add_sentiment_to_rows(
    rows: list[dict[str, Any]],
    backends: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Add sentiment columns to matched rows in memory. Scores each unique headline once per backend.
    Uses temperature=0 and YAML context for LLM backends. Returns new list of rows with sentiment_* keys added.
    """
    if backends is None:
        backends = list(BACKENDS.keys())
    if not rows:
        return []
    unique_headlines = list(dict.fromkeys(r["headline"] for r in rows))
    headline_to_tickers: dict[str, list[str]] = {}
    for r in rows:
        h = r.get("headline", "")
        t = (r.get("ticker") or "").strip()
        if t:
            headline_to_tickers.setdefault(h, []).append(t)
    for h in list(headline_to_tickers):
        headline_to_tickers[h] = list(dict.fromkeys(headline_to_tickers[h]))
    from src.matching import load_matching_config

    matching_config = load_matching_config()
    headline_scores = _score_unique_headlines(
        unique_headlines, backends, headline_to_tickers, matching_config
    )
    out = []
    for row in rows:
        out_row = dict(row)
        h = row.get("headline", "")
        for _, (out_key, _) in BACKENDS.items():
            if out_key in headline_scores.get(h, {}):
                out_row[out_key] = headline_scores[h].get(out_key)
        out.append(out_row)
    return out


def run_sentiment(
    matched_path: Path,
    output_path: Path,
    backends: list[str] | None = None,
) -> tuple[int, int]:
    """
    Load matched JSONL from path, score each unique headline, merge scores onto rows, write sentiment JSONL.
    Returns (rows_read, rows_written). For single-file pipeline prefer run_process (raw -> processed).
    """
    from src.utils import load_jsonl, write_jsonl

    if backends is None:
        backends = list(BACKENDS.keys())
    rows = load_jsonl(matched_path)
    if not rows:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            pass
        return (0, 0)
    full = add_sentiment_to_rows(rows, backends)
    write_jsonl(full, output_path)
    return (len(rows), len(full))
