import os
import json
import re
import ipaddress
import urllib.parse
from typing import Set, Tuple, List, Optional
import requests
from rapidfuzz import fuzz
from scamshield.schemas import Extracted, CheckResult, Evidence

SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".loan", ".gq", ".tk", ".ml"}

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly",
    "shorturl.at", "rb.gy", "ow.ly", "buff.ly", "rebrand.ly"
}

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


def _extract_domain_and_label(url: str) -> Tuple[str, str, str]:
    """Returns (host, registrable_domain, domain_label)."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host and "@" in url:
        host = url.split("@", 1)[-1].split("/")[0].lower()
    
    parts = host.split(".")
    if len(parts) >= 2:
        reg_domain = ".".join(parts[-2:])
        label = parts[-2]
        if len(parts) >= 3 and parts[-2] in {"co", "gov", "org", "net", "com", "ac", "edu", "res"}:
            reg_domain = ".".join(parts[-3:])
            label = parts[-3]
    else:
        reg_domain = host
        label = host

    return host, reg_domain, label


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _check_urlhaus(url: str) -> Tuple[str, Optional[bool]]:
    """Query URLhaus API with 3s timeout.

    Returns: (status_note, is_malicious_or_none)
    """
    try:
        resp = requests.post(
            "https://urlhaus-api.abuse.ch/v1/url/",
            data={"url": url},
            timeout=3
        )
        if resp.status_code == 200:
            data = resp.json()
            query_status = data.get("query_status")
            if query_status == "ok":
                url_status = data.get("url_status")
                return ("URLhaus found malicious URL", True)
            elif query_status == "no_results":
                return ("URLhaus clear", False)
            else:
                return (f"URLhaus query status {query_status}", None)
        else:
            return (f"URLhaus HTTP {resp.status_code}", None)
    except Exception as e:
        return (f"URLhaus lookup failed ({str(e)})", None)


def _check_gsb(url: str, api_key: str) -> Tuple[str, Optional[bool]]:
    """Query Google Safe Browsing v4 API with 3s timeout."""
    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    payload = {
        "client": {"clientId": "scamshield", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    try:
        resp = requests.post(endpoint, json=payload, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            matches = data.get("matches", [])
            if matches:
                return ("Google Safe Browsing threat detected", True)
            return ("Google Safe Browsing clear", False)
        else:
            return (f"Google Safe Browsing HTTP {resp.status_code}", None)
    except Exception as e:
        return (f"Google Safe Browsing lookup failed ({str(e)})", None)


def check(ext: Extracted, use_reputation: bool, blocklist: Set[str]) -> CheckResult:
    """Check extracted links, domains, and phones against local rules, lookalikes, blocklists, and reputation."""
    urls = ext.urls or []
    phones = ext.phones or []

    if not urls and not phones:
        return CheckResult(
            name="links",
            score=None,
            weight=0.15,
            status="not_applicable",
            evidence=[],
            detail="No URLs or phone numbers to check"
        )

    evidence_list: List[Evidence] = []
    brands, official_domains = _load_brands_data()
    norm_blocklist = {b.lower().strip() for b in blocklist}

    # 1. Phone blocklist checks
    for phone in phones:
        clean_p = re.sub(r"[\s\-+]", "", phone.lower())
        if phone.lower() in norm_blocklist or clean_p in norm_blocklist:
            evidence_list.append(Evidence(
                rule_id="BLOCKLIST_HIT",
                reason=f"Phone number {phone} is in the active blocklist",
                severity=1.0
            ))

    reputation_details = []
    has_failed_reputation_lookup = False

    # 2. URL structural and reputation checks
    for url in urls:
        host, reg_domain, label = _extract_domain_and_label(url)
        url_lower = url.lower()
        host_lower = host.lower()
        reg_lower = reg_domain.lower()

        # Blocklist check
        if (url_lower in norm_blocklist or host_lower in norm_blocklist or reg_lower in norm_blocklist):
            evidence_list.append(Evidence(
                rule_id="BLOCKLIST_HIT",
                reason=f"URL or domain {reg_domain} is in the active blocklist",
                severity=1.0
            ))

        # Check official domain
        is_official = (reg_lower in official_domains or host_lower in official_domains)

        # Suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if host_lower.endswith(tld):
                evidence_list.append(Evidence(
                    rule_id="SUSPICIOUS_TLD",
                    reason=f"Domain uses high-risk TLD {tld}",
                    severity=0.70
                ))
                break

        # More than 3 subdomains (e.g. a.b.c.d.example.com -> parts > 4)
        parts = host_lower.split(".")
        if len(parts) > 4:
            evidence_list.append(Evidence(
                rule_id="EXCESSIVE_SUBDOMAINS",
                reason=f"Host contains {len(parts)-2} subdomains, often used to conceal target host",
                severity=0.60
            ))

        # IP address host
        if _is_ip_address(host):
            evidence_list.append(Evidence(
                rule_id="IP_HOST",
                reason="URL host is a raw IP address rather than a registered domain",
                severity=0.85
            ))

        # Punycode
        if "xn--" in host_lower:
            evidence_list.append(Evidence(
                rule_id="PUNYCODE_DOMAIN",
                reason="Domain uses punycode encoding which can mimic legitimate domains",
                severity=0.75
            ))

        # @ symbol in URL
        if "@" in url:
            evidence_list.append(Evidence(
                rule_id="AT_IN_URL",
                reason="URL contains @ symbol, often used to spoof host destination",
                severity=0.80
            ))

        # Known URL shortener
        if host_lower in KNOWN_SHORTENERS or reg_lower in KNOWN_SHORTENERS:
            evidence_list.append(Evidence(
                rule_id="SHORTENER_DOMAIN",
                reason=f"URL uses known shortening service {host_lower}",
                severity=0.60
            ))

        # Very long URL
        if len(url) > 120:
            evidence_list.append(Evidence(
                rule_id="VERY_LONG_URL",
                reason="URL is unusually long (>120 chars)",
                severity=0.45
            ))

        # Lookalike brand check (skip if officially registered domain)
        if not is_official and label:
            # Hyphen-heavy brand mimicking
            if "-" in label:
                subtokens = label.split("-")
                for sub in subtokens:
                    for b in brands:
                        if sub == b or fuzz.ratio(sub, b) >= 85:
                            evidence_list.append(Evidence(
                                rule_id="LOOKALIKE_BRAND",
                                reason=f"Domain label {label} resembles brand '{b}'",
                                severity=0.85
                            ))
                            break
            else:
                for b in brands:
                    # Direct fuzzy comparison with brand name
                    sim = fuzz.ratio(label, b)
                    if sim >= 85 and label != b:
                        evidence_list.append(Evidence(
                            rule_id="LOOKALIKE_BRAND",
                            reason=f"Domain label '{label}' is lookalike of brand '{b}' (similarity {sim:.1f})",
                            severity=0.85
                        ))
                        break

        # Reputation lookups if enabled
        if use_reputation:
            # 1. URLhaus
            uh_note, uh_res = _check_urlhaus(url)
            if uh_res is True:
                evidence_list.append(Evidence(
                    rule_id="REPUTATION_MALICIOUS",
                    reason=f"URLhaus reported malicious link ({url})",
                    severity=1.0
                ))
                reputation_details.append(uh_note)
            elif uh_res is None:
                has_failed_reputation_lookup = True
                reputation_details.append(uh_note)
            else:
                reputation_details.append(uh_note)

            # 2. Google Safe Browsing (if GSB_API_KEY set)
            gsb_key = os.environ.get("GSB_API_KEY")
            if gsb_key:
                gsb_note, gsb_res = _check_gsb(url, gsb_key)
                if gsb_res is True:
                    evidence_list.append(Evidence(
                        rule_id="REPUTATION_MALICIOUS",
                        reason=f"Google Safe Browsing reported threat ({url})",
                        severity=1.0
                    ))
                    reputation_details.append(gsb_note)
                elif gsb_res is None:
                    has_failed_reputation_lookup = True
                    reputation_details.append(gsb_note)
                else:
                    reputation_details.append(gsb_note)

    # Compute combined score from evidence severities
    if not evidence_list:
        score = 0.0
    else:
        prod = 1.0
        for ev in evidence_list:
            prod *= (1.0 - ev.severity)
        score = round((1.0 - prod) * 100.0, 2)

    status = "ok"
    detail_parts = []
    if evidence_list:
        rule_ids = [e.rule_id for e in evidence_list]
        detail_parts.append(f"Flags fired: {', '.join(set(rule_ids))}")
    else:
        detail_parts.append("No suspicious links or phone indicators detected")

    if use_reputation:
        if has_failed_reputation_lookup:
            detail_parts.append(f"Reputation lookup failed/not_checked: {'; '.join(reputation_details)}")
        else:
            detail_parts.append(f"Reputation checks: {'; '.join(reputation_details)}")

    return CheckResult(
        name="links",
        score=score,
        weight=0.15,
        status=status,
        evidence=evidence_list,
        detail="; ".join(detail_parts)
    )
