import pytest
from scamshield.schemas import Extracted
from scamshield.rules import run

# 15 synthetic rule test cases
RULE_FIXTURES = [
    ("Share your OTP 482910 immediately", "OTP_REQUEST"),
    ("OTP batayein nahi to transaction fail ho jayega", "OTP_HINGLISH"),
    ("Your SIM card will be blocked within 24 hours", "URGENT_BLOCK"),
    ("Dear user, your KYC update is pending today", "KYC_UPDATE"),
    ("Turant verify karein warna services block", "TURANT_VERIFY_HINGLISH"),
    ("Aapka account band hone wala hai", "ACCOUNT_BAND_HINGLISH"),
    ("Approve collect request to receive bonus money", "UPI_COLLECT"),
    ("Congratulations you won a lucky draw prize of 50000", "PRIZE_CLAIM"),
    ("Customs courier fee required to release your package", "COURIER_FEE"),
    ("Part-time job earn daily 5000 rs like and subscribe", "JOB_FEE"),
    ("Guaranteed returns of 200% with zero risk", "GUARANTEED_RETURNS"),
    ("Free crypto airdrop tokens claim now", "CRYPTO_PROMO"),
    ("Notice from CBI crime branch regarding your case", "AUTHORITY_IMPERSONATION"),
    ("Digital arrest warrant issued against your name", "DIGITAL_ARREST"),
    ("Click bit.ly/claim-bonus to get gift", "SHORTENED_LINK"),
]


def test_empty_text_returns_not_checked():
    ext = Extracted(masked_text="", urls=[], phones=[], upi_ids=[], amounts=[])
    res = run(ext)
    assert res.status == "not_checked"
    assert res.score is None


@pytest.mark.parametrize("text,expected_rule_id", RULE_FIXTURES)
def test_individual_rules_fire(text, expected_rule_id):
    ext = Extracted(masked_text=text, urls=[], phones=[], upi_ids=[], amounts=[])
    res = run(ext)
    assert res.status == "ok"
    assert res.score > 0
    matched_ids = [ev.rule_id for ev in res.evidence]
    assert expected_rule_id in matched_ids


def test_combined_rule_score():
    # Multiple rules trigger combined score formula: 1 - prod(1 - sev)
    text = "Aapka account band ho jayega, turant verify karein and share your OTP"
    ext = Extracted(masked_text=text, urls=[], phones=[], upi_ids=[], amounts=[])
    res = run(ext)
    assert res.status == "ok"
    assert len(res.evidence) >= 2
    # Combined score should be higher than individual severities
    assert res.score >= 95.0


def test_clean_ham_message_zero_score():
    text = "Hey are we still meeting for dinner tonight at 8pm?"
    ext = Extracted(masked_text=text, urls=[], phones=[], upi_ids=[], amounts=[])
    res = run(ext)
    assert res.status == "ok"
    assert res.score == 0.0
    assert len(res.evidence) == 0
