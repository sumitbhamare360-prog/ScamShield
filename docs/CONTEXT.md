# ScamShield Context

## 1. Purpose and scope
ScamShield is an automated multichannel scam detection, explanation, and advisory engine.
It evaluates messages across SMS, WhatsApp, and Email channels by combining heuristic rules, link/domain checks, sender validation, and pretrained language models.
The engine flags high-risk indicators, generates human-understandable evidence spans and recommended actions, and surfaces results via a FastAPI backend and a Streamlit dashboard.

## 2. Non-goals
- No continuous model training, fine-tuning, or retraining; only pretrained weights or deterministic heuristics are employed.
- No persisting, logging, or printing of raw unmasked user message content; persistence is strictly restricted to masked text.
- No direct end-user telecommunication interception or automatic carrier-level network blocking.

## 3. Architecture and data flow
1. Ingestion: Message (text, channel, sender, subject) is submitted via FastAPI endpoint or dashboard UI.
2. Preprocessing: Message text is masked (sanitizing OTPs, mobile numbers, card, and account numbers), and metadata (URLs, phone numbers, UPI IDs, amounts, sender domains) is extracted into an Extracted object.
3. Feature checks and Model scoring:
   - Rules: Evaluates pattern rules, urgency cues, and scam indicators.
   - Links: Analyzes URL destinations, obfuscation, blocklists, and reputation lookups; failed reputation lookups never count as safe.
   - Sender: Inspects sender handle, display name spoofing, and domain reputation.
   - Pretrained Models (SCAMBERT, BiLSTM): Predict probability scores P(scam) independently.
   - Explainability: Extracts token and span highlights correlated with scam predictions.
4. Fusion & Decision: Check results and model probabilities are combined via weighted scoring into score bands, generating a final Verdict.
5. Advisory & Persistence: Scam type classification, remediation actions, and a report summary are attached. Masked records are saved in SQLite store.

## 4. Folder tree
```
ScamShield/
  .gitignore
  README.md
  requirements.txt
  dashboard/
    app.py
    assets/
  data/
    brands.json
    eval/
      .gitkeep
  docs/
    CONTEXT.md
    LICENSES.md
    PROGRESS.md
    RULES.md
  scamshield/
    __init__.py
    advice.py
    api.py
    config.py
    links.py
    ocr.py
    pipeline.py
    preprocess.py
    rules.py
    schemas.py
    scoring.py
    sender.py
    store.py
    models/
      __init__.py
      explain.py
      lstm.py
      transformer.py
  scripts/
    download_models.py
  tests/
    test_links.py
    test_models.py
    test_preprocess.py
    test_rules.py
    test_sender.py
```

## 5. Contracts
```python
class Evidence(BaseModel):
    rule_id: str
    reason: str
    severity: float = Field(ge=0.0, le=1.0)
    span: Optional[Tuple[int, int]] = None

class Message(BaseModel):
    text: str
    channel: str = Field(description="'sms' | 'whatsapp' | 'email' | 'unknown'")
    sender: Optional[str] = None
    subject: Optional[str] = None

class Extracted(BaseModel):
    masked_text: str
    urls: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    upi_ids: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    display_name: Optional[str] = None
    sender_domain: Optional[str] = None
    reply_to_domain: Optional[str] = None

class CheckResult(BaseModel):
    name: str
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    weight: float
    status: str = Field(description="'ok' | 'not_applicable' | 'not_checked' | 'error'")
    evidence: List[Evidence] = Field(default_factory=list)
    detail: str = ""

class Verdict(BaseModel):
    score: int
    category: str
    confidence: str = Field(description="'high' | 'medium' | 'low'")
    confidence_note: str
    scam_type: str
    uncertain: bool
    model_agreement: Optional[float] = None
    highlights: List[Dict[str, Any]] = Field(default_factory=list)
    checks: Dict[str, CheckResult] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    report_text: str
    scan_id: Optional[int] = None
```

### Module Responsibilities
- `preprocess`: Masks sensitive numbers and extracts structured metadata.
- `rules`: Runs regex heuristic pattern checks and outputs evidence.
- `links`: Checks URLs against reputations and blocklists.
- `sender`: Checks sender handles, headers, and spoofed display names.
- `models.transformer`: Generates P(scam) using fine-tuned DistilBERT (SCAMBERT).
- `models.lstm`: Generates P(scam) using bidirectional LSTM.
- `models.explain`: Computes word-level score drop highlights.
- `scoring`: Fuses checks and model probabilities into unified scores and categories.
- `advice`: Classifies scam categories, actionable steps, and user report text.
- `pipeline`: Orchestrates extraction, checking, scoring, and advisory generation.
- `ocr`: Extracts text from image inputs via Tesseract.
- `store`: Handles SQLite persistence for masked scans, feedback, and blocklists.
- `api`: Exposes REST endpoints for health checks, scans, and feedback.

## 6. Scoring constants and verdict bands
- Component Weights:
  - transformer: 0.40
  - rules: 0.20
  - lstm: 0.15
  - links: 0.15
  - sender: 0.10
- Verdict Bands:
  - score < 30: "Likely Safe"
  - 30 <= score < 55: "Suspicious"
  - 55 <= score < 80: "Likely Scam"
  - score >= 80: "High-Risk Scam"
- Disagreement Threshold: 0.40

## 7. Decisions log
- 2026-10-16: Streamlit dashboard calls the FastAPI service over localhost.
- 2026-10-16: Pretrained models only; no training or fine-tuning workflows permitted.
- 2026-10-16: SQLite stores masked text only; unmasked text is never persisted or logged.
- 2026-10-16: Models load once at application startup to reduce per-request latency.
- 2026-10-16: Transitional agent tracking replaced by phase-based progress tracking.

## 8. Commands
- Install dependencies: `pip install -r requirements.txt`
- Run API service: `uvicorn scamshield.api:app --reload --port 8000`
- Run Dashboard: `streamlit run dashboard/app.py`
- Run Test suite: `python -m pytest tests/`
- Download Models: `python scripts/download_models.py`

## 9. Known limitations
- SCAMBERT and BiLSTM model licensing status is unconfirmed for production distribution.
- English and Hinglish patterns are supported; broader regional languages are pending.
- OCR requires external Tesseract binary installed on the host system PATH.
- Reputation checks use Google Safe Browsing (only when GSB_API_KEY is set) and URLhaus; both can fail, in which case the result is "not_checked".
