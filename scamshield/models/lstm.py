import os
import json
import torch
import torch.nn as nn
from transformers import BertTokenizer
from safetensors.torch import load_file

_TOKENIZER = None
_MODEL = None
_MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "bilstm"))

# Output mapping verified via four-sentence test (Phase 1, Open Issue 3):
# BiLSTM outputs a single scalar logit (Linear(hidden_size*2, 1)).
# Observed: Positive logits (>+6.0) produce high sigmoid probability (>0.998) on scam sentences;
# Negative logits (<-9.0) produce low sigmoid probability (<0.0002) on safe sentences.
# Therefore, positive logit under sigmoid indicates P(scam).
SCAM_OUTPUT_STRUCTURE: str = "scalar_sigmoid"


class BiLSTMClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int = 30522,
        embedding_dim: int = 128,
        hidden_size: int = 64,
        num_layers: int = 5,
        dropout: float = 0.2,
        **kwargs,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.fc = nn.Linear(hidden_size * 2, 1)

    def forward(self, x):
        x = self.embedding(x)
        outputs, (h_n, c_n) = self.lstm(x)
        h_fwd = h_n[-2, :, :]
        h_bwd = h_n[-1, :, :]
        h_final = torch.cat((h_fwd, h_bwd), dim=1)
        logits = self.fc(h_final)
        return logits


def _get_model():
    global _TOKENIZER, _MODEL
    if _MODEL is None:
        cfg_path = os.path.join(_MODEL_DIR, "config.json")
        weights_path = os.path.join(_MODEL_DIR, "BiLSTMClassifier.safetensors")

        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        else:
            cfg = {
                "vocab_size": 30522,
                "embedding_dim": 128,
                "hidden_size": 64,
                "num_layers": 5,
                "dropout": 0.2,
            }

        _MODEL = BiLSTMClassifier(
            vocab_size=cfg.get("vocab_size", 30522),
            embedding_dim=cfg.get("embedding_dim", 128),
            hidden_size=cfg.get("hidden_size", 64),
            num_layers=cfg.get("num_layers", 5),
            dropout=cfg.get("dropout", 0.2),
        )

        if os.path.exists(weights_path):
            state_dict = load_file(weights_path)
            _MODEL.load_state_dict(state_dict)

        _MODEL.eval()
        if os.path.exists(_MODEL_DIR) and os.path.exists(os.path.join(_MODEL_DIR, "tokenizer_config.json")):
            _TOKENIZER = BertTokenizer.from_pretrained(_MODEL_DIR)
        else:
            _TOKENIZER = BertTokenizer.from_pretrained("bert-base-uncased")

    return _TOKENIZER, _MODEL


def score(text: str) -> float:
    """Predict probability P(scam) in range [0, 1] using St3w31 BiLSTM model."""
    if not text or not text.strip():
        return 0.0

    tokenizer, model = _get_model()
    tokens = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=False
    )
    with torch.no_grad():
        logits = model(tokens["input_ids"])
        prob = torch.sigmoid(logits).item()

    return float(prob)
