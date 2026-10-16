import io
import os
import shutil

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from scamshield import ocr
from scamshield.api import app


TESSERACT_PATH = (
    os.getenv("TESSERACT_CMD")
    or shutil.which("tesseract")
    or (r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.isfile(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        else None)
)
SYNTHETIC_TEXT = (
    "Your account is blocked. Share OTP 482913 now or call 9876543210. "
    "Visit https://example.com/verify"
)


def make_synthetic_screenshot():
    image = Image.new("RGB", (1000, 220), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 28)
    draw.multiline_text(
        (24, 42),
        "Your account is blocked. Share OTP 482913 now or call\n"
        "9876543210. Visit https://example.com/verify",
        fill="black",
        font=font,
        spacing=18,
    )
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_missing_binary_returns_503(monkeypatch):
    assert ocr.pytesseract is not None, "pytesseract is required to test the missing binary path"
    monkeypatch.setattr(
        ocr.pytesseract.pytesseract,
        "tesseract_cmd",
        "missing-tesseract-executable",
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/analyze-image",
            files={"file": ("screenshot.png", make_synthetic_screenshot(), "image/png")},
        )
    assert response.status_code == 503
    assert response.json()["error"] == "ocr_unavailable"


@pytest.mark.skipif(not TESSERACT_PATH, reason="Tesseract binary is not available")
def test_live_ocr_finds_at_least_three_required_keywords(monkeypatch):
    monkeypatch.setattr(ocr.pytesseract.pytesseract, "tesseract_cmd", TESSERACT_PATH)
    result = ocr.extract_text(make_synthetic_screenshot())
    assert not result.startswith("Error:"), "OCR should return extracted text"
    found = [term for term in ("blocked", "OTP", "482913", "example.com") if term in result]
    assert len(found) >= 3
