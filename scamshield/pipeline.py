import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Set

from scamshield import advice, config, links, preprocess, rules, scoring, sender
from scamshield.models import explain, lstm, transformer
from scamshield.schemas import CheckResult, Message, Verdict


logger = logging.getLogger(__name__)


def analyze(msg: Message, use_reputation: bool, blocklist: Set[str]) -> Verdict:
    ext = preprocess.extract(msg)
    masked_text = ext.masked_text

    tasks = {
        "transformer": lambda: transformer.score(masked_text),
        "lstm": lambda: lstm.score(masked_text),
        "rules": lambda: rules.run(ext),
        "links": lambda: links.check(ext, use_reputation, blocklist),
        "sender": lambda: sender.check(ext),
    }
    results = {}
    errors = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {name: executor.submit(task) for name, task in tasks.items()}
        for name, future in futures.items():
            try:
                results[name] = future.result()
            except Exception as exc:
                errors[name] = type(exc).__name__
                logger.warning("check %s status %s", name, "error")

    transformer_p = results.get("transformer") if "transformer" not in errors else None
    lstm_p = results.get("lstm") if "lstm" not in errors else None

    checks = {}
    for name in ("rules", "links", "sender"):
        if name in errors:
            checks[name] = CheckResult(
                name=name,
                score=None,
                weight=config.WEIGHTS[name],
                status="error",
                detail=f"Check failed ({errors[name]}).",
            )
        else:
            checks[name] = results[name]

    for name, probability in (("transformer", transformer_p), ("lstm", lstm_p)):
        if name in errors:
            checks[name] = CheckResult(
                name=name,
                score=None,
                weight=config.WEIGHTS[name],
                status="error",
                detail=f"Model check failed ({errors[name]}).",
            )
        elif probability is None:
            checks[name] = CheckResult(
                name=name,
                score=None,
                weight=config.WEIGHTS[name],
                status="not_checked",
                detail="Model returned no probability.",
            )
        else:
            checks[name] = CheckResult(
                name=name,
                score=float(probability) * 100.0,
                weight=config.WEIGHTS[name],
                status="ok",
                detail="Model probability available.",
            )

    fused = scoring.fuse(checks, lstm_p, transformer_p, ext=ext)
    scam_type = advice.classify_scam_type(ext, checks)
    recommended_actions = advice.actions(fused["category"], scam_type, ext)

    highlights = []
    if transformer_p is not None:
        try:
            # Explain only masked_text; never pass the raw message to highlight generation.
            highlights = explain.highlights(
                transformer.score,
                masked_text,
                batch_score_fn=transformer.score_batch,
            )
        except Exception:
            highlights = []

    verdict = Verdict(
        score=fused["score"],
        category=fused["category"],
        confidence=fused["confidence"],
        confidence_note=fused["confidence_note"],
        scam_type=scam_type,
        uncertain=fused["uncertain"],
        model_agreement=fused["model_agreement"],
        highlights=highlights,
        checks=checks,
        actions=recommended_actions,
        report_text="",
        scan_id=None,
    )
    verdict.report_text = advice.report_text(verdict)
    return verdict
