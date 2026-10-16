from contextlib import asynccontextmanager
from typing import Optional, Literal
from fastapi import FastAPI, Request, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scamshield.schemas import Message, Verdict
from scamshield.preprocess import mask
from scamshield import store, pipeline, ocr

# Model loading state
_MODELS_LOADED = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _MODELS_LOADED
    try:
        from scamshield.models import transformer, lstm
        # Attempt warm-up / initialization
        transformer.score("warmup")
        lstm.score("warmup")
        _MODELS_LOADED = True
    except Exception:
        _MODELS_LOADED = False
    yield


app = FastAPI(title="ScamShield API", lifespan=lifespan)

# Allow localhost origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Never expose stack trace
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "message": "An internal error occurred."}
    )


class AnalyzeRequest(BaseModel):
    text: str
    channel: str = Field(default="unknown")
    sender: Optional[str] = None
    subject: Optional[str] = None
    use_reputation: bool = False


class FeedbackRequest(BaseModel):
    scan_id: int
    label: Literal["correct", "scam", "safe"]


class BlocklistRequest(BaseModel):
    kind: str
    value: str


def _validate_text(text: Optional[str]) -> Optional[JSONResponse]:
    if text is None or not text.strip():
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "unprocessable_entity", "message": "Text cannot be empty."}
        )
    if len(text) > 5000:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "payload_too_large", "message": "Text exceeds maximum allowed length of 5000 characters."}
        )
    return None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "models_loaded": _MODELS_LOADED}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    val_err = _validate_text(req.text)
    if val_err:
        return val_err

    masked = mask(req.text)
    blocklist = store.get_blocklist()
    msg = Message(
        text=req.text,
        channel=req.channel,
        sender=req.sender,
        subject=req.subject
    )

    verdict: Verdict = pipeline.analyze(
        msg=msg,
        use_reputation=req.use_reputation,
        blocklist=blocklist
    )

    # Save masked text only
    scan_id = store.save_scan(
        masked_text=masked,
        channel=req.channel,
        verdict=verdict.model_dump()
    )

    verdict.scan_id = scan_id
    return verdict.model_dump()


@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    channel: str = Form("unknown"),
    sender: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    use_reputation: bool = Form(False)
):
    try:
        contents = await file.read()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "unprocessable_entity", "message": "Failed to read image file."}
        )

    extracted_text = ocr.extract_text(contents)
    if extracted_text.startswith("Error:"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "ocr_failed", "message": extracted_text}
        )

    val_err = _validate_text(extracted_text)
    if val_err:
        return val_err

    masked = mask(extracted_text)
    blocklist = store.get_blocklist()
    msg = Message(
        text=extracted_text,
        channel=channel,
        sender=sender,
        subject=subject
    )

    verdict: Verdict = pipeline.analyze(
        msg=msg,
        use_reputation=use_reputation,
        blocklist=blocklist
    )

    scan_id = store.save_scan(
        masked_text=masked,
        channel=channel,
        verdict=verdict.model_dump()
    )

    verdict.scan_id = scan_id
    return verdict.model_dump()


@app.get("/history")
def get_history(limit: int = 50):
    return store.list_scans(limit=limit)


@app.delete("/history/{scan_id}")
def delete_history_item(scan_id: int):
    store.delete_scan(scan_id)
    return {"status": "ok", "deleted_id": scan_id}


@app.delete("/history")
def clear_history():
    store.clear_history()
    return {"status": "ok", "message": "History cleared"}


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    store.save_feedback(scan_id=req.scan_id, label=req.label)
    return {"status": "ok"}


@app.post("/blocklist")
def add_to_blocklist(req: BlocklistRequest):
    store.add_blocklist(kind=req.kind, value=req.value)
    return {"status": "ok"}


@app.get("/blocklist")
def list_blocklist():
    return list(store.get_blocklist())
