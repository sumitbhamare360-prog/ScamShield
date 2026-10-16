# ScamShield Progress Log

## How to work on this project
1. Read docs/CONTEXT.md and the "Current status" section below. Read nothing else first.
2. Do not start a later phase while the current phase has open items that block development. Items that block shipping do not block development, but they must stay listed until resolved.
3. When a task finishes, add to the current phase: what was done, problems found, fix applied, commit hash.
4. When something fails, log it under the phase where it happened, and state whether it is fixed or open.
5. Do not change shared contracts in schemas.py without a decision logged in CONTEXT.md.
6. Use pretrained models only. Never train or fine-tune.
7. Never store or log raw message text. Only masked text is persisted.
8. Token economy: search with grep, view with line ranges, do not re-read files you just wrote.
9. Style: no emoji, no em dashes in code, UI text, or docs.
10. When a phase is finished, mark it Complete with the date and commit hash, then move the Current status pointer to the next phase.

## Current status
Phase: 2 (Scoring, advice, pipeline, dashboard, evaluation), in progress
Next action: evaluation. Phase 1 open items 1, 2, 3, and 4 remain open; items 1 and 2 block shipping only.
Last updated: 2026-10-16 at commit 64ba865

## Open issues
1. SCAMBERT licence UNCONFIRMED (blocks shipping). Owner action: confirm or obtain written permission from the author, or choose a licensed replacement.
2. BiLSTM licence not verified (blocks shipping). Owner action: check the licence tag on the model page.
3. Label mapping consistent with four test sentences; not verified on a broader set. Stays open until the 40-message evaluation runs. Four fixed sentences tested and recorded:
   - Sentence 1 (Scam): "Your account is blocked! Verify immediately with OTP. Send money to scam@ybl using https://scam.xyz/"
     * SCAMBERT (id2label generic {0: 'LABEL_0', 1: 'LABEL_1'}): Logits = [-4.4548, 4.1978], Probs = [0.000175, 0.999825]. Index 1 = scam.
     * BiLSTM (scalar logit under sigmoid): Logit = +6.904060, Prob P(scam) = 0.99899727. Positive logit = scam.
   - Sentence 2 (Scam): "Congratulations! You won Rs 50,000 lottery prize. Contact urgently to claim via link: http://bit.ly/claim"
     * SCAMBERT: Logits = [-4.5531, 4.2160], Probs = [0.000155, 0.999845]. Index 1 = scam.
     * BiLSTM: Logit = +9.857625, Prob P(scam) = 0.99994767. Positive logit = scam.
   - Sentence 3 (Safe): "Hey, are we still meeting for lunch tomorrow at 12?"
     * SCAMBERT: Logits = [3.6100, -3.7525], Probs = [0.999366, 0.000634]. Index 0 = safe.
     * BiLSTM: Logit = -11.375002, Prob P(scam) = 0.00001148. Negative logit = safe.
   - Sentence 4 (Safe): "Your OTP for the login is 482913. Do not share it with anyone."
     * SCAMBERT: Logits = [1.5299, -1.7361], Probs = [0.963244, 0.036756]. Index 0 = safe.
     * BiLSTM: Logit = -9.061960, Prob P(scam) = 0.00011598. Negative logit = safe.
   Observation: SCAMBERT index 1 means scam (`SCAM_CLASS_INDEX = 1`). BiLSTM scalar positive logit under sigmoid means scam (`SCAM_OUTPUT_STRUCTURE = "scalar_sigmoid"`). Regression tests enforced in `tests/test_models.py`.
4. Peak memory measured for the whole process, not per model (does not block). Owner action: isolate process memory profiling per model component.
5. Claim of verified MIT licenses in old log removed (resolved).
6. Tokenizer for BiLSTM is bert-base-uncased, inferred, not confirmed. The St3w31 repo has no vocabulary file.
7. Scheduled task from an earlier session: the record shows no active schedules, but the removal or non-creation is not documented. Note this in the Phase 2 entry.

## Phase 0: Scaffold and contracts
Status: Complete at commit 48ac44d.
Goal: project skeleton and shared contracts.
Done:
- Created folder structure: scamshield/, dashboard/, data/, docs/, scripts/, tests/.
- Defined shared Pydantic data schemas in scamshield/schemas.py (Evidence, Message, Extracted, CheckResult, Verdict).
- Implemented configuration constants and score thresholds in scamshield/config.py.
- Created all initial module stubs with exact function signatures raising NotImplementedError.
- Created minimal FastAPI /health endpoint and Streamlit dashboard placeholder.
- Created README.md, requirements.txt, .gitignore, and data/brands.json.
Problems found and fixes:
- Root models directory in .gitignore initially ignored package scamshield/models/. Fixed by anchoring ignore pattern to /models/.
- Overlap in early tracking for scripts/ and tests/. Fixed during scaffold restructuring.
- Path error in initial tracking table referencing docs/ instead of website/. Fixed at commit df4a225.
- Documentation restructuring into phase-based log completed at commit 12f07f4.
Files removed:
- docs/TASKS.md removed during migration to docs/PROGRESS.md.

