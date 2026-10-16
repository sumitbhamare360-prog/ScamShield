import re
from scamshield.schemas import Extracted, CheckResult, Evidence

# Define 28 distinct rules with regex patterns, severities (0.0 to 1.0), and plain-language reasons
RULES_DEF = [
    {
        "id": "OTP_REQUEST",
        "severity": 0.95,
        "reason": "requests an OTP; real banks and services never ask for it",
        "regex": r"(?i)(?:share|send|provide|tell|give|enter|batayein|bhejo|dein|sajha karein)\s+(?:your\s+)?(?:otp|pin|one\s*time\s*password|verification\s*code)"
    },
    {
        "id": "OTP_HINGLISH",
        "severity": 0.90,
        "reason": "requests OTP in Hinglish phrased urgency",
        "regex": r"(?i)(?:otp\s+batayein|otp\s+bhejo|otp\s+share\s+karein|otp\s+dein)"
    },
    {
        "id": "URGENT_BLOCK",
        "severity": 0.85,
        "reason": "claims your account or service will be immediately blocked or suspended",
        "regex": r"(?i)(?:account|card|sim|connection|pan)\s+(?:will\s+be|has\s+been|is)\s+(?:blocked|suspended|deactivated|terminated|freeze|frozen)|(?:block\s+ho\s+jayega|band\s+ho\s+jayega|suspend\s+ho\s+jayega)"
    },
    {
        "id": "KYC_UPDATE",
        "severity": 0.85,
        "reason": "coerces immediate KYC or PAN update via unverified channels",
        "regex": r"(?i)(?:kyc|pan\s*card|aadhaar)\s+(?:is\s+pending|expired|update|verification\s+required|turant\s+update|karein|mandate)"
    },
    {
        "id": "TURANT_VERIFY_HINGLISH",
        "severity": 0.80,
        "reason": "pressures urgent verification in Hinglish to induce panic",
        "regex": r"(?i)(?:turant\s+verify|jaldi\s+karein|abhi\s+update\s+karein|nahi\s+to\s+band)"
    },
    {
        "id": "ACCOUNT_BAND_HINGLISH",
        "severity": 0.85,
        "reason": "threatens account closure in Hinglish",
        "regex": r"(?i)(?:aapka\s+account\s+band|khata\s+band|sewa\s+band)"
    },
    {
        "id": "UPI_COLLECT",
        "severity": 0.80,
        "reason": "requests approving a UPI collect request or entering PIN to receive funds",
        "regex": r"(?i)(?:enter\s+pin\s+to\s+receive|approve\s+collect|accept\s+request\s+to\s+get|collect\s+request|pin\s+daalein\s+paise\s+pane)"
    },
    {
        "id": "PRIZE_CLAIM",
        "severity": 0.85,
        "reason": "claims you have won a lottery, gift, or contest requiring a claim action",
        "regex": r"(?i)(?:won|winner|lottery|lucky\s+draw|cashback|prize|reward|claim\s+your\s+reward|inaam|jeeta\s+hai)"
    },
    {
        "id": "COURIER_FEE",
        "severity": 0.75,
        "reason": "claims parcel or package delivery is stuck and requires immediate fee payment",
        "regex": r"(?i)(?:parcel|package|shipment|courier|customs|delivery\s+failed|address\s+confirmation|pay\s+delivery\s+fee)"
    },
    {
        "id": "JOB_FEE",
        "severity": 0.80,
        "reason": "offers high daily income or part-time work requiring an initial deposit or fee",
        "regex": r"(?i)(?:part[- ]?time\s+job|work\s+from\s+home|earn\s+daily|earn\s+\d+\s*(?:rs|inr|per\s*day)|telegram\s+task|like\s+and\s+subscribe|daily\s+income)"
    },
    {
        "id": "GUARANTEED_RETURNS",
        "severity": 0.85,
        "reason": "promises unrealistic risk-free high profits or guaranteed investment returns",
        "regex": r"(?i)(?:guaranteed\s+return|100%\s+profit|double\s+your\s+money|risk[- ]?free\s+investment|zero\s+risk)"
    },
    {
        "id": "CRYPTO_PROMO",
        "severity": 0.75,
        "reason": "unsolicited cryptocurrency or token investment scheme promotion",
        "regex": r"(?i)(?:crypto|bitcoin|usdt|airdrop|binance\s+signal|free\s+tokens|crypto\s+bonus)"
    },
    {
        "id": "AUTHORITY_IMPERSONATION",
        "severity": 0.90,
        "reason": "impersonates law enforcement, police, CBI, RBI, or government department",
        "regex": r"(?i)(?:cbi|crime\s+branch|cyber\s+crime|police|rbi\s+notice|income\s+tax\s+department|customs\s+officer|court\s+summons|digital\s+arrest)"
    },
    {
        "id": "DIGITAL_ARREST",
        "severity": 0.95,
        "reason": "fabricates a digital arrest or legal custody notice",
        "regex": r"(?i)(?:digital\s+arrest|arrest\s+warrant|under\s+investigation|stay\s+on\s+video\s+call)"
    },
    {
        "id": "SHORTENED_LINK",
        "severity": 0.65,
        "reason": "uses URL shorteners commonly associated with masking malicious destinations",
        "regex": r"(?i)(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|cutt\.ly|shorturl\.at|rb\.gy)"
    },
    {
        "id": "REMOTE_ACCESS_APP",
        "severity": 0.90,
        "reason": "urges installation of remote screen sharing or access tools",
        "regex": r"(?i)(?:anydesk|teamviewer|rustdesk|quicksupport|screen\s+share\s+app|airmirror)"
    },
    {
        "id": "APK_DOWNLOAD",
        "severity": 0.85,
        "reason": "requests downloading an Android APK package directly rather than official app stores",
        "regex": r"(?i)(?:download\s+apk|\.apk\b|install\s+app\s+from\s+link|sbi\.apk|bank\.apk)"
    },
    {
        "id": "ELECTRICITY_BILL_CUT",
        "severity": 0.85,
        "reason": "threatens immediate electricity disconnection due to supposed unpaid bill",
        "regex": r"(?i)(?:electricity\s+(?:power\s+)?will\s+be\s+disconnected|power\s+cut|bijli\s+kat|bijli\s+bill|officer\s+contact)"
    },
    {
        "id": "REFUND_TRAP",
        "severity": 0.75,
        "reason": "claims an unexpected refund or tax rebate is waiting to be processed",
        "regex": r"(?i)(?:tax\s+refund|overpayment\s+refund|rebate\s+processed|claim\s+refund|refund\s+initiated)"
    },
    {
        "id": "PASSWORD_RESET_UNSOLICITED",
        "severity": 0.70,
        "reason": "unsolicited security alert pushing a password reset or validation link",
        "regex": r"(?i)(?:security\s+alert|unauthorized\s+login|reset\s+your\s+password\s+now|compromised\s+account)"
    },
    {
        "id": "THREAT_OF_ACTION",
        "severity": 0.80,
        "reason": "uses aggressive intimidation or deadline threats",
        "regex": r"(?i)(?:within\s+24\s+hours|within\s+1\s+hour|immediately\s+or\s+face|legal\s+action\s+will\s+be\s+taken)"
    },
    {
        "id": "FAKE_CUSTOMER_CARE",
        "severity": 0.75,
        "reason": "shares non-standard customer care phone numbers to divert users",
        "regex": r"(?i)(?:helpline\s+number|customer\s+care\s+toll\s*free|contact\s+manager\s+on\s+whatsapp)"
    },
    {
        "id": "CREDIT_SCORE_FIX",
        "severity": 0.70,
        "reason": "claims ability to artificially boost CIBIL or credit score instantly",
        "regex": r"(?i)(?:improve\s+cibil|fix\s+credit\s+score|instant\s+cibil\s+upgrade)"
    },
    {
        "id": "PRE_APPROVED_LOAN",
        "severity": 0.70,
        "reason": "unsolicited pre-approved loan with zero documentation requiring processing fee",
        "regex": r"(?i)(?:pre[- ]?approved\s+loan|no\s+document\s+loan|instant\s+disbursal|processing\s+fee\s+first)"
    },
    {
        "id": "TELEGRAM_INVESTMENT",
        "severity": 0.80,
        "reason": "solicits users to join private Telegram channel for investment or tasks",
        "regex": r"(?i)(?:join\s+telegram|t\.me\/|telegram\s+channel\s+for\s+profit)"
    },
    {
        "id": "CHARITY_FRAUD",
        "severity": 0.70,
        "reason": "manipulative appeal for emergency donation via direct personal UPI",
        "regex": r"(?i)(?:emergency\s+donation|save\s+child\s+life|send\s+donation\s+to\s+upi)"
    },
    {
        "id": "CARD_EXPIRY_SPOOF",
        "severity": 0.75,
        "reason": "falsely claims ATM/Debit card expiration requiring details confirmation",
        "regex": r"(?i)(?:debit\s+card\s+expired|atm\s+card\s+will\s+expire|renew\s+card\s+online)"
    },
    {
        "id": "OFFER_EXPIRES_SOON",
        "severity": 0.60,
        "reason": "creates artificial scarcity with expiring offer countdown",
        "regex": r"(?i)(?:offer\s+expires\s+in\s+\d+\s+min|limited\s+time\s+deal|valid\s+only\s+today)"
    }
]


