"""Ollama LLM sentiment: prompt model for a number in [-1, 1], parse last number, clamp."""
import re
import time
from typing import Any

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_TIMEOUT = 60
DELAY_BETWEEN_CALLS_S = 0.5

# Senior Equity Research Analyst (AI sector) sentiment prompt; model replies with one number after "Score:"
# prompted off of ChatGPT
SENTIMENT_PROMPT = """### SYSTEM PROMPT ###
You are a Senior Equity Research Analyst specializing in the AI Sector.
Your task is to analyze the sentiment of a financial headline on a scale of [-1.0, 1.0].

SCORING CRITERIA:
- [-1.0 to -0.6]: Critical negative impact (e.g., massive fine, model failure, key partner loss).
- [-0.5 to -0.1]: Minor headwinds (e.g., supply chain delays, increased competition).
- [0.0]: Neutral/Routine corporate news.
- [0.1 to 0.5]: Incremental positives (e.g., routine software update, minor partnership).
- [0.6 to 1.0]: Major breakthroughs (e.g., AGI milestone, huge CapEx expansion, new chip lead).

### EXAMPLES ###
Headline: "FTC launches antitrust investigation into Microsoft's OpenAI partnership."
Score: -0.8

Headline: "Nvidia announces new Blackwell shipment delays due to server rack overheating."
Score: -0.5

Headline: "Apple integrates OpenAI's ChatGPT into iOS 18 with local processing."
Score: 0.7

Headline: "Meta releases Llama 4 with 10x efficiency gains over previous generation."
Score: 0.9

### TASK ###
{CONTEXT}Headline: "{HEADLINE}"
Score:

Response must be a single float value only. No prose."""


def _parse_sentiment_number(response_text: str) -> float | None:
    """Extract a number in [-1, 1] from response; take last match for reasoning models."""
    if not response_text or not response_text.strip():
        return None
    # Match integers or decimals, optional minus
    matches = re.findall(r"-?\d+\.?\d*", response_text.strip())
    if not matches:
        return None
    try:
        value = float(matches[-1])
        return max(-1.0, min(1.0, value))
    except (ValueError, TypeError):
        return None


def score_ollama(
    text: str,
    model: str,
    timeout: int = DEFAULT_TIMEOUT,
    delay_after_s: float = DELAY_BETWEEN_CALLS_S,
    context: str | None = None,
) -> float | None:
    """
    Send headline to Ollama, parse response for a number in [-1, 1].
    Uses temperature=0 for deterministic scoring. Optional context (e.g. from YAML) is prepended.
    Returns None on timeout, HTTP error, or parse failure.
    """
    if not text or not text.strip():
        return None
    context_block = f"Context: {context}\n\n" if (context and context.strip()) else ""
    prompt = SENTIMENT_PROMPT.format(CONTEXT=context_block, HEADLINE=text.strip())
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        response_text = data.get("response") or ""
        if delay_after_s > 0:
            time.sleep(delay_after_s)
        return _parse_sentiment_number(response_text)
    except (requests.RequestException, KeyError, TypeError):
        return None