## Phase 1: Core modules
Status: In progress.

### Preprocessing, masking, rules, OCR
- Status: Complete at commit 7e86d5e.
- Test count: 33 tests passing (tests/test_preprocess.py, tests/test_rules.py). Total test suite count: 58 tests passing.
- What was done:
  - Implemented mask() covering OTPs, Indian mobile numbers, bank account numbers, and card numbers, retaining last 2 visible digits.
  - Implemented extract() handling obfuscated URLs (hxxp, [.]), phones, UPI IDs, amounts, and email sender headers.
  - Implemented 28 heuristic rules in rules.py with combined scoring.
  - Implemented graceful OCR text extraction via ocr.py.
  - Documented rules in docs/RULES.md.
- Problems found and fixes:
  - Account masking pattern conflicted with card number matcher. Fixed regex ordering to process explicit account keywords first.

### Models and explainability
- Status: Partly complete at commit 7e86d5e.
- Test count: 6 tests passing (tests/test_models.py). Total test suite count: 74 tests passing.
- What was done:
  - Created scripts/download_models.py to cache SCAMBERT and BiLSTM models.
  - Implemented transformer.py scoring via Hugging Face DistilBERT.
  - Implemented lstm.py scoring via PyTorch BiLSTM architecture.
  - Implemented explain.py word perturbation explainer.
  - Latency measured: SCAMBERT 16.22 ms/msg, BiLSTM 2.08 ms/msg. Process memory: ~762 MB (process memory, not valid per model, re-measure pending).
  - Verified label mapping on four canonical sentences: SCAMBERT index 1 means scam (`SCAM_CLASS_INDEX = 1`), BiLSTM scalar positive logit under sigmoid means scam (`SCAM_OUTPUT_STRUCTURE = "scalar_sigmoid"`).
- Problems found and fixes:
  - Old task log erroneously claimed MIT licenses verified. Fixed: docs/LICENSES.md marks both models UNCONFIRMED.
  - Generic id2label in SCAMBERT resolved via empirical four-sentence verification test and enforced in regression tests.
- Open:
  - Licences unconfirmed for production distribution (Issue 1, Issue 2).
  - Peak memory measured for the whole process, not per model (Issue 4).

### Links and sender checks
- Status: Complete at commit 99cfe13.
- Test count: 20 tests passing (14 links tests in tests/test_links.py, 6 sender tests in tests/test_sender.py). Total test suite count: 58 tests passing.
- What was done:
  - Populated data/brands.json with major Indian banks, UPI apps, wallets, and couriers along with official domains.
  - Implemented links.check() in scamshield/links.py with structural flags (suspicious TLDs, >3 subdomains, raw IP host, punycode, @ symbol, known shorteners, very long URLs), lookalike brand matching via rapidfuzz ratio >= 85, active blocklist lookups, and reputation integrations (Google Safe Browsing v4 with GSB_API_KEY, URLhaus) with 3-second timeout and mocked HTTP testing.
  - Implemented sender.check() in scamshield/sender.py with display name brand mismatch against sender domain, free email provider brand impersonation, lookalike sender domains, and high-risk TLD checks.
- Problems found and fixes:
  - Ensured failed reputation lookups mark the lookup as failed/not_checked in detail and never falsely report safe. Verified by test.

### Store and API
- Status: Complete at commit 08f56ad.
- Test count: 15 tests passing (6 store tests in tests/test_store.py, 9 api tests in tests/test_api.py). Total test suite count: 73 tests passing.
- What was done:
  - Implemented SQLite store in scamshield/store.py managing scans, feedback, and blocklist tables with configurable database path (default ./data/scamshield.db).
  - Implemented save_scan storing masked text only, list_scans, delete_scan, clear_history, save_feedback, add_blocklist, and get_blocklist.
  - Implemented FastAPI app in scamshield/api.py with POST /analyze, POST /analyze-image, GET /history, DELETE /history/{scan_id}, DELETE /history, POST /feedback, POST /blocklist, GET /blocklist, and GET /health.
  - Implemented lifespan model loader with fallback flag models_loaded on startup.
  - Implemented localhost-only CORS middleware and input validations (422 for empty text, 413 for text >5000 chars) returning standard JSON error payloads without stack traces.
- Problems found and fixes:
  - Added python-multipart requirement for handling multipart image upload.
  - Verified with direct SQLite inspection test that raw OTPs and phone numbers never appear in the database.
  - Replaced deprecated 413 status constant with numeric HTTP status 413; full suite confirms the warning is gone.
  - Replaced deprecated 422 status constant with HTTP_422_UNPROCESSABLE_CONTENT; commit 5150565.

## Phase 2: Scoring, advice, pipeline, dashboard, evaluation
Status: In progress.

