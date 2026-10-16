import pytest
from scamshield.models import transformer, lstm
from scamshield.models.explain import highlights

SAMPLES = [
    "URGENT: Your bank account is locked! Send OTP to unlock immediately at http://scam.xyz",
    "Congratulations you won 50,000 lottery cash prize! Call 9876543210 to claim.",
    "Hey mom, are we still meeting for lunch today at 12:30?",
    "Dear customer, update KYC immediately or electricity connection will be cut.",
    "Can you please review the attached slide deck before tomorrow's meeting?"
]


def test_transformer_score_range():
    for text in SAMPLES:
        sc = transformer.score(text)
        assert 0.0 <= sc <= 1.0


def test_lstm_score_range():
    for text in SAMPLES:
        sc = lstm.score(text)
        assert 0.0 <= sc <= 1.0


def test_scam_vs_ham_discrimination():
    spam_text = SAMPLES[0]
    ham_text = SAMPLES[2]

    trans_spam = transformer.score(spam_text)
    trans_ham = transformer.score(ham_text)
    assert trans_spam > 0.5
    assert trans_ham < 0.5
    assert trans_spam > 0.8
    assert trans_ham < 0.2

    lstm_spam = lstm.score(spam_text)
    lstm_ham = lstm.score(ham_text)
    assert lstm_spam > 0.5
    assert lstm_ham < 0.5
    assert lstm_spam > 0.8
    assert lstm_ham < 0.2


def test_explainer_spans_match_original_text():
    sample = "URGENT: Your bank account is locked! Send OTP immediately"
    hl = highlights(transformer.score, sample)
    assert isinstance(hl, list)
    assert len(hl) <= 8
    for item in hl:
        assert "text" in item
        assert "start" in item
        assert "end" in item
        assert "weight" in item
        assert item["weight"] > 0.05
        # Verify span in original text matches item text
        extracted_from_span = sample[item["start"]:item["end"]]
        assert extracted_from_span == item["text"]


def test_explainer_with_custom_score_fn():
    # Any custom score_fn must work
    def dummy_score(t: str) -> float:
        return 0.9 if "danger" in t else 0.1

    sample = "This is a danger situation"
    hl = highlights(dummy_score, sample)
    assert len(hl) == 1
    assert hl[0]["text"] == "danger"
    assert sample[hl[0]["start"]:hl[0]["end"]] == "danger"


def test_label_mapping_four_sentences():
    # The four canonical sentences for label mapping verification
    scam_1 = "Your account is blocked! Verify immediately with OTP. Send money to scam@ybl using https://scam.xyz/"
    scam_2 = "Congratulations! You won Rs 50,000 lottery prize. Contact urgently to claim via link: http://bit.ly/claim"
    safe_1 = "Hey, are we still meeting for lunch tomorrow at 12?"
    safe_2 = "Your OTP for the login is 482913. Do not share it with anyone."

    assert transformer.SCAM_CLASS_INDEX == 1
    assert lstm.SCAM_OUTPUT_STRUCTURE == "scalar_sigmoid"

    # SCAMBERT checks: scam > 0.5, safe < 0.5
    assert transformer.score(scam_1) > 0.5
    assert transformer.score(scam_2) > 0.5
    assert transformer.score(safe_1) < 0.5
    assert transformer.score(safe_2) < 0.5
    assert transformer.score(scam_1) > 0.99
    assert transformer.score(scam_2) > 0.99
    assert transformer.score(safe_1) < 0.01
    assert transformer.score(safe_2) < 0.05

    # BiLSTM checks: scam > 0.5, safe < 0.5
    assert lstm.score(scam_1) > 0.5
    assert lstm.score(scam_2) > 0.5
    assert lstm.score(safe_1) < 0.5
    assert lstm.score(safe_2) < 0.5
    assert lstm.score(scam_1) > 0.99
    assert lstm.score(scam_2) > 0.99
    assert lstm.score(safe_1) < 0.001
    assert lstm.score(safe_2) < 0.001
