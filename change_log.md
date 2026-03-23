# Change log

## 2026-03-23 - base_data: AI-only matched rows

- **`base_data.jsonl`:** Built by matching all raw headlines, filtering to **`is_ai_related == True`**, deduping on **`(posted_at, url, ticker)`**, then sorting. Full rebuild each `scripts/base_data.py` run (no incremental append).

## 2026-03-23 - Rename raw aggregate to base_data

- **File:** `data/cleaned/headlines_master_orig.jsonl` → `data/cleaned/base_data.jsonl`.
- **Script:** `scripts/headlines_master_orig.py` → `scripts/base_data.py`.
- **Utils:** `RAW_MASTER_PATH` → `BASE_DATA_PATH` in `src/utils.py`.
- **CI:** `.github/workflows/headlines_master_orig.yml` → `base_data.yml` (workflow name: "Update base data").

## 2026-03-17 - Raw scrapes as daily CSV

- **Scraper output:** `save_raw_jsonl` replaced with `save_raw_daily_csv` in `src/scrapers/base.py`. Each run writes/merges `data/raw/headlines_YYYYMMDD.csv` (UTC date). If the file already exists, new rows are concatenated, deduped by `(headline, url)` (first row kept), sorted by `posted_at` then `headline`, then saved via a temp file + atomic replace.
- **Loaders:** `src/utils.py` adds `load_csv`, `load_headline_paths`, `iter_raw_headline_paths`; `get_latest_raw_path` considers both `headlines_*.csv` and legacy `headlines_*.jsonl`.
- **Pipeline:** `base_data.py` (formerly headlines master), `run_process.py`, and `matcher.py` use `load_headline_paths` / unified raw listing so legacy JSONL still aggregates until removed.
- **CI:** `.github/workflows/run-scrapers.yml` artifacts and `git add` target `data/raw/headlines_*.csv`.

## 2026-02-25 - Project Start
- **Scrapers:** Tried Bloomberg and Reuters scraping/RSS, but the sources either didn’t work or triggered a slider CAPTCHA. After undetected-chromedriver also failed, we stopped investing time in that approach and dropped Selenium entirely.
- **Sentiment strategy:** Dual approach documented: (1) **VADER** on headlines (and optionally snippets), score in [-1, 1]; (2) **LLM** via a single prompt (e.g. "Rate sentiment for this tech/AI headline from -1 to 1"), parse numeric score, same scale. Both outputs stored per headline so Hype Score and analysis can use either method and results can be compared.
- **Small-model comparison (sub-hypothesis):** Three target models for LLM sentiment, all run locally via **Ollama** (no API cost): **phi3** (Microsoft), **llama3.2:3b** (Meta), **deepseek-r1:1.5b** (DeepSeek). Goal: compare which small model is best at this sentiment task and how much they agree. Research rationale and pull commands documented in PLAN.md and README.md.
- **Free LLM options:** Ollama recommended as primary (local, no keys); optional free APIs (e.g. Google AI Studio / Gemini, Groq) documented for running without local compute.
- **Docs:** PLAN.md section 4 (Sentiment) expanded with dual backends, three-model targets, and sub-hypothesis. README.md updated with Sentiment section and small-model comparison. This change log updated.
- **.gitignore:** Fixed PLAN.md ignore (removed leading spaces so the pattern matches). Added comment "Planning (keep local only)". PLAN.md is now properly ignored; use `git rm --cached PLAN.md` and commit if it was already tracked.
- **GitHub Actions:** Added `.github/workflows/run-scrapers.yml`. Workflow runs all three scrapers (TechCrunch, NewsAPI Tech, Google News RSS) on a schedule or manually. Uses `NEWSAPI_API_KEY` from repo Secrets; writes `config/secrets.env` in the runner. Saves one combined, deduped file `data/raw/headlines_YYYYMMDD.jsonl` (date comes from the Python script at run time). Uploads that file as a run artifact; commits and pushes new or changed headlines to the repo so the remote stays up to date (pull locally to get new data).
- **Schedule:** Cron set to `0 15 * * *` (15:00 UTC = 9am Central in winter/CST; 10am Central during CDT). One run per day is enough to capture the prior day’s relevant news from the current feeds.

## 2026-02-26 - AI flag and entities

- **is_ai_related:** Testing through01_sentiment_scores.ipynb notebook. Wanted to gauge what were hitting as is_ai_related and whether it was correct
- **entities_global:** Expanded ai_buzz_entities with popular AI products/agents: ChatGPT, Copilot, Claude, Gemini, Grok, Perplexity, Midjourney, DALL-E, Sora, Cursor, Vertex AI, Bedrock, Watson, Bard, Llama, Phi, GPT-4/5, o1/o3, Claude Opus, etc.
- **data/processed → data/cleaned:** Output folder renamed; all processed and master files now live under `data/cleaned/`.
- **Raw master:** `scripts/headlines_master_orig.py` aggregates all `data/raw/headlines_*.jsonl` into `data/cleaned/headlines_master_orig.jsonl`. If the file exists, only new rows (by headline+url) are appended; otherwise it is created and deduped. No sentiment or matching—raw aggregation only.
- **Update headlines master workflow:** `.github/workflows/headlines_master_orig.yml` runs after "Run scrapers" completes successfully, waits 30 minutes, then runs `headlines_master_orig.py` and commits/pushes the updated master file. Cron set to `0 22 * * *` to run twice per day.
- **run_matching:** Matching is integrated into `run_process.py` (it calls `run_matching_to_rows` then adds sentiment). The standalone `scripts/run_matching.py` is optional—only needed if you want match-only output (`matched_*.jsonl`); the main pipeline is `run_process` → one `processed_*.jsonl`.


