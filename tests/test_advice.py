import pytest

from scamshield.advice import actions, classify_scam_type, report_text
from scamshield.schemas import CheckResult, Evidence, Extracted, Verdict


def rule_check(rule_id):
    return CheckResult(
        name="rules",
        score=80,
        weight=0.2,
        status="ok",
        evidence=[Evidence(rule_id=rule_id, reason="matched", severity=0.8)],
    )


@pytest.mark.parametrize(
    "rule_id,expected",
    [
        ("OTP_REQUEST", "OTP fraud"),
        ("KYC_UPDATE", "Fake KYC or bank alert"),
        ("PRIZE_CLAIM", "Lottery or prize"),
        ("JOB_FEE", "Job offer"),
        ("COURIER_FEE", "Courier or parcel"),
        ("UPI_COLLECT", "UPI payment request"),
        ("CRYPTO_PROMO", "Investment or crypto"),
        ("AUTHORITY_IMPERSONATION", "Impersonation"),
    ],
)
def test_each_scam_type_is_reachable_from_rule_fixture(rule_id, expected):
    assert classify_scam_type(Extracted(masked_text="ordinary message"), {"rules": rule_check(rule_id)}) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Please share your OTP immediately", "OTP fraud"),
        ("Your KYC is pending, update your Aadhaar", "Fake KYC or bank alert"),
        ("You won a lottery prize", "Lottery or prize"),
        ("Work from home job offer", "Job offer"),
        ("Your parcel courier needs a delivery fee", "Courier or parcel"),
        ("Approve the UPI collect request", "UPI payment request"),
        ("Invest in bitcoin with guaranteed returns", "Investment or crypto"),
        ("Police issued a digital arrest warrant", "Impersonation"),
        ("Can we meet for lunch tomorrow?", "Unclear"),
    ],
)
def test_keyword_scam_type_fallback(text, expected):
    assert classify_scam_type(Extracted(masked_text=text), {}) == expected


@pytest.mark.parametrize(
    "scam_type,requires_secret,requires_report",
    [
        ("OTP fraud", True, True),
        ("Fake KYC or bank alert", True, True),
        ("Lottery or prize", True, True),
        ("Job offer", True, True),
        ("Courier or parcel", True, True),
        ("UPI payment request", True, True),
        ("Investment or crypto", True, True),
        ("Impersonation", True, True),
        ("Unclear", False, False),
    ],
)
def test_actions_have_three_or_four_steps_and_required_advice(scam_type, requires_secret, requires_report):
    result = actions("Suspicious", scam_type, Extracted(masked_text=""))
    assert 3 <= len(result) <= 4
    assert ("Never share your OTP, UPI PIN, or passwords" in result) is requires_secret
    assert ("Report at 1930 or cybercrime.gov.in" in result) is requires_report


def test_likely_safe_advice_appends_required_note():
    result = actions("Likely Safe", "Unclear", Extracted(masked_text=""))
    assert len(result) == 4
    assert result[-1] == "Safe does not mean guaranteed safe. Still avoid links and payment requests."


def test_report_text_uses_safe_verdict_fields_and_omits_raw_phone_and_otp():
    verdict = Verdict(
        score=90,
        category="High-Risk Scam",
        confidence="high",
        confidence_note="Message included phone 9876543210 and OTP 482913.",
        scam_type="OTP fraud",
        uncertain=False,
        highlights=[{"text": "9876543210 482913"}],
        checks={"rules": rule_check("OTP_REQUEST")},
        actions=["Call 9876543210", "OTP 482913"],
        report_text="Raw source had phone 9876543210 and OTP 482913.",
    )
    output = report_text(verdict)
    assert len(output.splitlines()) <= 6
    assert "9876543210" not in output
    assert "482913" not in output
    assert "OTP fraud" in output


def test_report_text_falls_back_to_safe_category_and_unclear_scam_type():
    verdict = Verdict(
        score=50,
        category="Unknown category",
        confidence="medium",
        confidence_note="",
        scam_type="Unknown type",
        uncertain=False,
        report_text="",
    )
    output = report_text(verdict)
    assert "Category: Uncertain: verify manually" in output
    assert "Scam type: Unclear" in output
