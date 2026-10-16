from unittest.mock import Mock

import pytest

from scamshield import config, pipeline
from scamshield.schemas import CheckResult, Evidence, Extracted, Message, Verdict


@pytest.fixture
def mocked_checks(monkeypatch):
    ext = Extracted(masked_text="Your account needs review before access continues today, please verify through the official app when you have time.")
    monkeypatch.setattr(pipeline.preprocess, "extract", Mock(return_value=ext))
    monkeypatch.setattr(pipeline.transformer, "score", Mock(return_value=0.8))
    monkeypatch.setattr(pipeline.transformer, "score_batch", Mock(side_effect=lambda texts: [0.5] * len(texts)))
    monkeypatch.setattr(pipeline.lstm, "score", Mock(return_value=0.7))
    monkeypatch.setattr(
        pipeline.rules,
        "run",
        Mock(return_value=CheckResult(name="rules", score=20, weight=0.2, status="ok")),
    )
    monkeypatch.setattr(
        pipeline.links,
        "check",
        Mock(return_value=CheckResult(name="links", score=0, weight=0.15, status="ok")),
    )
    monkeypatch.setattr(
        pipeline.sender,
        "check",
        Mock(return_value=CheckResult(name="sender", score=0, weight=0.1, status="ok")),
    )
    monkeypatch.setattr(pipeline.explain, "highlights", Mock(return_value=[{"text": "review"}]))
    return ext


def test_analyze_happy_path_builds_typed_verdict(mocked_checks):
    verdict = pipeline.analyze(Message(text="not printed", channel="sms"), True, set())
    assert isinstance(verdict, Verdict)
    assert verdict.score == 46
    assert verdict.category == "Suspicious"
    assert verdict.confidence == "high"
    assert verdict.scam_type == "Unclear"
    assert verdict.uncertain is False
    assert isinstance(verdict.model_agreement, float)
    assert isinstance(verdict.score, int)
    assert isinstance(verdict.category, str)
    assert isinstance(verdict.confidence, str)
    assert isinstance(verdict.confidence_note, str)
    assert isinstance(verdict.scam_type, str)
    assert isinstance(verdict.uncertain, bool)
    assert isinstance(verdict.highlights, list)
    assert isinstance(verdict.checks, dict)
    assert isinstance(verdict.actions, list)
    assert isinstance(verdict.report_text, str)
    assert all(check.status == "ok" for check in verdict.checks.values())
    assert verdict.checks["transformer"].score == 80
    assert verdict.checks["lstm"].score == 70
    assert verdict.actions
    assert verdict.report_text
    assert verdict.scan_id is None
    assert verdict.highlights == [{"text": "review"}]


def test_one_check_error_does_not_prevent_verdict(mocked_checks, monkeypatch):
    monkeypatch.setattr(pipeline.rules, "run", Mock(side_effect=RuntimeError("private detail")))
    verdict = pipeline.analyze(Message(text="not printed", channel="sms"), False, set())
    assert isinstance(verdict, Verdict)
    assert verdict.checks["rules"].status == "error"
    assert verdict.checks["rules"].weight == config.WEIGHTS["rules"]
    assert "private detail" not in verdict.checks["rules"].detail


@pytest.mark.parametrize("failed_model", ["transformer", "lstm"])
@pytest.mark.parametrize("failure", ["none", "raises"])
def test_missing_or_failed_model_is_passed_as_none(mocked_checks, monkeypatch, failed_model, failure):
    model = getattr(pipeline, failed_model)
    score = Mock(return_value=None) if failure == "none" else Mock(side_effect=RuntimeError("private detail"))
    monkeypatch.setattr(model, "score", score)
    fused = Mock(wraps=pipeline.scoring.fuse)
    monkeypatch.setattr(pipeline.scoring, "fuse", fused)

    verdict = pipeline.analyze(Message(text="not printed", channel="sms"), False, set())

    args = fused.call_args.args
    probability_index = 2 if failed_model == "transformer" else 1
    assert args[probability_index] is None
    assert verdict.confidence in {"medium", "low"}
    assert verdict.checks[failed_model].status in {"error", "not_checked"}
    if failed_model == "transformer":
        assert verdict.highlights == []


def test_link_reputation_override_produces_high_risk_verdict(mocked_checks, monkeypatch):
    evidence = Evidence(rule_id="REPUTATION_MALICIOUS", reason="malicious destination", severity=0.9)
    monkeypatch.setattr(
        pipeline.links,
        "check",
        Mock(return_value=CheckResult(name="links", score=90, weight=0.15, status="ok", evidence=[evidence])),
    )
    verdict = pipeline.analyze(Message(text="not printed", channel="sms"), True, set())
    assert verdict.score >= 80


def test_transformer_none_keeps_verdict_and_empty_highlights(mocked_checks, monkeypatch):
    monkeypatch.setattr(pipeline.transformer, "score", Mock(return_value=None))
    highlight_mock = Mock(side_effect=AssertionError("highlights should be skipped"))
    monkeypatch.setattr(pipeline.explain, "highlights", highlight_mock)

    verdict = pipeline.analyze(Message(text="not printed", channel="sms"), False, set())

    assert isinstance(verdict, Verdict)
    assert verdict.highlights == []
    highlight_mock.assert_not_called()


def test_explain_failure_keeps_verdict_and_empty_highlights(mocked_checks, monkeypatch):
    monkeypatch.setattr(pipeline.explain, "highlights", Mock(side_effect=RuntimeError("explain failed")))

    verdict = pipeline.analyze(Message(text="not printed", channel="sms"), False, set())

    assert isinstance(verdict, Verdict)
    assert verdict.highlights == []
    assert verdict.report_text


def test_models_receive_only_masked_text(monkeypatch):
    raw_text = "Call me at 9876543210 and use OTP 482913 to verify your account."
    message = Message(text=raw_text, channel="sms")
    monkeypatch.setattr(pipeline.transformer, "score", Mock(return_value=0.8))
    monkeypatch.setattr(pipeline.transformer, "score_batch", Mock(side_effect=lambda texts: [0.5] * len(texts)))
    monkeypatch.setattr(pipeline.lstm, "score", Mock(return_value=0.7))
    monkeypatch.setattr(pipeline.rules, "run", Mock(return_value=CheckResult(name="rules", score=0, weight=0.2, status="ok")))
    monkeypatch.setattr(pipeline.links, "check", Mock(return_value=CheckResult(name="links", score=0, weight=0.15, status="ok")))
    monkeypatch.setattr(pipeline.sender, "check", Mock(return_value=CheckResult(name="sender", score=0, weight=0.1, status="ok")))
    extracted = pipeline.preprocess.extract(message)
    monkeypatch.setattr(pipeline.preprocess, "extract", Mock(return_value=extracted))

    pipeline.analyze(message, False, set())

    for model in (pipeline.transformer, pipeline.lstm):
        received_texts = [call.args[0] for call in model.score.call_args_list]
        assert received_texts
        assert all("9876543210" not in text and "482913" not in text for text in received_texts)
        assert all(text == extracted.masked_text for text in received_texts)
    batch_texts = pipeline.transformer.score_batch.call_args.args[0]
    assert batch_texts
    assert all("9876543210" not in text and "482913" not in text for text in batch_texts)


def test_use_reputation_false_passes_through_unchanged(mocked_checks, monkeypatch):
    blocklist = {"https://blocked.example"}
    pipeline.analyze(Message(text="not printed", channel="sms"), False, blocklist)
    pipeline.links.check.assert_called_once_with(mocked_checks, False, blocklist)
