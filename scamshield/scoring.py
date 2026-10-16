from typing import Dict, Any
from scamshield.schemas import CheckResult


def fuse(checks: Dict[str, CheckResult], lstm_p: float, transformer_p: float) -> Dict[str, Any]:
    # keys: score, category, confidence, confidence_note, uncertain, model_agreement
    raise NotImplementedError
