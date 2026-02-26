"""Load entities_global.yaml and config/relationships/*.yaml for the matcher."""
from pathlib import Path
from typing import Any

import yaml


def _collect_strings(value: Any) -> list[str]:
    """Flatten a YAML value to a list of non-empty strings for matching."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_collect_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            if isinstance(v, (str, list)):
                out.extend(_collect_strings(v))
            elif isinstance(v, dict) and "aliases" in v:
                out.extend(_collect_strings(v["aliases"]))
            elif isinstance(v, dict) and "keywords" in v:
                out.extend(_collect_strings(v["keywords"]))
            elif isinstance(v, dict) and "name" in v:
                out.append(str(v["name"]).strip())
                out.extend(_collect_strings(v.get("aliases", v.get("keywords", []))))
        return out
    return []


def _get_ticker_from_meta(data: dict) -> str | None:
    """Get target_ticker from metadata or infer from filename."""
    meta = data.get("metadata") or {}
    ticker = meta.get("target_ticker")
    if ticker:
        return ticker.upper()
    return None


def _identity_keywords(identity: dict) -> list[str]:
    """All strings that imply this ticker from identity."""
    out = []
    if identity.get("company_name"):
        out.append(identity["company_name"].strip())
    out.extend(_collect_strings(identity.get("aliases", [])))
    out.extend(_collect_strings(identity.get("key_people", [])))
    return out


def _subsidiaries_keywords(subs: dict) -> list[str]:
    """Subsidiary names and their aliases."""
    out = []
    for name, val in (subs or {}).items():
        out.append(name.replace("_", " ").strip())
        if isinstance(val, dict):
            out.extend(_collect_strings(val.get("aliases", [])))
    return out


def _products_keywords(products: dict) -> list[str]:
    """Product names and their aliases."""
    out = []
    for name, val in (products or {}).items():
        out.append(name.replace("_", " ").strip())
        if isinstance(val, dict):
            out.extend(_collect_strings(val.get("aliases", [])))
    return out


def _keyword_contexts_from_section(section: dict, normalize_name: bool = True) -> dict[str, str]:
    """From products or subsidiaries, return dict keyword -> context for entries with context/catalyst."""
    out: dict[str, str] = {}
    for name, val in (section or {}).items():
        if not isinstance(val, dict):
            continue
        ctx = (val.get("context") or val.get("catalyst") or "").strip()
        if not ctx:
            continue
        key = name.replace("_", " ").strip() if normalize_name else name
        out[key] = ctx
        for alias in _collect_strings(val.get("aliases", [])):
            if alias:
                out[alias] = ctx
    return out


def _ecosystem_partner_keywords(ecosystem: dict, partner_keys: tuple[str, ...]) -> list[str]:
    """Names and aliases for partner-type keys (lab_partners, partners, infra_partners) only."""
    out = []
    for key in partner_keys:
        block = ecosystem.get(key)
        if not block:
            continue
        if isinstance(block, dict):
            for partner_name, partner_val in block.items():
                out.append(partner_name.replace("_", " ").strip())
                if isinstance(partner_val, dict):
                    out.extend(_collect_strings(partner_val.get("aliases", partner_val.get("keywords", []))))
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    out.append(str(item.get("name", "")).strip())
                    out.extend(_collect_strings(item.get("aliases", item.get("keywords", []))))
    return out


def _ecosystem_all_keywords(ecosystem: dict) -> list[str]:
    """All ecosystem names/aliases/keywords for association (partners + suppliers + competitors)."""
    out = []
    partner_keys = ("lab_partners", "partners", "infra_partners", "suppliers", "competitors")
    for key in partner_keys:
        block = ecosystem.get(key)
        if not block:
            continue
        if isinstance(block, dict):
            for partner_name, partner_val in block.items():
                out.append(partner_name.replace("_", " ").strip())
                if isinstance(partner_val, dict):
                    out.extend(_collect_strings(partner_val.get("aliases", partner_val.get("keywords", []))))
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    out.append(str(item.get("name", "")).strip())
                    out.extend(_collect_strings(item.get("aliases", item.get("keywords", []))))
    return out


def load_entities_global(path: Path) -> tuple[list[str], list[str]]:
    """Load entities_global.yaml; return (ai_buzz_phrases, ai_buzz_entities)."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    phrases = _collect_strings(data.get("ai_buzz_phrases", []))
    entities = _collect_strings(data.get("ai_buzz_entities", []))
    return (phrases, entities)


