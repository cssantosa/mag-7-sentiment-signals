# Mag 7 AI Sentiment Pipeline

- **Purpose 1:** Test whether AI-specific sentiment in news headlines predicts short-term price movements for the Magnificent 7 (NVDA, MSFT, AAPL, AMZN, GOOGL, META, TSLA).
- **Purpose 2:** Compare small local LLMs (phi3, llama3.2:3b, deepseek-r1:1.5b) on performance for sentiment analysis of those headlines.
- **Purpose 3 (tentative):** Test whether suppliers (e.g. NVDA) or consumers (e.g. META) lead in sentiment-return dynamics (bullwhip analysis).

Phase 1 of the pipeline is live: scrapers run to collect headlines, `run_process.py` applies matching and sentiment, and per-headline scores from VADER and three small LLMs are written to `data/cleaned/processed_*.jsonl` and explored in notebooks to compare backends and ticker-level sentiment patterns.

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
4. Writes **one** file: `data/cleaned/processed_<suffix>.jsonl` (no intermediate matched_ or sentiment_ files).

Additional details:

- Output columns currently include `sentiment_vader`, `sentiment_llm_phi3`, `sentiment_llm_llama3_2`, and `sentiment_llm_deepseek_r1`, all on the [-1, 1] scale.
- Matching uses the YAML configuration in `config/entities_global.yaml` and `config/relationships/*` to derive ticker/AI flags and injects that context into the LLM sentiment prompt.
- You can control which sentiment backends run via `--backends`, e.g. `python scripts/run_process.py --backends vader` for a fast VADER-only test.

Ensure Ollama is running with models pulled: `ollama pull phi3`, `ollama pull llama3.2:3b`, `ollama pull deepseek-r1:1.5b`. To run matching only (no sentiment), use `python scripts/run_matching.py`; it still writes `matched_*.jsonl` for backward compatibility.

## Run scrapers

```bash
python scripts/run_all_scrapers.py
```

1. Scrapes TechCrunch, NewsAPI Tech, and Google News RSS; prints per-source counts (before and after dedup).
2. Deduplicates and writes to `data/raw/`: `headlines_YYYYMMDD_HH.jsonl` (combined, deduped: source, fetched_at, headline, posted_at, reporter, url).
Then run `python scripts/run_process.py` to produce `data/cleaned/processed_<suffix>.jsonl`. Optionally run `python scripts/headlines_master_orig.py` to aggregate all raw files into `data/cleaned/headlines_master_orig.jsonl` (create or append new rows only). Notebook analysis currently focuses on sentiment patterns and model comparison; Hype Score and price analysis are planned; see PLAN.md.

## Analysis & notebooks

- **`notebooks/sentiment_analysis.ipynb`**
  - Loads `data/cleaned/processed_master_orig.jsonl` (or the latest `processed_*.jsonl`) into a Pandas DataFrame.
  - Computes ticker-level average sentiment across all headlines and an AI-related-only subset (`is_ai_related == True`).
  - Visualizes backends with heatmaps and grouped bar charts to compare VADER vs the three LLMs at the ticker level.
  - Includes a section that inspects DeepSeek-R1 versus other models (e.g., on TSLA and META) and prints raw DeepSeek-R1 responses for contrarian headlines to understand its reasoning.
  - Example grouped barplot (saved from the notebook) can be embedded by saving the figure and viewing it in the repo:

    ```python
    plt.tight_layout()
    plt.savefig("docs/ticker_sentiment_barplot.png", dpi=150)
    ```

    And in this README:

    `![Average sentiment per ticker and backend](docs/ticker_sentiment_barplot.png)`

- **`notebooks/sentiment_testing.ipynb`**
  - Earlier exploration and scratchpad for sentiment scoring and AI-flag tuning; useful for experiments but not required for running the main pipeline.

## LLM–VADER delta metrics

LLM–VADER deltas are simple per-headline spreads that measure how far each LLM moves away from the VADER baseline on the same [-1, 1] scale. In notebooks, variables such as:

- `phi3_minus_vader = sentiment_llm_phi3 - sentiment_vader`
- `llama_minus_vader = sentiment_llm_llama3_2 - sentiment_vader`
- `deepseek_minus_vader = sentiment_llm_deepseek_r1 - sentiment_vader`

are used to explore disagreement between models. Aggregating these deltas by ticker and/or time (e.g., mean and mean absolute spread per ticker) helps quantify disagreement and model behavior. VADER is treated as a baseline/control, and LLM deltas are used as:

- **Quality checks**: flagging headlines or tickers where LLMs strongly disagree with VADER or with each other.
- **Research features**: candidate inputs for future predictive models alongside raw sentiment scores.

Empirically, DeepSeek-R1 has shown more contrarian behavior on some names (e.g., TSLA and META); inspecting its raw responses in the notebook suggests this is due to different but coherent reasoning rather than a pipeline or parsing bug.

### Planned delta visualizations

Planned delta/spread visualizations include:

- **Per-ticker plots** of mean sentiment per backend alongside mean spread versus VADER.
- **Distribution plots** (histograms or violin plots) of delta values to quantify disagreement across headlines and tickers.
- **Time-series charts** of sentiment and deltas around notable events (once price data is wired in).

These views will support defining confidence regimes (for example, trusting signals more when VADER and LLMs agree in sign and the absolute spread is small) and selecting backends or ensembles for Phase 2 modeling and backtests.

## Next Steps
Looking into analyzing sentiment scores of VADER and the llms and once there's enough time data pulled from the workflow, I'll start looking into a predictive model

## Project layout

- `config/entities_global.yaml` - AI buzz phrases/entities; `config/relationships/<ticker>.yaml` - Mag 7 aliases, partnerships
- `config/secrets.env.example` - template for optional NewsAPI key
- `src/scrapers/` - TechCrunch, NewsAPI Tech, Google News RSS; base dedup/save to single JSONL
- `src/matching/` - match headlines to tickers and AI relevance (config-driven)
- `src/sentiment/` - VADER + Ollama sentiment; analyst prompt
- `src/utils.py` - shared JSONL and path helpers
- `scripts/run_all_scrapers.py` - run all three scrapers
- `scripts/run_process.py` - **raw -> one processed file** (match + sentiment)
- `scripts/headlines_master_orig.py` - aggregate all raw into data/cleaned/headlines_master_orig.jsonl (create or append)
- `scripts/run_matching.py` - matching only (writes matched_*.jsonl)
- `scripts/test/` - test_google_news.py, test_newsapi.py
- `data/raw/` - scraped headlines (headlines_*.jsonl)
- `data/cleaned/` - **processed_<suffix>.jsonl** (match + sentiment), **headlines_master_orig.jsonl** (aggregated raw, run `scripts/headlines_master_orig.py`)

Hype Score, prices, and analysis are planned; see PLAN.md.

See **PLAN.md** for hypothesis, architecture, and full pipeline design.
