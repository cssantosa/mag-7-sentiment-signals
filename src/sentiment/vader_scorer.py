"""VADER sentiment: compound score on headline, clamped to [-1, 1]."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def score_vader(text: str) -> float:
    """Score text with VADER compound; return value in [-1, 1]."""
    if not (text or text.strip()):
        return 0.0
    out = _analyzer.polarity_scores(text.strip())
    compound = out.get("compound", 0.0)
    return max(-1.0, min(1.0, float(compound)))

def score_vader(text: str) -> float:
    """Utilizes VADER sentiment analysis to score text on a scale of [-1, 1]"""
    
