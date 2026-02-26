"""Match headlines to Mag 7 tickers and AI relevance using config/relationships and config/entities_global."""

from pathlib import Path

from .config_loader import load_matching_config, build_context_for_headline
from .matcher import run_matching, run_matching_to_rows

__all__ = ["load_matching_config", "build_context_for_headline", "run_matching", "run_matching_to_rows"]

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
RELATIONSHIPS_DIR = CONFIG_DIR / "relationships"
ENTITIES_GLOBAL_PATH = CONFIG_DIR / "entities_global.yaml"
