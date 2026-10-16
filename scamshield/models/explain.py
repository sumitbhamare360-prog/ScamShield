import re
from typing import Callable, List, Dict, Any


def highlights(score_fn: Callable[[str], float], text: str) -> List[Dict[str, Any]]:
    """Word-level perturbation explainer.

    Splits text into words, removes each word one at a time, and measures the score drop.
    Weight = baseline_score - perturbed_score.
    Returns up to the top 8 words with weight > 0.05, as dicts with:
    - text: str (the word)
    - start: int (character start offset in original text)
    - end: int (character end offset in original text)
    - weight: float
    """
    if not text or not text.strip():
        return []

    baseline_score = score_fn(text)
    if baseline_score <= 0.0:
        return []

    # Find word tokens and their character spans
    word_matches = list(re.finditer(r"\S+", text))
    if not word_matches:
        return []

    drops = []
    for match in word_matches:
        start, end = match.start(), match.end()
        word = match.group(0)

        # Build text without this word
        left = text[:start].rstrip()
        right = text[end:].lstrip()
        if left and right:
            perturbed_text = f"{left} {right}"
        else:
            perturbed_text = left or right

        perturbed_score = score_fn(perturbed_text)
        drop = baseline_score - perturbed_score

        if drop > 0.05:
            drops.append({
                "text": word,
                "start": start,
                "end": end,
                "weight": round(float(drop), 4)
            })

    # Sort descending by weight, take top 8
    drops.sort(key=lambda x: x["weight"], reverse=True)
    return drops[:8]
