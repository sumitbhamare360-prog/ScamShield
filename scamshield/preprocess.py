import re
import urllib.parse
from email.utils import parseaddr
from scamshield.schemas import Message, Extracted

# Standard and common Indian and global PSP handles for UPI validation
KNOWN_PSP_HANDLES = {
    "okaxis", "okhdfcbank", "okicici", "oksbi",
    "ybl", "ibl", "axl",
    "paytm", "ptyes", "pthdfc", "ptaxis", "ptsbi",
    "apl", "rapl",
    "upi", "barodampay", "aubank", "cnrb", "federal", "indus",
    "idfcbank", "kotak", "pnb", "sib", "yesbank", "axisbank",
    "postbank", "ikwik", "jupiteraxis", "freecharge"
}

# Regex patterns
RE_OTP = re.compile(
    r"(?i)(?:(?:\botp\b|one[-\s]?time[-\s]?password|verification\s*code|pin|code)[\s:=\u2013\-#]*"
    r"|(?:\bis\b|\bcode\b|\blogin\b)[\s:=\u2013\-#]+)"
    r"(\b\d{4,8}\b)"
)
RE_OTP_POST = re.compile(
    r"(\b\d{4,8}\b)\s*(?:is\s+your\s+(?:otp|one[-\s]?time|verification)|(?:for\s+otp|otp\b))",
    re.IGNORECASE
)

# Indian mobile numbers: +91 followed by 10 digits starting with 6-9, or 10 digits starting with 6-9
# Needs to avoid matching 12-18 digit account numbers or card numbers by using boundary/lookahead
RE_PHONE = re.compile(r"(?:(?:\+91[\s\-]?)|\b)([6-9]\d{9})\b")

# Bank cards: 13 to 19 digits (optional spaces or hyphens)
RE_CARD = re.compile(r"\b(?:\d[ \-]*?){13,19}\b")

# Bank account numbers: 9 to 18 digits (often preceded by a/c, acct, account, etc. or standalone sequence)
RE_ACCOUNT = re.compile(r"(?i)(?:a/c|acct|acc|account|ac|number|no\.?)[^\w\n]{0,5}(\d{9,18})\b")
RE_GENERIC_LONG_NUM = re.compile(r"\b\d{11,18}\b")

# Obfuscated / standard URLs
RE_URL = re.compile(
    r"(?:(?:https?|hxxps?):\/\/|www\.)[^\s<>\"']+|[a-zA-Z0-9_\-]+\[\.\][a-zA-Z0-9_\-\.\[\]\/]+",
    re.IGNORECASE
)

# Phone extraction
RE_PHONE_EXTRACT = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}\b")

# UPI pattern: localpart@handle
RE_UPI = re.compile(r"\b([a-zA-Z0-9\.\-_]{2,256})@([a-zA-Z0-9]{2,64})\b")

# Amounts: Rs, INR, rupee sign ₹
RE_AMOUNT = re.compile(
    r"(?:(?i:rs\.?|inr)|₹)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)|([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:(?i:rs\.?|inr)|₹)",
    re.IGNORECASE
)


