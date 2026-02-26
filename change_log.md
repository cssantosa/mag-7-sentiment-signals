# Change log

## 2026-02-26 - Project Start
- **Scrapers:** Tried Bloomberg and Reuters scraping/RSS, but the sources either didn’t work or triggered a slider CAPTCHA. After undetected-chromedriver also failed, we stopped investing time in that approach and dropped Selenium entirely.
- **Sentiment strategy:** Dual approach documented: (1) **VADER** on headlines (and optionally snippets), score in [-1, 1]; (2) **LLM** via a single prompt (e.g. "Rate sentiment for this tech/AI headline from -1 to 1"), parse numeric score, same scale. Both outputs stored per headline so Hype Score and analysis can use either method and results can be compared.
- **Small-model comparison (sub-hypothesis):** Three target models for LLM sentiment, all run locally via **Ollama** (no API cost): **phi3** (Microsoft), **llama3.2:3b** (Meta), **deepseek-r1:1.5b** (DeepSeek). Goal: compare which small model is best at this sentiment task and how much they agree. Research rationale and pull commands documented in PLAN.md and README.md.
- **Free LLM options:** Ollama recommended as primary (local, no keys); optional free APIs (e.g. Google AI Studio / Gemini, Groq) documented for running without local compute.
- **Docs:** PLAN.md section 4 (Sentiment) expanded with dual backends, three-model targets, and sub-hypothesis. README.md updated with Sentiment section and small-model comparison. This change log updated.




