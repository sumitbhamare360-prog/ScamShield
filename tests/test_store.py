import os
import sqlite3
import pytest
from scamshield import store

TEST_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data.db")
)


@pytest.fixture(autouse=True)
def setup_test_db():
    store.init_db(TEST_DB_PATH)
    store.clear_history()
    yield
    store.clear_history()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


def test_save_and_list_scans():
    verdict = {
        "score": 85,
        "category": "High-Risk Scam",
        "confidence": "high",
        "scam_type": "KYC Scam",
        "uncertain": False
    }
    scan_id = store.save_scan(
        masked_text="Your account is blocked [PHONE:********10]",
        channel="sms",
        verdict=verdict
    )
    assert scan_id is not None
    assert scan_id > 0

    scans = store.list_scans(limit=10)
    assert len(scans) == 1
    assert scans[0]["id"] == scan_id
    assert scans[0]["channel"] == "sms"
    assert scans[0]["masked_text"] == "Your account is blocked [PHONE:********10]"
    assert scans[0]["verdict"]["category"] == "High-Risk Scam"


def test_delete_scan():
    scan_id = store.save_scan("Masked text", "email", {"score": 20})
    scans = store.list_scans()
    assert len(scans) == 1

    store.delete_scan(scan_id)
    scans_after = store.list_scans()
    assert len(scans_after) == 0


def test_clear_history():
    store.save_scan("Masked 1", "sms", {"score": 10})
    store.save_scan("Masked 2", "sms", {"score": 20})
    assert len(store.list_scans()) == 2

    store.clear_history()
    assert len(store.list_scans()) == 0


def test_save_feedback():
    scan_id = store.save_scan("Masked text", "sms", {"score": 90})
    store.save_feedback(scan_id=scan_id, label="correct")

    # Verify directly from DB table
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT scan_id, label FROM feedback WHERE scan_id = ?", (scan_id,))
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0][0] == scan_id
    assert rows[0][1] == "correct"


def test_add_and_get_blocklist():
    store.add_blocklist("domain", "evil-site.xyz")
    store.add_blocklist("phone", "9876543210")
    # Duplicate addition should be ignored
    store.add_blocklist("domain", "evil-site.xyz")

    bl = store.get_blocklist()
    assert "evil-site.xyz" in bl
    assert "9876543210" in bl
    assert len(bl) == 2


def test_raw_text_not_stored_in_sqlite():
    raw_phone = "9876543210"
    raw_otp = "482910"
    # Simulated pipeline flow: raw text was masked prior to store.save_scan
    from scamshield.preprocess import mask
    raw_msg = f"Your OTP is {raw_otp} for mobile {raw_phone}"
    masked = mask(raw_msg)

    scan_id = store.save_scan(masked_text=masked, channel="sms", verdict={"score": 80})

    # Read SQLite database file bytes and check for raw strings
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT masked_text, verdict_json FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()

    db_text = row[0]
    db_json = row[1]

    # Confirm raw sensitive PII is absent
    assert raw_phone not in db_text
    assert raw_otp not in db_text
    assert raw_phone not in db_json
    assert raw_otp not in db_json

    # Directly inspect entire raw DB file
    with open(TEST_DB_PATH, "rb") as f:
        content = f.read()
    assert raw_phone.encode() not in content
    assert raw_otp.encode() not in content