def mask(text: str) -> str:
    """Mask OTP codes, Indian mobile numbers, bank account numbers, and card numbers.

    Rules:
    - OTP: completely masked (e.g. [OTP:****])
    - Phone: keep last 2 digits visible (e.g. [PHONE:********89])
    - Account numbers: keep last 2 digits visible (e.g. [ACCOUNT:**********34])
    - Card numbers: keep last 2 digits visible (e.g. [CARD:************56])
    """
    if not text:
        return ""

    masked = text

    # 1. Mask OTP
    def _mask_otp(m):
        full_match = m.group(0)
        otp_val = m.group(1)
        return full_match.replace(otp_val, "[OTP:****]")

    masked = RE_OTP.sub(_mask_otp, masked)
    masked = RE_OTP_POST.sub(lambda m: "[OTP:****] is your OTP", masked)

    # 2. Mask Explicit Account Numbers (prefixed by a/c, acct, etc.)
    def _mask_acc(m):
        acc = m.group(1)
        last2 = acc[-2:]
        masked_val = f"[ACCOUNT:{'*' * (len(acc) - 2)}{last2}]"
        return m.group(0).replace(acc, masked_val)

    masked = RE_ACCOUNT.sub(_mask_acc, masked)

    # 3. Mask Bank Cards (13-19 digits formatted)
    def _mask_card(m):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19:
            last2 = digits[-2:]
            return f"[CARD:{'*' * (len(digits) - 2)}{last2}]"
        return m.group(0)

    masked = RE_CARD.sub(_mask_card, masked)

    # 4. Mask remaining long numbers (11 to 18 digits) as accounts if not already masked
    def _mask_long_num(m):
        val = m.group(0)
        last2 = val[-2:]
        return f"[ACCOUNT:{'*' * (len(val) - 2)}{last2}]"

    masked = RE_GENERIC_LONG_NUM.sub(_mask_long_num, masked)

    # 5. Mask Indian Mobile Numbers (10 digits starting 6-9, with optional +91)
    def _mask_phone(m):
        phone = m.group(1)
        last2 = phone[-2:]
        prefix = "+91 " if "+91" in m.group(0) else ""
        return f"[PHONE:{prefix}{'*' * 8}{last2}]"

    masked = RE_PHONE.sub(_mask_phone, masked)

    return masked


def _normalize_url(url_str: str) -> str:
    cleaned = url_str.strip(".,;:()[]{}<>\"'")
    cleaned = cleaned.replace("[.]", ".").replace("hxxp://", "http://").replace("hxxps://", "https://")
    if not cleaned.lower().startswith(("http://", "https://")):
        cleaned = "https://" + cleaned
    return cleaned


def extract(msg: Message) -> Extracted:
    """Extract metadata and return an Extracted schema with masked text."""
    raw_text = msg.text or ""
    masked_text = mask(raw_text)

    # Extract URLs
    raw_urls = RE_URL.findall(raw_text)
    urls = []
    for u in raw_urls:
        norm = _normalize_url(u)
        if norm not in urls:
            urls.append(norm)

    # Extract Phones
    raw_phones = RE_PHONE_EXTRACT.findall(raw_text)
    phones = []
    for p in raw_phones:
        cleaned_p = re.sub(r"[\s\-]", "", p)
        if cleaned_p not in phones:
            phones.append(cleaned_p)

    # Extract UPI IDs
    raw_upis = RE_UPI.findall(raw_text)
    upi_ids = []
    for user_part, handle_part in raw_upis:
        handle_lower = handle_part.lower()
        if handle_lower in KNOWN_PSP_HANDLES or any(bank in handle_lower for bank in ["bank", "pay", "axis", "sbi", "hdfc", "icici"]):
            full_upi = f"{user_part}@{handle_part}"
            if full_upi not in upi_ids:
                upi_ids.append(full_upi)

    # Extract Amounts
    amounts = []
    for m in RE_AMOUNT.finditer(raw_text):
        amt = m.group(1) or m.group(2)
        if amt and amt not in amounts:
            amounts.append(amt.strip())

    display_name = None
    sender_domain = None
    reply_to_domain = None

    if msg.sender:
        sender_str = msg.sender.strip()
        parsed_name, parsed_addr = parseaddr(sender_str)
        if parsed_name:
            display_name = parsed_name
        if "@" in parsed_addr:
            sender_domain = parsed_addr.split("@", 1)[1].strip().lower()
        elif "@" in sender_str:
            sender_domain = sender_str.split("@", 1)[1].strip().lower()

    return Extracted(
        masked_text=masked_text,
        urls=urls,
        phones=phones,
        upi_ids=upi_ids,
        amounts=amounts,
        display_name=display_name,
        sender_domain=sender_domain,
        reply_to_domain=reply_to_domain,
    )
