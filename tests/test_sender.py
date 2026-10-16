import pytest
from scamshield.schemas import Extracted
from scamshield.sender import check


def test_sender_not_applicable_when_no_sender_info():
    ext = Extracted(masked_text="Some message", sender_domain=None, display_name=None)
    res = check(ext)
    assert res.name == "sender"
    assert res.status == "not_applicable"
    assert res.score is None


def test_sender_suspicious_tld():
    ext = Extracted(masked_text="", sender_domain="alerts-service.xyz", display_name="Support")
    res = check(ext)
    assert res.status == "ok"
    assert any(e.rule_id == "SENDER_SUSPICIOUS_TLD" for e in res.evidence)
    assert res.score > 0


def test_freemail_bank_impersonation():
    ext = Extracted(
        masked_text="",
        sender_domain="gmail.com",
        display_name="HDFC Bank Customer Support"
    )
    res = check(ext)
    assert res.status == "ok"
    assert any(e.rule_id == "FREEMAIL_BANK_IMPERSONATION" for e in res.evidence)
    assert res.score >= 85.0


def test_display_name_brand_mismatch():
    ext = Extracted(
        masked_text="",
        sender_domain="random-marketing-firm.com",
        display_name="SBI Card Services"
    )
    res = check(ext)
    assert res.status == "ok"
    assert any(e.rule_id == "DISPLAY_NAME_BRAND_MISMATCH" for e in res.evidence)


def test_lookalike_sender_domain():
    ext = Extracted(
        masked_text="",
        sender_domain="icici-verify-notice.com",
        display_name="Verification Desk"
    )
    res = check(ext)
    assert res.status == "ok"
    assert any(e.rule_id == "LOOKALIKE_SENDER_DOMAIN" for e in res.evidence)


def test_legitimate_official_bank_sender():
    ext = Extracted(
        masked_text="",
        sender_domain="hdfcbank.com",
        display_name="HDFC Bank"
    )
    res = check(ext)
    assert res.status == "ok"
    assert res.score == 0.0
    assert len(res.evidence) == 0
