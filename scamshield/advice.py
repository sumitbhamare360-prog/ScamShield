import re
from typing import Dict, List

from scamshield.schemas import CheckResult, Extracted, Verdict


_RULE_TYPES = (
    ({"OTP_REQUEST", "OTP_HINGLISH"}, "OTP fraud"),
    ({"KYC_UPDATE", "TURANT_VERIFY_HINGLISH", "ACCOUNT_BAND_HINGLISH"}, "Fake KYC or bank alert"),
    ({"PRIZE_CLAIM"}, "Lottery or prize"),
    ({"JOB_FEE"}, "Job offer"),
    ({"COURIER_FEE"}, "Courier or parcel"),
    ({"UPI_COLLECT", "UPI_PAYMENT_REQUEST", "UPI_ID_REQUEST"}, "UPI payment request"),
    ({"GUARANTEED_RETURNS", "CRYPTO_PROMO"}, "Investment or crypto"),
    ({"AUTHORITY_IMPERSONATION", "DIGITAL_ARREST", "FREEMAIL_BANK_IMPERSONATION", "DISPLAY_NAME_BRAND_MISMATCH"}, "Impersonation"),
)

_KEYWORD_TYPES = (
    (r"\b(?:share|send|provide|tell|give|enter)\s+(?:your\s+)?(?:otp|one[- ]time password|verification code)\b|\botp\s+(?:share|bhejo|batayein|dein)\b", "OTP fraud"),
    (r"\b(?:kyc|aadhaar|pan card)\b|\b(?:bank|account|card)\b.{0,30}\b(?:blocked|suspended|verify|update)\b", "Fake KYC or bank alert"),
    (r"\b(?:lottery|prize|winner|won|lucky draw|reward|claim your gift)\b", "Lottery or prize"),
    (r"\b(?:part[- ]time job|work from home|job offer|earn daily|telegram task)\b", "Job offer"),
    (r"\b(?:courier|parcel|package|shipment|delivery fee|customs fee)\b", "Courier or parcel"),
    (r"\b(?:upi collect|collect request|approve (?:the )?payment|enter pin to receive|pay via upi)\b", "UPI payment request"),
    (r"\b(?:crypto|bitcoin|usdt|investment|guaranteed returns|double your money|airdrop)\b", "Investment or crypto"),
    (r"\b(?:police|cbi|rbi notice|income tax department|digital arrest|arrest warrant|impersonat(?:e|ing))\b", "Impersonation"),
)


def classify_scam_type(ext: Extracted, checks: Dict[str, CheckResult]) -> str:
    rule_ids = {
        evidence.rule_id
        for check in checks.values()
        if check.status == "ok"
        for evidence in check.evidence
    }
    for ids, scam_type in _RULE_TYPES:
        if rule_ids.intersection(ids):
            return scam_type

    text = (ext.masked_text or "").lower()
    for pattern, scam_type in _KEYWORD_TYPES:
        if re.search(pattern, text, re.IGNORECASE):
            return scam_type
    return "Unclear"


def actions(category: str, scam_type: str, ext: Extracted) -> List[str]:
    specific_steps = {
        "OTP fraud": [
            "Do not share the code or approve a login you did not start.",
            "Open the service's official app or website to check your account.",
            "Block the sender and report the message to the service.",
        ],
        "Fake KYC or bank alert": [
            "Contact your bank using the number on your card or official website.",
            "Do not open the message link or install an app it recommends.",
            "Report the message to your bank's fraud team.",
        ],
        "Lottery or prize": [
            "Do not pay a fee or tax to claim an unexpected prize.",
            "Verify the promotion through the organization's official website.",
            "Block the sender and report the message.",
        ],
        "Job offer": [
            "Do not pay registration, training, or task fees to get a job.",
            "Verify the employer and opening through its official careers page.",
            "Stop contact if they pressure you to deposit or recruit others.",
        ],
        "Courier or parcel": [
            "Check delivery status in the courier's official app or website.",
            "Do not pay through a link sent in an unexpected delivery message.",
            "Contact the courier using its published customer service details.",
        ],
        "UPI payment request": [
            "Decline unexpected collect requests and inspect the payee before paying.",
            "Remember that receiving money never requires entering your UPI PIN.",
            "Contact your bank promptly if you approved a suspicious payment.",
        ],
        "Investment or crypto": [
            "Do not transfer money or crypto based on guaranteed-return claims.",
            "Verify the provider and registration with the relevant official regulator.",
            "Do not install remote-access software or share wallet recovery phrases.",
        ],
        "Impersonation": [
            "End contact and independently call the named organization using its official number.",
            "Do not transfer money or install software at the caller's direction.",
            "Preserve the message and report the impersonation to the organization.",
        ],
        "Unclear": [
            "Verify the sender using a phone number or website you find independently.",
            "Do not open unexpected links, attachments, or payment requests.",
            "Block or report the sender if the message remains suspicious.",
        ],
    }
    steps = list(specific_steps.get(scam_type, specific_steps["Unclear"]))
    involves_sensitive_payment = scam_type in {
        "OTP fraud", "Fake KYC or bank alert", "Lottery or prize", "Job offer",
        "Courier or parcel", "UPI payment request", "Investment or crypto", "Impersonation",
    }
    required = []
    if involves_sensitive_payment:
        required.append("Never share your OTP, UPI PIN, or passwords")
    if scam_type != "Unclear":
        required.append("Report at 1930 or cybercrime.gov.in")
    safe_note = "Safe does not mean guaranteed safe. Still avoid links and payment requests."
    if category == "Likely Safe":
        required.append(safe_note)
    steps = steps[: max(0, 4 - len(required))] + required
    return steps


def report_text(verdict: Verdict) -> str:
    allowed_categories = {
        "Likely Safe", "Suspicious", "Likely Scam", "High-Risk Scam",
        "Uncertain: verify manually",
    }
    allowed_confidence = {"high", "medium", "low"}
    allowed_types = {
        "OTP fraud", "Fake KYC or bank alert", "Lottery or prize", "Job offer",
        "Courier or parcel", "UPI payment request", "Investment or crypto",
        "Impersonation", "Unclear",
    }
    category = verdict.category if verdict.category in allowed_categories else "Unclear"
    confidence = verdict.confidence if verdict.confidence in allowed_confidence else "low"
    scam_type = verdict.scam_type if verdict.scam_type in allowed_types else "Unclear"
    lines = [
        "ScamShield assessment",
        f"Category: {category}",
        f"Risk score: {int(verdict.score)}/100",
        f"Confidence: {confidence}",
        f"Scam type: {scam_type}",
    ]
    if verdict.uncertain:
        lines.append("Manual verification is recommended.")
    return "\n".join(lines)