### Scoring and advice
- Status: Complete at 2026-10-16.
- Test count: 41 tests passing for scoring/advice; 115 tests passing in the full suite.
- What was done:
  - Implemented weighted scoring with available-check filtering and weight redistribution, model contributions, malicious reputation/blocklist overrides, configured score bands, disagreement detection, model agreement, and confidence notes.
  - Implemented rule-first and masked-keyword scam classification, scam-specific remediation actions, required payment and reporting advice, and a safe-field-only report summary.
  - Added scoring and advice fixtures covering the requested boundaries, overrides, weight redistribution, disagreement, all scam types, action requirements, and report privacy.
  - Added missing-model confidence and unknown report-label fallback tests.
- Problems found and fixes:
  - The scoring call has no message metadata parameter, although confidence depends on message length and URLs. Added an optional Extracted argument while preserving the three-argument call form.
  - Confidence thresholds: medium when text is below 15 words; low when text has 4 words or fewer, models disagree, or links are present without a reputation result.
  - Scheduled task from an earlier session has no active schedules recorded; removal or non-creation is undocumented. Recorded as an open issue; no schedule was changed in this task.
  - Remaining warning: StarletteDeprecationWarning from FastAPI's site-packages/fastapi/testclient.py:1 about httpx usage.
  - The FastAPI test client warning is third-party, not actionable; it originates from FastAPI's testclient.py and does not come from project code.
- Commit: a9c14e2.

### Pipeline
- Status: Complete at 2026-10-16.
- Test count: 11 pipeline tests passing; 126 tests passing in the full suite.
- What was done:
  - Implemented concurrent transformer, BiLSTM, rules, links, and sender checks and assembled their results into a Verdict.
  - Check exceptions produce safe error details and do not prevent a Verdict; missing model probabilities remain None and model checks are marked error or not_checked.
  - Generated highlights using masked text only, and left highlights empty when the transformer is unavailable or explainability fails.
  - Passed Extracted metadata into scoring.fuse so confidence can use text and link availability.
  - Confirmed from commit 842afb6 that fuse already accepted optional ext; updated the section 5 contract and dated decision log to document the existing contract.
  - Measured end-to-end analyze latency on CPU with loaded models warmed before timing and use_reputation=False: the four label-mapping sentences combined across 12 runs had median 331.4 ms and maximum 357.2 ms; the 40-word message across 3 runs had median 946.2 ms and maximum 990.7 ms; the 100-word message across 3 runs had median 4,666.5 ms and maximum 4,879.3 ms.
- Problems found and fixes:
  - Added explicit tests for a None transformer result and an explain.highlights exception; both preserve a Verdict with empty highlights.
  - Latency decision (2026-10-16): retain the under-3-second target for typical messages under 50 words. The 40-word measurement is within target. Record the 100-word result as a known stress-test limit and defer optimization to Phase 3; no speed changes were made in this task.
  - The remaining StarletteDeprecationWarning originates from FastAPI's test client and is third-party, not actionable.
- Commit: ff2360d.

### Dashboard
- Status: Complete at 2026-10-16.
- Test count: 5 dashboard tests passing; 131 tests passing in the full suite.
- What was done:
  - Built the Streamlit Analyze, History, and Blocklist pages against the existing FastAPI endpoints, with mock mode, image upload, reputation toggle, verdict evidence, feedback, report download, and blocklist actions.
  - Escaped all highlight text before rendering; exercised the UI with fixed mock data and a synthetic message against the live local API.
  - Added filters and confirmed per-scan and clear-all history deletion controls.
- Problems found and fixes:
  - First UI run mixed light backgrounds with the default dark text palette. Applied a neutral grey palette with teal accent and readable form controls.
  - The first request-state implementation left form controls disabled after completion. Switched to a submit callback and explicit pending-state reset; confirmed controls disable during the request and re-enable afterward.
  - Full suite has one existing StarletteDeprecationWarning from FastAPI's `testclient.py:1` about `httpx` use. It is third-party and not actionable in this task.
- Mock and live API checks: passed. API health reported models loaded; dashboard submission returned and displayed a live Verdict.
- Commit: 64ba865.

### Blocklist validation
- Status: Complete at 2026-10-16.
- Test count: 4 API tests added or expanded; 135 tests passing in the full suite.
- Confirmed `store.get_blocklist()` returns a `Set[str]` of plain values, as required by `links.check`.
- Added exact `kind` validation for `url`, `domain`, and `phone`; other values return 422 with the documented error and message fields.
- Added a real-pipeline API test that stores a full URL, analyzes a message containing it, observes `BLOCKLIST_HIT`, and verifies the score is at least 80. Models were available, so neither `pipeline.analyze` nor its model scores were mocked.
- The end-to-end test passed without changes to `links.py`; matching uses the stored full URL.
- Remaining warning: third-party `StarletteDeprecationWarning` from FastAPI's `testclient.py:1` about `httpx` use.
- Commit: pending progress-only follow-up.

## Phase 3: Integration and quality
Status: Not started.
- Quality list:
  - Validate model probabilities are within [0, 1] before constructing CheckResult scores.

## Phase 4: Website and launch gates
Status: Not started. Launch gates: custom domain, favicon, remove platform badge, privacy policy, terms, and legal review.
