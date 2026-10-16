import os
import json
from typing import List, Set, Tuple
from rapidfuzz import fuzz
from scamshield.schemas import Extracted, CheckResult, Evidence

FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "rediffmail.com", "aol.com", "icloud.com", "proton.me", "protonmail.com"
}

SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".loan", ".gq", ".tk", ".ml"}

_BRANDS_DATA = None


def _load_brands_data() -> Tuple[List[str], Set[str]]:
    global _BRANDS_DATA
    if _BRANDS_DATA is None:
        data_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "brands.json")
        )
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                brands = [b.lower().strip() for b in content.get("brands", [])]
                official = {d.lower().strip() for d in content.get("official_domains", [])}
                _BRANDS_DATA = (brands, official)
        else:
            _BRANDS_DATA = ([], set())
    return _BRANDS_DATA


def check(ext: Extracted) -> CheckResult:
    """Check email sender characteristics for spoofing, brand mismatch, and lookalike domains."""
    sender_domain = ext.sender_domain
    display_name = ext.display_name

    if not sender_domain and not display_name:
        return CheckResult(
            name="sender",
            score=None,
            weight=0.10,
            status="not_applicable",
            evidence=[],
            detail="No email sender available to check"
        )

    evidence_list: List[Evidence] = []
    brands, official_domains = _load_brands_data()

    norm_domain = (sender_domain or "").lower().strip()
    norm_name = (display_name or "").lower().strip()

    # 1. Suspicious TLD check on sender domain
    if norm_domain:
        for tld in SUSPICIOUS_TLDS:
            if norm_domain.endswith(tld):
                evidence_list.append(Evidence(
                    rule_id="SENDER_SUSPICIOUS_TLD",
                    reason=f"Sender domain uses high-risk TLD {tld}",
                    severity=0.75
                ))
                break

    # 2. Free-mail domain claiming bank or financial institution
    is_freemail = norm_domain in FREE_MAIL_DOMAINS
    claimed_brand_in_display = None
    if norm_name:
        for b in brands:
            if b in norm_name:
                claimed_brand_in_display = b
                break

    if is_freemail and claimed_brand_in_display:
        evidence_list.append(Evidence(
            rule_id="FREEMAIL_BANK_IMPERSONATION",
            reason=f"Free email provider {norm_domain} claiming brand '{claimed_brand_in_display}' in display name",
            severity=0.90
        ))

    # 3. Display name brand mismatch against sender domain
    if claimed_brand_in_display and norm_domain:
        # Check if domain belongs to official domains of the claimed brand
        if norm_domain not in official_domains and not norm_domain.startswith(claimed_brand_in_display):
            evidence_list.append(Evidence(
                rule_id="DISPLAY_NAME_BRAND_MISMATCH",
                reason=f"Display name claims '{claimed_brand_in_display}' but sender domain is '{norm_domain}'",
                severity=0.85
            ))

    # 4. Lookalike sender domain
    if norm_domain and norm_domain not in official_domains and not is_freemail:
        # Extract domain label
        parts = norm_domain.split(".")
        label = parts[-2] if len(parts) >= 2 else norm_domain
        if len(parts) >= 3 and parts[-2] in {"co", "gov", "org", "net", "com", "ac", "edu", "res"}:
            label = parts[-3]

        if "-" in label:
            subtokens = label.split("-")
            for sub in subtokens:
                for b in brands:
                    if sub == b or fuzz.ratio(sub, b) >= 85:
                        evidence_list.append(Evidence(
                            rule_id="LOOKALIKE_SENDER_DOMAIN",
                            reason=f"Sender domain label '{label}' resembles brand '{b}'",
                            severity=0.85
                        ))
                        break
        else:
            for b in brands:
                sim = fuzz.ratio(label, b)
                if sim >= 85 and label != b:
                    evidence_list.append(Evidence(
                        rule_id="LOOKALIKE_SENDER_DOMAIN",
                        reason=f"Sender domain label '{label}' is lookalike of brand '{b}' (similarity {sim:.1f})",
                        severity=0.85
                    ))
                    break

    # Score calculation
    if not evidence_list:
        score = 0.0
    else:
        prod = 1.0
        for ev in evidence_list:
            prod *= (1.0 - ev.severity)
        score = round((1.0 - prod) * 100.0, 2)

    detail_str = (
        f"Fired sender flags: {', '.join(set(e.rule_id for e in evidence_list))}"
        if evidence_list else "Sender domain and display name appear consistent"
    )

    return CheckResult(
        name="sender",
        score=score,
        weight=0.10,
        status="ok",
        evidence=evidence_list,
        detail=detail_str
    )
