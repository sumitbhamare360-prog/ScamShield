# ScamShield Context

## 1. Purpose and scope
ScamShield is an automated multichannel scam detection, explanation, and advisory engine.
It evaluates messages across SMS, WhatsApp, and Email channels by combining heuristic rules, link/domain checks, sender validation, and pretrained language models.
The engine flags high-risk indicators, generates human-understandable evidence spans and recommended actions, and surfaces results via an API and Streamlit dashboard.

## 2. Non-goals
- No continuous model training, fine-tuning, or retraining in this pipeline; only pretrained weights or deterministic heuristics are employed.
- No persisting, logging, or printing of raw unmasked user message content; persistence is strictly restricted to masked text.
- No direct end-user telecommunication interception or automatic carrier blocking.

## 3. Architecture and data flow
1. Input ingestion: Raw Message (text, channel, sender, subject) is submitted via FastAPI endpoint or Dashboard UI.
2. Preprocessing: Message text is masked (PII sanitized) and metadata (URLs, phone numbers, UPI IDs, amounts, domains) is extracted into an Extracted object.
3. Feature checks and Model scoring:
   - Rules check: Evaluates keyword patterns, urgency flags, and structural scam indicators.
   - Links check: Analyzes URL safety, suspicious redirectors, and blocklists.
   - Sender check: Inspects sender handle, display name spoofing, and domain reputation.
   - Pretrained Models (Transformer and LSTM): Predict probability scores P(scam) independently.
   - Explainability: Extracts token/span highlights correlated with scam predictions.
4. Fusion & Decision: Check results and model probabilities are combined via weighted scoring into score bands, generating a final Verdict.
5. Advisory & Persistence: Scam type classification, remediation actions, and a report summary are attached. Masked records are saved in SQLite store.

## 4. Folder tree
```
ScamShield/
  .gitignore
  README.md
  requirements.txt
  data/
    brands.json
    eval/
  dashboard/
    app.py
    assets/
  docs/
    CONTEXT.md
    TASKS.md
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
  tests/
```

## 5. Contracts

### Data Schemas
- Message:
  - text: str
  - channel: str ("sms" | "whatsapp" | "email" | "unknown")
  - sender: str | None = None
  - subject: str | None = None
- Extracted:
  - masked_text: str
  - urls: list[str]
  - phones: list[str]
  - upi_ids: list[str]
  - amounts: list[str]
  - display_name: str | None = None
  - sender_domain: str | None = None
  - reply_to_domain: str | None = None
- Evidence:
  - rule_id: str
  - reason: str
  - severity: float (0 - 1)
  - span: tuple[int, int] | None = None
- CheckResult:
  - name: str
  - score: float | None (0 - 100)
  - weight: float
  - status: str ("ok" | "not_applicable" | "not_checked" | "error")
  - evidence: list[Evidence] = []
  - detail: str = ""
- Verdict:
  - score: int
  - category: str
  - confidence: str ("high" | "medium" | "low")
  - confidence_note: str
  - scam_type: str
  - uncertain: bool
  - model_agreement: float | None
  - highlights: list[dict]
  - checks: dict[str, CheckResult]
  - actions: list[str]
  - report_text: str
  - scan_id: int | None = None

### Function Signatures
- preprocess:
  - mask(text: str) -> str
  - extract(msg: Message) -> Extracted
- rules:
  - run(ext: Extracted) -> CheckResult (name="rules")
- links:
  - check(ext: Extracted, use_reputation: bool, blocklist: set[str]) -> CheckResult (name="links")
- sender:
  - check(ext: Extracted) -> CheckResult (name="sender")
- models.transformer:
  - score(text: str) -> float (0 - 1, P(scam))
- models.lstm:
  - score(text: str) -> float (0 - 1, P(scam))
- models.explain:
  - highlights(score_fn: Callable[[str], float], text: str) -> list[dict] (keys: text, start, end, weight)
- scoring:
  - fuse(checks: dict[str, CheckResult], lstm_p: float, transformer_p: float) -> dict (keys: score, category, confidence, confidence_note, uncertain, model_agreement)
- advice:
  - classify_scam_type(ext: Extracted, checks: dict[str, CheckResult]) -> str
  - actions(category: str, scam_type: str, ext: Extracted) -> list[str]
  - report_text(verdict: Verdict) -> str
- pipeline:
  - analyze(msg: Message, use_reputation: bool, blocklist: set[str]) -> Verdict
- ocr:
  - extract_text(image_bytes: bytes) -> str
- store:
  - init_db(path: str) -> None
  - save_scan(masked_text: str, channel: str, verdict: dict) -> int
  - list_scans(limit: int = 50) -> list[dict]
  - delete_scan(scan_id: int) -> None
  - clear_history() -> None
  - save_feedback(scan_id: int, label: str) -> None
  - add_blocklist(kind: str, value: str) -> None
  - get_blocklist() -> set[str]

## 6. Scoring constants and bands
- Weights:
  - transformer: 0.40
  - rules: 0.20
  - lstm: 0.15
  - links: 0.15
  - sender: 0.10
- Bands:
  - score < 30: "Likely Safe"
  - 30 <= score < 55: "Suspicious"
  - 55 <= score < 80: "Likely Scam"
  - score >= 80: "High-Risk Scam"
- Thresholds:
  - DISAGREE_THRESHOLD = 0.4
  - CHECK_NAMES = ["transformer", "rules", "lstm", "links", "sender"]

## 7. Decisions log
- Streamlit dashboard calls the FastAPI service over localhost.
- Pretrained models only; no training or fine-tuning workflows are supported.
- SQLite stores masked text only; unmasked text is never persisted to disk or logs.
- Models load once at API startup to minimize request latency.

## 8. Conventions and commands
- Fast testing: `pytest`
- Run API: `uvicorn scamshield.api:app --reload --port 8000`
- Run Dashboard: `streamlit run dashboard/app.py`
- Style: plain language, no emoji, no em dashes in code or docs.

## 9. Status board
- Scaffold: Complete
- Contracts: Defined in schemas.py and CONTEXT.md
- Core workstreams: Pending implementation by assigned agents
