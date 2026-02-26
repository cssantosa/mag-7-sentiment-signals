"""Match headlines to tickers and AI relevance; emit one row per (headline, ticker)."""
import json
import re
from pathlib import Path
from typing import Any

from .config_loader import load_matching_config
from src.utils import load_jsonl_paths


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _contains_keyword(text_lower: str, keyword: str) -> bool:
    """True if keyword appears in text (phrase or word-boundary for single tokens)."""
    k = keyword.lower().strip()
    if not k:
        return False
    if " " in k:
        return k in text_lower
    return bool(re.search(r"\b" + re.escape(k) + r"\b", text_lower))


def _is_ai_related(headline_lower: str, config: dict) -> bool:
    """Based solely on entities_global.yaml (ai_buzz_phrases + ai_buzz_entities)."""
    for phrase in config.get("ai_buzz_phrases", []):
        if _contains_keyword(headline_lower, phrase):
            return True
    for entity in config.get("ai_buzz_entities", []):
        if _contains_keyword(headline_lower, entity):
            return True
    return False


def _associated_tickers(headline_lower: str, config: dict) -> list[str]:
    """Tickers for which the headline matches at least one ticker keyword."""
    associated = []
    for ticker, data in config.get("tickers", {}).items():
        for kw in data.get("ticker_keywords", []):
            if _contains_keyword(headline_lower, kw):
                associated.append(ticker)
                break
    return associated


def _is_proxy_partnership(headline_lower: str, ticker: str, config: dict) -> bool:
    """True if headline mentions one of this ticker's partner keywords."""
    data = config.get("tickers", {}).get(ticker, {})
    for kw in data.get("partner_keywords", []):
        if _contains_keyword(headline_lower, kw):
            return True
    return False


def match_headline(row: dict, config: dict) -> list[dict]:
    """
    Given one raw headline row and loaded config, return list of output rows (one per ticker).
    row must have: headline, posted_at, fetched_at, source, reporter, url.
    """
    headline = row.get("headline", "")
    headline_lower = _normalize(headline)
    is_ai = _is_ai_related(headline_lower, config)
    tickers = _associated_tickers(headline_lower, config)
    if not tickers:
        return []

    out = []
    for ticker in tickers:
        is_partnership = _is_proxy_partnership(headline_lower, ticker, config)
        out.append({
            "posted_at": row.get("posted_at", ""),
            "fetched_at": row.get("fetched_at", ""),
            "headline": headline,
            "url": row.get("url", ""),
            "source": row.get("source", ""),
            "reporter": row.get("reporter", ""),
            "ticker": ticker,
            "is_ai_related": is_ai,
            "is_proxy_partnership": is_partnership,
        })
    return out


def run_matching_to_rows(
    raw_paths: list[Path],
    config: dict | None = None,
) -> list[dict[str, Any]]:
    """
    Read raw JSONL file(s), match each headline, return matched rows (no file write).
    Use this to chain match -> sentiment -> write one processed file.
    """
    if config is None:
        config = load_matching_config()
    raw_rows = load_jsonl_paths(raw_paths)
    matched = []
    for row in raw_rows:
        matched.extend(match_headline(row, config))
    return matched


def run_matching(
    raw_paths: list[Path],
    output_path: Path,
    config: dict | None = None,
) -> tuple[int, int]:
    """
    Read raw JSONL file(s), match each headline, write matched rows to output_path JSONL.
    Returns (headlines_read, rows_written).
    """
    if config is None:
        config = load_matching_config()
    raw_rows = load_jsonl_paths(raw_paths)
    matched = []
    for row in raw_rows:
        matched.extend(match_headline(row, config))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        for row in matched:
            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return (len(raw_rows), len(matched))
