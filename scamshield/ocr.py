import io
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


def extract_text(image_bytes: bytes) -> str:
    """Extract text from raw image bytes using pytesseract.

    If tesseract binary or library is missing, returns an error message instead of crashing.
    """
    if not image_bytes:
        return ""

    if pytesseract is None:
        return "Error: pytesseract library is not installed."

    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract OCR engine is not installed or not found on system PATH."
    except Exception as e:
        return f"Error: OCR extraction failed: {str(e)}"
