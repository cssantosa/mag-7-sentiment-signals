"""FinBERT sentiment: map finance polarity to score in [-1, 1]."""
from typing import Any

_tokenizer = None
_model = None
_id2label: dict[int, str] = {}


def _load_finbert() -> tuple[Any, Any]:
    """Lazy-load FinBERT model/tokenizer to avoid import cost at module import."""
    global _tokenizer, _model, _id2label
    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_name = "ProsusAI/finbert"
    _tokenizer = AutoTokenizer.from_pretrained(model_name)
    _model = AutoModelForSequenceClassification.from_pretrained(model_name)
    _id2label = {int(k): str(v).lower() for k, v in _model.config.id2label.items()}
    return _tokenizer, _model


def score_finbert(text: str) -> float:
    """
    Score finance text with FinBERT using probability(positive) - probability(negative).
    Returns value in [-1, 1]. Blank input -> 0.0.
    """
    if not (text and text.strip()):
        return 0.0

    tokenizer, model = _load_finbert()

    import torch

    encoded = tokenizer(
        text.strip(),
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )
    with torch.no_grad():
        logits = model(**encoded).logits
        probs = torch.softmax(logits, dim=1).squeeze(0).tolist()

    label_to_prob: dict[str, float] = {}
    for idx, prob in enumerate(probs):
        label = _id2label.get(idx, str(idx)).lower()
        label_to_prob[label] = float(prob)

    pos = label_to_prob.get("positive", 0.0)
    neg = label_to_prob.get("negative", 0.0)
    score = pos - neg
    return max(-1.0, min(1.0, float(score)))
