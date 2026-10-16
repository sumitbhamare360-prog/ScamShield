import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

_TOKENIZER = None
_MODEL = None
_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "scambert"))


def _get_model():
    global _TOKENIZER, _MODEL
    if _MODEL is None:
        if os.path.exists(_MODEL_PATH):
            load_src = _MODEL_PATH
        else:
            load_src = "Digvijay05/SCAMBERT"

        _TOKENIZER = AutoTokenizer.from_pretrained(load_src)
        _MODEL = AutoModelForSequenceClassification.from_pretrained(load_src)
        _MODEL.eval()
    return _TOKENIZER, _MODEL


def score(text: str) -> float:
    """Predict probability P(scam) in range [0, 1] using SCAMBERT.

    Label mapping: index 0 is Safe/Ham, index 1 is Scam/Spam.
    """
    if not text or not text.strip():
        return 0.0

    tokenizer, model = _get_model()
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=False
    )
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        # Index 1 is confirmed P(scam)
        scam_prob = probs[0, 1].item()

    return float(scam_prob)
