from typing import Dict, List, Tuple

WEIGHTS: Dict[str, float] = {
    "transformer": 0.40,
    "rules": 0.20,
    "lstm": 0.15,
    "links": 0.15,
    "sender": 0.10,
}

# Score bands: (min_inclusive, max_exclusive, label)
# score < 30: Likely Safe
# 30 <= score < 55: Suspicious
# 55 <= score < 80: Likely Scam
# score >= 80: High-Risk Scam
BANDS: List[Tuple[float, float, str]] = [
    (0.0, 30.0, "Likely Safe"),
    (30.0, 55.0, "Suspicious"),
    (55.0, 80.0, "Likely Scam"),
    (80.0, 100.0, "High-Risk Scam"),
]

DISAGREE_THRESHOLD: float = 0.4

CHECK_NAMES: List[str] = [
    "transformer",
    "rules",
    "lstm",
    "links",
    "sender",
]
