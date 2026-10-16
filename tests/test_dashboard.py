import requests
import pytest

from dashboard import app
from scamshield import links
from scamshield.schemas import Extracted


def test_mock_mode_serves_example_verdict_and_page_data(monkeypatch):
    monkeypatch.setenv("SCAMSHIELD_MOCK", "1")

    verdict = app.api_request("POST", "/analyze", json={"text": "demo"})
    history = app.api_request("GET", "/history")
    blocklist = app.api_request("GET", "/blocklist")

    assert verdict["category"] == "High-Risk Scam"
    assert {"transformer", "lstm", "rules", "links", "sender"} <= set(verdict["checks"])
    assert history[0]["verdict"]["score"] == verdict["score"]
    assert blocklist


def test_highlight_markup_escapes_untrusted_text():
    markup = app.format_highlights([{"text": "<script>alert(1)</script>"}])

    assert "<script>" not in markup
    assert "&lt;script&gt;" in markup
    assert markup.startswith("<mark>")


def test_unreachable_service_uses_actionable_message(monkeypatch):
    def fail_request(*args, **kwargs):
        raise requests.ConnectionError("connection details are not displayed")

    monkeypatch.delenv("SCAMSHIELD_MOCK", raising=False)
    monkeypatch.setattr(app.requests, "request", fail_request)

    with pytest.raises(app.DashboardServiceError) as error:
        app.api_request("GET", "/health")

    assert str(error.value) == app.SERVICE_ERROR


def test_blocklist_payload_value_is_matched_by_links_check():
    payload = app.blocklist_payload("offers.example", "domain")
    ext = Extracted(masked_text="review offer", urls=["https://offers.example/pay"])
    result = links.check(ext, use_reputation=False, blocklist={payload["value"]})

    assert payload["kind"] == "domain"
    assert any(item.rule_id == "BLOCKLIST_HIT" for item in result.evidence)


def test_block_link_candidates_include_full_urls_and_domains():
    verdict = {
        "checks": {
            "links": {
                "evidence": [
                    {"reason": "Malicious URL (https://offers.example/claim)"},
                    {"reason": "URL or domain blocked.example is in the active blocklist"},
                ]
            }
        }
    }

    assert app.find_evidence_urls(verdict) == [
        "https://offers.example/claim",
        "https://blocked.example",
    ]
