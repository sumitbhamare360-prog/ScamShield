import pytest

from scamshield import config
from scamshield.schemas import CheckResult, Evidence, Extracted
from scamshield.scoring import fuse


def check(name, score, weight=1.0, status="ok", evidence=None, detail=""):
    return CheckResult(
        name=name,
        score=score,
        weight=weight,
        status=status,
        evidence=evidence or [],
        detail=detail,
    )


@pytest.mark.parametrize(
    "score,expected",
    [
        (int(config.BANDS[0][1]) - 1, config.BANDS[0][2]),
        (int(config.BANDS[1][0]), config.BANDS[1][2]),
        (int(config.BANDS[1][1]) - 1, config.BANDS[1][2]),
        (int(config.BANDS[2][0]), config.BANDS[2][2]),
        (int(config.BANDS[2][1]) - 1, config.BANDS[2][2]),
        (int(config.BANDS[3][0]), config.BANDS[3][2]),
    ],
)
def test_band_boundaries_use_config(score, expected):
    assert fuse({"rules": check("rules", score)}, None, None)["category"] == expected


@pytest.mark.parametrize("rule_id", ["REPUTATION_MALICIOUS", "BLOCKLIST_HIT"])
def test_malicious_link_evidence_forces_score_to_80(rule_id):
    evidence = Evidence(rule_id=rule_id, reason="test flag", severity=0.5)
    result = fuse({"links": check("links", 2, evidence=[evidence])}, None, None)
    assert result["score"] == 80
    assert result["category"] == config.BANDS[-1][2]


def test_not_applicable_weight_is_removed_and_remaining_weights_renormalized():
    checks = {
        "rules": check("rules", 100, weight=0.25),
        "sender": check("sender", 0, weight=0.75, status="not_applicable"),
    }
    assert fuse(checks, None, None)["score"] == 100


def test_uncertain_only_above_configured_disagreement_threshold():
    difference = config.DISAGREE_THRESHOLD
    below = fuse({}, 0.2, 0.2 + difference - 0.01)
    above = fuse({}, 0.2, 0.2 + difference + 0.01)
    assert below["uncertain"] is False
    assert above["uncertain"] is True
    assert above["category"] == "Uncertain: verify manually"
    expected_score = round(
        (config.WEIGHTS["transformer"] * (0.2 + difference + 0.01) * 100
         + config.WEIGHTS["lstm"] * 0.2 * 100)
        / (config.WEIGHTS["transformer"] + config.WEIGHTS["lstm"])
    )
    assert above["score"] == expected_score


def test_confidence_uses_text_length_and_reputation_availability():
    full_text = Extracted(masked_text="This is a sufficiently long example message with more than fifteen words for confidence evaluation.")
    short_text = Extracted(masked_text="Please verify this now")
    high = fuse({}, 0.2, 0.21, ext=full_text)
    medium = fuse({}, 0.2, 0.21, ext=Extracted(masked_text="This is a short message"))
    low = fuse({"links": check("links", 1, detail="Reputation lookup failed/not_checked")}, 0.2, 0.21, ext=Extracted(masked_text=full_text.masked_text, urls=["https://example.test"]))
    very_low = fuse({}, 0.2, 0.21, ext=short_text)
    assert high["confidence"] == "high"
    assert medium["confidence"] == "medium"
    assert low["confidence"] == "low"
    assert very_low["confidence"] == "low"