def run(ext: Extracted) -> CheckResult:
    """Run regex-based heuristic checks against extracted message text."""
    text = (ext.masked_text or "").strip()
    if not text:
        return CheckResult(
            name="rules",
            score=None,
            weight=0.20,
            status="not_checked",
            evidence=[],
            detail="Empty text; rules check skipped"
        )

    evidence_list = []
    reasons_fired = []
    product_remaining = 1.0

    for rule in RULES_DEF:
        m = re.search(rule["regex"], text)
        if m:
            span = (m.start(), m.end())
            severity = float(rule["severity"])
            ev = Evidence(
                rule_id=rule["id"],
                reason=rule["reason"],
                severity=severity,
                span=span
            )
            evidence_list.append(ev)
            reasons_fired.append(rule["id"])
            product_remaining *= (1.0 - severity)

    if not evidence_list:
        return CheckResult(
            name="rules",
            score=0.0,
            weight=0.20,
            status="ok",
            evidence=[],
            detail="No suspicious rules matched"
        )

    # Combined score = 1 - product(1 - severity), scaled to 0-100
    combined_score = round((1.0 - product_remaining) * 100.0, 2)
    detail_str = f"Fired {len(evidence_list)} rules: {', '.join(reasons_fired[:5])}"
    if len(reasons_fired) > 5:
        detail_str += f" and {len(reasons_fired) - 5} more"

    return CheckResult(
        name="rules",
        score=combined_score,
        weight=0.20,
        status="ok",
        evidence=evidence_list,
        detail=detail_str
    )
