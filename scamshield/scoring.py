from typing import Any, Dict, Optional

from scamshield import config
from scamshield.schemas import CheckResult, Extracted


def fuse(
    checks: Dict[str, CheckResult],
    lstm_p: Optional[float],
    transformer_p: Optional[float],
    ext: Optional[Extracted] = None,
) -> Dict[str, Any]:
    """Fuse available check scores and model probabilities into a verdict summary."""
    components = []
    for check in checks.values():
        if check.status != "ok" or check.score is None:
            continue
        name = check.name.lower()
        if name in ("lstm", "transformer"):
            continue
        components.append((float(check.weight), float(check.score)))

    if transformer_p is not None:
        components.append((float(config.WEIGHTS.get("transformer", 0.0)), transformer_p * 100.0))
    if lstm_p is not None:
        components.append((float(config.WEIGHTS.get("lstm", 0.0)), lstm_p * 100.0))

    total_weight = sum(weight for weight, _ in components if weight > 0)
    if total_weight:
        raw_score = sum(weight * score for weight, score in components if weight > 0) / total_weight
    else:
        raw_score = 0.0

    override_rules = {"REPUTATION_MALICIOUS", "BLOCKLIST_HIT"}
    if any(evidence.rule_id in override_rules for check in checks.values() for evidence in check.evidence):
        raw_score = max(raw_score, 80.0)

    score = int(round(max(0.0, min(100.0, raw_score))))
    category = next(
        (label for lower, upper, label in config.BANDS if lower <= score < upper),
        config.BANDS[-1][2],
    )

    models_ran = lstm_p is not None and transformer_p is not None
    disagreement = abs(lstm_p - transformer_p) if models_ran else None
    uncertain = disagreement is not None and disagreement > config.DISAGREE_THRESHOLD
    if uncertain:
        category = "Uncertain: verify manually"
    model_agreement = round(1.0 - disagreement, 3) if disagreement is not None else None

    text = ext.masked_text if ext is not None else ""
    word_count = len(text.split())
    very_short = ext is not None and word_count <= 4
    link_check = next((c for c in checks.values() if c.name.lower() == "links"), None)
    reputation_unchecked = bool(
        link_check
        and (
            link_check.status == "not_checked"
            or "not_checked" in link_check.detail.lower()
        )
    )
    links_present = bool(ext and ext.urls)

    if uncertain or very_short or (links_present and reputation_unchecked):
        confidence = "low"
        confidence_note = "Confidence is low because the models disagree or the available message and link checks are limited."
    elif not models_ran or word_count < 15:
        confidence = "medium"
        confidence_note = "Confidence is medium because a model result is missing or the message is short."
    else:
        confidence = "high"
        confidence_note = "Confidence is high because both models agree and the message has enough text."

    return {
        "score": score,
        "category": category,
        "confidence": confidence,
        "confidence_note": confidence_note,
        "uncertain": uncertain,
        "model_agreement": model_agreement,
    }
