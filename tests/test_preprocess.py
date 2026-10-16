import pytest
from scamshield.schemas import Message
from scamshield.preprocess import mask, extract

SYNTHETIC_FIXTURES = [
    # 1. OTP sharing with standard OTP keyword
    {
        "text": "Your login OTP is 482910. Do not share with anyone.",
        "expect_masked_otp": True,
        "raw_secret": "482910"
    },
    # 2. OTP in Hinglish format
    {
        "text": "Dear customer, OTP 9531 hai aapka verification code. Please confirm.",
        "expect_masked_otp": True,
        "raw_secret": "9531"
    },
    # 3. Indian mobile phone starting with 9
    {
        "text": "Call our officer immediately at 9876543210 for account help.",
        "expect_masked_phone": True,
        "raw_secret": "9876543210",
        "last2": "10"
    },
    # 4. Indian mobile phone with +91 prefix
    {
        "text": "Emergency contact: +91 8765432109 regarding your parcel.",
        "expect_masked_phone": True,
        "raw_secret": "8765432109",
        "last2": "09"
    },
    # 5. Bank Account number with a/c keyword
    {
        "text": "Amount credited to A/C 50100234567891 successfully.",
        "expect_masked_acc": True,
        "raw_secret": "50100234567891",
        "last2": "91"
    },
    # 6. Standalone long bank account number
    {
        "text": "Transfer money to account 12345678901234 before 5pm.",
        "expect_masked_acc": True,
        "raw_secret": "12345678901234",
        "last2": "34"
    },
    # 7. Credit/Debit Card number (16 digits formatted)
    {
        "text": "Verify your card 4111 2222 3333 4444 to avoid deactivation.",
        "expect_masked_card": True,
        "raw_secret": "4111 2222 3333 4444",
        "last2": "44"
    },
    # 8. Obfuscated URL with [.] and hxxp
    {
        "text": "Visit hxxps://secure-banking[.]com/login to update details.",
        "raw_url": "secure-banking[.]com",
        "normalized_url": "https://secure-banking.com/login"
    },
    # 9. UPI ID extraction with standard PSP handle
    {
        "text": "Pay penalty of Rs 500 to payment@okhdfcbank right now.",
        "expected_upi": "payment@okhdfcbank",
        "expected_amount": "500"
    },
    # 10. UPI ID with Paytm handle
    {
        "text": "Claim refund by sending request to merchant@paytm immediately.",
        "expected_upi": "merchant@paytm"
    },
    # 11. Amount with Rupee symbol ₹
    {
        "text": "You won ₹ 25,000 lottery cash prize today!",
        "expected_amount": "25,000"
    },
    # 12. Amount with INR
    {
        "text": "Electricity bill due: INR 3,450.50 pending disconnection.",
        "expected_amount": "3,450.50"
    },
    # 13. Email channel sender parsing
    {
        "sender": "HDFC Security Team <alerts@hdfc-verify.net>",
        "expected_name": "HDFC Security Team",
        "expected_domain": "hdfc-verify.net"
    },
    # 14. Plain email address as sender
    {
        "sender": "support@service-update.org",
        "expected_domain": "service-update.org"
    },
    # 15. Combined multi-entity message
    {
        "text": "Share OTP 746123 to verify A/C 9876543210987 and mobile 9123456780 for ₹ 1,500 cashback.",
        "multi": True
    }
]


def test_mask_otp():
    res = mask(SYNTHETIC_FIXTURES[0]["text"])
    assert SYNTHETIC_FIXTURES[0]["raw_secret"] not in res
    assert "[OTP:" in res


def test_mask_otp_hinglish():
    res = mask(SYNTHETIC_FIXTURES[1]["text"])
    assert SYNTHETIC_FIXTURES[1]["raw_secret"] not in res
    assert "[OTP:" in res


def test_mask_phone_standard():
    fix = SYNTHETIC_FIXTURES[2]
    res = mask(fix["text"])
    assert fix["raw_secret"] not in res
    assert f"{fix['last2']}]" in res


def test_mask_phone_prefix():
    fix = SYNTHETIC_FIXTURES[3]
    res = mask(fix["text"])
    assert fix["raw_secret"] not in res
    assert f"{fix['last2']}]" in res


def test_mask_account_number():
    fix = SYNTHETIC_FIXTURES[4]
    res = mask(fix["text"])
    assert fix["raw_secret"] not in res
    assert f"{fix['last2']}]" in res


def test_mask_standalone_account():
    fix = SYNTHETIC_FIXTURES[5]
    res = mask(fix["text"])
    assert fix["raw_secret"] not in res
    assert f"{fix['last2']}]" in res


def test_mask_card_number():
    fix = SYNTHETIC_FIXTURES[6]
    res = mask(fix["text"])
    assert "4111 2222 3333 4444" not in res
    assert f"{fix['last2']}]" in res


def test_extract_obfuscated_url():
    msg = Message(text=SYNTHETIC_FIXTURES[7]["text"], channel="sms")
    ext = extract(msg)
    assert SYNTHETIC_FIXTURES[7]["normalized_url"] in ext.urls


def test_extract_upi_and_amount_rs():
    msg = Message(text=SYNTHETIC_FIXTURES[8]["text"], channel="sms")
    ext = extract(msg)
    assert SYNTHETIC_FIXTURES[8]["expected_upi"] in ext.upi_ids
    assert SYNTHETIC_FIXTURES[8]["expected_amount"] in ext.amounts


def test_extract_upi_paytm():
    msg = Message(text=SYNTHETIC_FIXTURES[9]["text"], channel="whatsapp")
    ext = extract(msg)
    assert SYNTHETIC_FIXTURES[9]["expected_upi"] in ext.upi_ids


def test_extract_amount_symbol():
    msg = Message(text=SYNTHETIC_FIXTURES[10]["text"], channel="sms")
    ext = extract(msg)
    assert SYNTHETIC_FIXTURES[10]["expected_amount"] in ext.amounts


def test_extract_amount_inr():
    msg = Message(text=SYNTHETIC_FIXTURES[11]["text"], channel="sms")
    ext = extract(msg)
    assert SYNTHETIC_FIXTURES[11]["expected_amount"] in ext.amounts


def test_extract_email_sender_with_display_name():
    msg = Message(text="Your account is on hold", channel="email", sender=SYNTHETIC_FIXTURES[12]["sender"])
    ext = extract(msg)
    assert ext.display_name == SYNTHETIC_FIXTURES[12]["expected_name"]
    assert ext.sender_domain == SYNTHETIC_FIXTURES[12]["expected_domain"]


def test_extract_plain_email_sender():
    msg = Message(text="Notice", channel="email", sender=SYNTHETIC_FIXTURES[13]["sender"])
    ext = extract(msg)
    assert ext.sender_domain == SYNTHETIC_FIXTURES[13]["expected_domain"]


def test_mask_combined_entities():
    fix = SYNTHETIC_FIXTURES[14]
    res = mask(fix["text"])
    assert "746123" not in res
    assert "9876543210987" not in res
    assert "9123456780" not in res
    assert "[OTP:" in res
    assert "[ACCOUNT:" in res
    assert "[PHONE:" in res
