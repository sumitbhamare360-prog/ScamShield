import os
import sqlite3
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from scamshield.api import app
from scamshield import store
from scamshield.schemas import Verdict

TEST_API_DB = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_api_store.db")
)


@pytest.fixture(autouse=True)
def init_api_db():
    store.init_db(TEST_API_DB)
    store.clear_history()
    yield
    store.clear_history()
    if os.path.exists(TEST_API_DB):
        try:
            os.remove(TEST_API_DB)
        except Exception:
            pass


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _mock_verdict():
    return Verdict(
        score=75,
        category="Likely Scam",
        confidence="high",
        confidence_note="Multiple indicators",
        scam_type="Phishing",
        uncertain=False,
        model_agreement=0.85,
        highlights=[],
        checks={},
        actions=["Block and delete"],
        report_text="Caution recommended"
    )


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "models_loaded" in data


def test_cors_headers_on_localhost(client):
    res = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_analyze_empty_text_returns_422(client):
    res = client.post("/analyze", json={"text": "   ", "channel": "sms"})
    assert res.status_code == 422
    data = res.json()
    assert data["error"] == "unprocessable_entity"


def test_analyze_long_text_returns_413(client):
    huge_text = "a" * 5001
    res = client.post("/analyze", json={"text": huge_text, "channel": "sms"})
    assert res.status_code == 413
    data = res.json()
    assert data["error"] == "payload_too_large"


@patch("scamshield.pipeline.analyze")
def test_analyze_success_and_stores_masked_only(mock_analyze, client):
    mock_analyze.return_value = _mock_verdict()

    raw_phone = "9876543210"
    raw_otp = "482910"
    msg_text = f"Urgent: your OTP is {raw_otp} sent to +91 {raw_phone}. Confirm immediately."

    res = client.post(
        "/analyze",
        json={"text": msg_text, "channel": "sms", "use_reputation": False}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["score"] == 75
    assert data["scan_id"] is not None

    # Inspect SQLite database directly to confirm no raw secrets were persisted
    conn = sqlite3.connect(TEST_API_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT masked_text, verdict_json FROM scans WHERE id = ?", (data["scan_id"],))
    row = cursor.fetchone()
    conn.close()

    db_masked = row[0]
    assert raw_otp not in db_masked
    assert raw_phone not in db_masked
    assert "[OTP:" in db_masked
    assert "[PHONE:" in db_masked

    # File-level byte inspection
    with open(TEST_API_DB, "rb") as f:
        raw_db_bytes = f.read()
    assert raw_otp.encode() not in raw_db_bytes
    assert raw_phone.encode() not in raw_db_bytes


@patch("scamshield.ocr.extract_text")
@patch("scamshield.pipeline.analyze")
def test_analyze_image_endpoint(mock_analyze, mock_ocr, client):
    mock_ocr.return_value = "Urgent lottery reward claim immediately"
    mock_analyze.return_value = _mock_verdict()

    fake_img = b"\x89PNG\r\n\x1a\nfakeimagecontent"
    res = client.post(
        "/analyze-image",
        files={"file": ("screenshot.png", fake_img, "image/png")},
        data={"channel": "whatsapp"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["score"] == 75
    assert data["scan_id"] is not None


def test_history_crud_endpoints(client):
    # Add scan manually
    scan_id = store.save_scan("Masked text", "email", {"score": 50})

    # GET /history
    res = client.get("/history")
    assert res.status_code == 200
    scans = res.json()
    assert len(scans) == 1
    assert scans[0]["id"] == scan_id

    # DELETE /history/{id}
    del_res = client.delete(f"/history/{scan_id}")
    assert del_res.status_code == 200
    assert client.get("/history").json() == []

    # Clear history
    store.save_scan("Masked 1", "sms", {"score": 30})
    clr_res = client.delete("/history")
    assert clr_res.status_code == 200
    assert client.get("/history").json() == []


def test_feedback_endpoint(client):
    scan_id = store.save_scan("Masked text", "sms", {"score": 90})
    res = client.post("/feedback", json={"scan_id": scan_id, "label": "scam"})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_blocklist_endpoints(client):
    res_add = client.post("/blocklist", json={"kind": "domain", "value": "phish-bank.xyz"})
    assert res_add.status_code == 200

    res_get = client.get("/blocklist")
    assert res_get.status_code == 200
    assert "phish-bank.xyz" in res_get.json()


def test_blocklist_accepts_url_kind(client):
    url = "https://blocked.example/account"

    response = client.post("/blocklist", json={"kind": "url", "value": url})

    assert response.status_code == 200
    assert url in client.get("/blocklist").json()


@pytest.mark.parametrize("kind", ["dmain", "url "])
def test_blocklist_rejects_unknown_kind(client, kind):
    response = client.post("/blocklist", json={"kind": kind, "value": "blocked.example"})

    assert response.status_code == 422
    assert response.json() == {
        "error": "invalid_blocklist_kind",
        "message": "Kind must be one of: url, domain, phone.",
    }


def test_blocklisted_full_url_is_found_by_real_pipeline(client):
    """Exercise storage, extraction, and the real pipeline with models as available."""
    url = "https://blocked.example/verify"
    add_response = client.post("/blocklist", json={"kind": "url", "value": url})
    assert add_response.status_code == 200

    response = client.post(
        "/analyze",
        json={
            "text": f"Review your account using this page: {url}",
            "channel": "sms",
            "use_reputation": False,
        },
    )

    assert response.status_code == 200
    verdict = response.json()
    link_check = verdict["checks"]["links"]
    assert any(item["rule_id"] == "BLOCKLIST_HIT" for item in link_check["evidence"])
    assert verdict["score"] >= 80
