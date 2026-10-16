import pytest
from unittest.mock import patch, MagicMock
from scamshield.schemas import Extracted
from scamshield.links import check


def test_links_not_applicable_when_no_urls_or_phones():
    ext = Extracted(masked_text="Hello", urls=[], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert res.name == "links"
    assert res.status == "not_applicable"
    assert res.score is None


def test_suspicious_tld_flag():
    ext = Extracted(masked_text="", urls=["https://bank-verification.xyz/login"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert res.status == "ok"
    assert any(e.rule_id == "SUSPICIOUS_TLD" for e in res.evidence)
    assert res.score > 0


def test_excessive_subdomains():
    ext = Extracted(masked_text="", urls=["https://login.secure.update.verify.example.com"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "EXCESSIVE_SUBDOMAINS" for e in res.evidence)


def test_ip_address_host():
    ext = Extracted(masked_text="", urls=["http://192.168.1.50/pay"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "IP_HOST" for e in res.evidence)


def test_punycode_domain():
    ext = Extracted(masked_text="", urls=["https://xn--sbi-8ka.com/login"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "PUNYCODE_DOMAIN" for e in res.evidence)


def test_at_symbol_in_url():
    ext = Extracted(masked_text="", urls=["https://legit.com@scam-site.org/path"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "AT_IN_URL" for e in res.evidence)


def test_known_shortener():
    ext = Extracted(masked_text="", urls=["https://bit.ly/claim-prize"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "SHORTENER_DOMAIN" for e in res.evidence)


def test_very_long_url():
    long_url = "https://example.com/" + "a" * 125
    ext = Extracted(masked_text="", urls=[long_url], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "VERY_LONG_URL" for e in res.evidence)


def test_lookalike_brand_domain():
    # sbi lookalike: sbi-secure-update.com
    ext = Extracted(masked_text="", urls=["https://sbi-secure-update.com/netbanking"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert any(e.rule_id == "LOOKALIKE_BRAND" for e in res.evidence)


def test_official_brand_domain_not_flagged_as_lookalike():
    # Official sbi domain
    ext = Extracted(masked_text="", urls=["https://onlinesbi.sbi/portal"], phones=[])
    res = check(ext, use_reputation=False, blocklist=set())
    assert not any(e.rule_id == "LOOKALIKE_BRAND" for e in res.evidence)


def test_blocklist_hit_url_and_phone():
    ext = Extracted(masked_text="", urls=["https://malicious-domain.com"], phones=["9876543210"])
    blocklist = {"malicious-domain.com", "9876543210"}
    res = check(ext, use_reputation=False, blocklist=blocklist)
    assert res.score == 100.0
    hits = [e for e in res.evidence if e.rule_id == "BLOCKLIST_HIT"]
    assert len(hits) >= 1


@patch("requests.post")
def test_reputation_urlhaus_malicious(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"query_status": "ok", "url_status": "online"}
    mock_post.return_value = mock_resp

    ext = Extracted(masked_text="", urls=["https://danger-url.com"], phones=[])
    res = check(ext, use_reputation=True, blocklist=set())
    assert any(e.rule_id == "REPUTATION_MALICIOUS" for e in res.evidence)
    assert "URLhaus found malicious URL" in res.detail


@patch("requests.post")
def test_reputation_failure_shows_not_checked_in_detail(mock_post):
    # Simulate network timeout or exception
    mock_post.side_effect = Exception("Connection timed out")

    ext = Extracted(masked_text="", urls=["https://unknown-domain.com"], phones=[])
    res = check(ext, use_reputation=True, blocklist=set())
    assert "Reputation lookup failed/not_checked" in res.detail
    assert "failed" in res.detail.lower()
    # Ensure it never claims safe when lookup failed
    assert "clear" not in res.detail.lower()


@patch("requests.post")
def test_reputation_gsb_when_api_key_set(mock_post, monkeypatch):
    monkeypatch.setenv("GSB_API_KEY", "dummy_key")

    def side_effect(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "safebrowsing.googleapis.com" in url:
            resp.json.return_value = {"matches": [{"threatType": "MALWARE"}]}
        else:
            resp.json.return_value = {"query_status": "no_results"}
        return resp

    mock_post.side_effect = side_effect

    ext = Extracted(masked_text="", urls=["https://threat-site.com"], phones=[])
    res = check(ext, use_reputation=True, blocklist=set())
    assert any(e.rule_id == "REPUTATION_MALICIOUS" for e in res.evidence)
    assert "Google Safe Browsing threat detected" in res.detail
