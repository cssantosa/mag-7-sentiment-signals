"""Sentiment scoring: VADER and Ollama LLM backends; pipeline to score matched headlines."""

from .vader_scorer import score_vader
from .ollama_scorer import score_ollama
from .pipeline import run_sentiment, add_sentiment_to_rows

__all__ = ["score_vader", "score_ollama", "run_sentiment", "add_sentiment_to_rows"]