def load_relationship(path: Path) -> tuple[str | None, list[str], list[str], dict[str, str]]:
    """
    Load one relationship YAML.
    Returns (ticker, ticker_keywords, partner_keywords, keyword_contexts).
    - keyword_contexts: keyword -> context string for products/subsidiaries that have context/catalyst in YAML.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    ticker = _get_ticker_from_meta(data)
    if not ticker:
        return (None, [], [], {})

    ticker_kw = []
    ticker_kw.extend(_identity_keywords(data.get("identity") or {}))
    ticker_kw.extend(_subsidiaries_keywords(data.get("subsidiaries") or {}))
    ticker_kw.extend(_products_keywords(data.get("products") or {}))
    ticker_kw.extend(_ecosystem_all_keywords(data.get("ecosystem") or {}))

    partner_kw = _ecosystem_partner_keywords(
        data.get("ecosystem") or {},
        ("lab_partners", "partners", "infra_partners"),
    )

    keyword_contexts: dict[str, str] = {}
    keyword_contexts.update(_keyword_contexts_from_section(data.get("products")))
    keyword_contexts.update(_keyword_contexts_from_section(data.get("subsidiaries")))

    ticker_kw = list({s for s in ticker_kw if s})
    partner_kw = list({s for s in partner_kw if s})
    return (ticker, ticker_kw, partner_kw, keyword_contexts)


def load_matching_config(
    entities_path: Path | None = None,
    relationships_dir: Path | None = None,
) -> dict:
    """
    Load all config needed for matching.
    Returns dict with:
      - ai_buzz_phrases: list[str]
      - ai_buzz_entities: list[str]
      - tickers: dict[ticker -> { "ticker_keywords": list[str], "partner_keywords": list[str] }
    """
    from . import ENTITIES_GLOBAL_PATH, RELATIONSHIPS_DIR

    entities_path = entities_path or ENTITIES_GLOBAL_PATH
    relationships_dir = relationships_dir or RELATIONSHIPS_DIR

    ai_phrases, ai_entities = load_entities_global(entities_path)
    tickers = {}
    for path in sorted(relationships_dir.glob("*.yaml")):
        ticker, ticker_kw, partner_kw, keyword_contexts = load_relationship(path)
        if ticker:
            tickers[ticker] = {
                "ticker_keywords": ticker_kw,
                "partner_keywords": partner_kw,
                "keyword_contexts": keyword_contexts,
            }

    return {
        "ai_buzz_phrases": ai_phrases,
        "ai_buzz_entities": ai_entities,
        "tickers": tickers,
    }


def build_context_for_headline(headline_lower: str, tickers: list[str], config: dict) -> str | None:
    """
    Build a context string for the SLM from YAML: for each ticker, if the headline contains
    a keyword that has a context/catalyst in config, include it. Used to inject e.g.
    "This news relates to NVDA's primary 2026 catalyst" when Blackwell is mentioned.
    """
    headline_lower = headline_lower.strip().lower()
    parts: list[str] = []
    for ticker in tickers:
        data = config.get("tickers", {}).get(ticker, {})
        for keyword, ctx in (data.get("keyword_contexts") or {}).items():
            if not keyword or not ctx:
                continue
            kw_lower = keyword.lower()
            if kw_lower in headline_lower or (" " + kw_lower + " " in " " + headline_lower + " "):
                parts.append(ctx)
    if not parts:
        return None
    return "This news relates to " + "; ".join(parts) + "."
