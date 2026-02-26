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

- **`config/entities.yaml`** - Mag 7 tickers and **aliases** (including products/subsidiaries: e.g. Waymo, YouTube for GOOGL; Instagram, WhatsApp for META). AI buzz phrases/entities. **Partnerships** map (ticker -> list of AI partners); **partnership_entity_aliases** (e.g. OpenAI -> ChatGPT, Sam Altman, GPT-4; Qwen, DeepSeek, Ollama with model names). Partnership weight applies only when a headline mentions both the ticker (or its product) and one of that ticker's configured partners (or that partner's alias). Hype formula, bullwhip roles. Edit to add keywords or tickers.
- **NewsAPI (optional):** Put your API key in `config/secrets.env` (copy from `config/secrets.env.example`). Do not commit `secrets.env`; it is gitignored.

## Sources

Headlines come from three sources:

1. **TechCrunch** (RSS) - no API key required.
2. **NewsAPI Tech** (Top Headlines, category=technology) - requires API key in `config/secrets.env`.
3. **Google News** (RSS, artificial intelligence topic) - no API key required.

Test individual sources: `python scripts/test/test_google_news.py`, `python scripts/test/test_newsapi.py`. Run all three and save: `python scripts/run_all_scrapers.py`.

## Sentiment and small-model comparison (planned)

Sentiment will be scored in two ways for comparison: **VADER** (lexicon-based on headline/snippet, output in [-1, 1]) and **LLM** via **Ollama** (local, no API cost). Small-model comparison will use three target models to compare "which small model is best at this task":

- **phi3** (Microsoft)
- **llama3.2:3b** (Meta)
- **deepseek-r1:1.5b** (DeepSeek)

Pull with: `ollama pull phi3`, `ollama pull llama3.2:3b`, `ollama pull deepseek-r1:1.5b`. Results will be stored per headline and per method for agreement comparison and downstream Hype Score. See **PLAN.md** section 4 for design.

## Run scrapers

```bash
python scripts/run_all_scrapers.py
```

1. Scrapes TechCrunch, NewsAPI Tech, and Google News RSS; prints per-source counts (before and after dedup).
2. Deduplicates and writes to `data/raw/`:
   - `headlines_YYYYMMDD.jsonl` - combined, deduped; each line: source (pipeline), fetched_at, headline, posted_at, reporter, url

Matching, sentiment, Hype Score, and price analysis are planned; see PLAN.md.

## Phase 2 (planned)

Phase 2 (predictive model and backtest) is planned; see PLAN.md.

## Project layout

- `config/entities.yaml` - Mag 7, AI buzz, partnerships, etc.
- `config/secrets.env.example` - template for optional NewsAPI key
- `src/scrapers/` **(1. scrapers)** - TechCrunch, NewsAPI Tech, Google News RSS; base dedup/save to single JSONL
- `scripts/run_all_scrapers.py` - run all three scrapers and save outputs
- `scripts/test/` - test_google_news.py, test_newsapi.py
- `data/raw/` - scraped headlines (headlines_YYYYMMDD.jsonl only)

Additional modules (matching, sentiment, hype, prices, analysis) are planned; see PLAN.md.

See **PLAN.md** for hypothesis, architecture, and full pipeline design.
