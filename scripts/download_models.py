import os
import json
import urllib.request
import torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
SCAMBERT_DIR = os.path.join(MODELS_DIR, "scambert")
BILSTM_DIR = os.path.join(MODELS_DIR, "bilstm")


def download_scambert():
    print(f"Checking/Downloading SCAMBERT into {SCAMBERT_DIR}...")
    os.makedirs(SCAMBERT_DIR, exist_ok=True)
    # Download files using huggingface_hub
    repo_id = "Digvijay05/SCAMBERT"
    files = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json"]
    for f in files:
        target = os.path.join(SCAMBERT_DIR, f)
        if not os.path.exists(target):
            print(f"Downloading {f}...")
            hf_hub_download(repo_id=repo_id, filename=f, local_dir=SCAMBERT_DIR)
        else:
            print(f"Already present: {f}")

    # Verify loading
    print("Verifying SCAMBERT load...")
    tok = AutoTokenizer.from_pretrained(SCAMBERT_DIR)
    mod = AutoModelForSequenceClassification.from_pretrained(SCAMBERT_DIR)
    mod.eval()
    print("SCAMBERT loaded successfully!")


def download_bilstm():
    print(f"Checking/Downloading BiLSTM into {BILSTM_DIR}...")
    os.makedirs(BILSTM_DIR, exist_ok=True)
    repo_id = "St3w31/BiLSTMSpamClassifier"
    files = ["config.json", "BiLSTMClassifier.py", "BiLSTMClassifier.safetensors"]
    for f in files:
        target = os.path.join(BILSTM_DIR, f)
        if not os.path.exists(target):
            print(f"Downloading {f}...")
            hf_hub_download(repo_id=repo_id, filename=f, local_dir=BILSTM_DIR)
        else:
            print(f"Already present: {f}")

    print("Verifying BiLSTM load...")
    # Verify tokenizer (bert-base-uncased) and weights
    tok = AutoTokenizer.from_pretrained("bert-base-uncased")
    from safetensors.torch import load_file
    with open(os.path.join(BILSTM_DIR, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    import sys
    if BILSTM_DIR not in sys.path:
        sys.path.insert(0, BILSTM_DIR)
    from BiLSTMClassifier import BiLSTMClassifier

    model = BiLSTMClassifier(
        vocab_size=cfg.get("vocab_size", 30522),
        embedding_dim=cfg.get("embedding_dim", 128),
        hidden_size=cfg.get("hidden_size", 64),
        num_layers=cfg.get("num_layers", 5),
        dropout=cfg.get("dropout", 0.2),
    )
    weights = load_file(os.path.join(BILSTM_DIR, "BiLSTMClassifier.safetensors"))
    model.load_state_dict(weights)
    model.eval()
    print("BiLSTM loaded successfully!")


if __name__ == "__main__":
    download_scambert()
    download_bilstm()
