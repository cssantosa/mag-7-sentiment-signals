# Mag 7 AI Sentiment Pipeline

- **Purpose 1:** Test whether AI-specific sentiment in news headlines predicts short-term price movements for the Magnificent 7 (NVDA, MSFT, AAPL, AMZN, GOOGL, META, TSLA).
- **Purpose 2:** Compare small local LLMs (phi3, llama3.2:3b, deepseek-r1:1.5b) on performance for sentiment analysis of those headlines.
- **Purpose 3 (tentative):** Test whether suppliers (e.g. NVDA) or consumers (e.g. META) lead in sentiment-return dynamics (bullwhip analysis).


## Setup

**Option 1: Virtual environment (recommended)**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

**Option 2: System Python**

```bash
pip install -r requirements.txt
```

Dependencies (see `requirements.txt`): feedparser, requests, beautifulsoup4, lxml, pyyaml, pandas, numpy, yfinance, vaderSentiment, matplotlib, seaborn, scipy, xgboost, newsapi-python. Optional: LLM sentiment will use Ollama locally (no API key required for phi3, llama3.2:3b, deepseek-r1:1.5b).

## Config

- **`config/entities_global.yaml`** - AI buzz phrases/entities (global). **`config/relationships/<ticker>.yaml`** - Mag 7 tickers, aliases (including products/subsidiaries: Waymo, YouTube for GOOGL; Instagram, WhatsApp for META), partnerships (ticker -> AI partners and aliases). Partnership weight applies when a headline mentions a ticker's partner. Edit to add keywords or tickers.
- **NewsAPI (optional):** Put your API key in `config/secrets.env` (copy from `config/secrets.env.example`). Do not commit `secrets.env`; it is gitignored.

## Sources

Headlines come from three sources:

1. **TechCrunch** (RSS) - no API key required.
2. **NewsAPI Tech** (Top Headlines, category=technology) - requires API key in `config/secrets.env`.
3. **Google News** (RSS, artificial intelligence topic) - no API key required.

Test individual sources: `python scripts/test/test_google_news.py`, `python scripts/test/test_newsapi.py`. Run all three and save: `python scripts/run_all_scrapers.py`.

## Process: match + sentiment (one file)

One pipeline turns raw headlines into a single processed file with matching and sentiment:

```bash
python scripts/run_process.py
```

1. Reads the latest `data/raw/headlines_*.jsonl`.
2. Runs **matching** (ticker, is_ai_related, is_proxy_partnership) using `config/relationships/*` and `config/entities_global.yaml`.
3. Runs **sentiment**: **VADER** plus Ollama LLMs (**phi3**, **llama3.2:3b**, **deepseek-r1:1.5b**) with the Senior Equity Research Analyst prompt.
4. Writes **one** file: `data/processed/processed_<suffix>.jsonl` (no intermediate matched_ or sentiment_ files).

Ensure Ollama is running with models pulled: `ollama pull phi3`, `ollama pull llama3.2:3b`, `ollama pull deepseek-r1:1.5b`. To run matching only (no sentiment), use `python scripts/run_matching.py`; it still writes `matched_*.jsonl` for backward compatibility.

## Run scrapers

```bash
python scripts/run_all_scrapers.py
```

1. Scrapes TechCrunch, NewsAPI Tech, and Google News RSS; prints per-source counts (before and after dedup).
2. Deduplicates and writes to `data/raw/`: `headlines_YYYYMMDD_HH.jsonl` (combined, deduped: source, fetched_at, headline, posted_at, reporter, url).

Then run `python scripts/run_process.py` to produce `data/processed/processed_<suffix>.jsonl`. Hype Score and price analysis are planned; see PLAN.md.

## Phase 2 (planned)

Phase 2 (predictive model and backtest) is planned; see PLAN.md.

## Project layout

- `config/entities_global.yaml` - AI buzz phrases/entities; `config/relationships/<ticker>.yaml` - Mag 7 aliases, partnerships
- `config/secrets.env.example` - template for optional NewsAPI key
- `src/scrapers/` - TechCrunch, NewsAPI Tech, Google News RSS; base dedup/save to single JSONL
- `src/matching/` - match headlines to tickers and AI relevance (config-driven)
- `src/sentiment/` - VADER + Ollama sentiment; analyst prompt
- `src/utils.py` - shared JSONL and path helpers
- `scripts/run_all_scrapers.py` - run all three scrapers
- `scripts/run_process.py` - **raw -> one processed file** (match + sentiment)
- `scripts/run_matching.py` - matching only (writes matched_*.jsonl)
- `scripts/test/` - test_google_news.py, test_newsapi.py
- `data/raw/` - scraped headlines (headlines_*.jsonl)
- `data/processed/` - **processed_<suffix>.jsonl** (match + sentiment in one file)

Hype Score, prices, and analysis are planned; see PLAN.md.

See **PLAN.md** for hypothesis, architecture, and full pipeline design.
