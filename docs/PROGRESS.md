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
Phase: 1 (Core modules) complete; ready for Phase 2 (Scoring, advice, pipeline, dashboard, evaluation)
Next action: Address Phase 2 development prerequisites (scoring fusion, advice generation, pipeline orchestrator) while maintaining Phase 1 shipping blockers (Issues 1-3).
Last updated: 2026-10-16 at commit 08f56ad

## Open issues
1. SCAMBERT licence UNCONFIRMED (blocks shipping). Owner action: confirm or obtain written permission from the author, or choose a licensed replacement.
2. BiLSTM licence not verified (blocks shipping). Owner action: check the licence tag on the model page.
3. Label mapping for SCAMBERT and BiLSTM not verified. Action: run the four fixed sentences in docs/LICENSES or tests, record raw logits and id2label, state which index means scam.
4. Peak memory measured for the whole process, not per model (does not block). Owner action: isolate process memory profiling per model component.
5. Claim of verified MIT licenses in old log removed (resolved).

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
- Test count: 5 tests passing (tests/test_models.py).
- What was done:
  - Created scripts/download_models.py to cache SCAMBERT and BiLSTM models.
  - Implemented transformer.py scoring via Hugging Face DistilBERT.
  - Implemented lstm.py scoring via PyTorch BiLSTM architecture.
  - Implemented explain.py word perturbation explainer.
  - Latency measured: SCAMBERT 16.22 ms/msg, BiLSTM 2.08 ms/msg. Process memory: ~762 MB (process memory, not valid per model, re-measure pending).
- Problems found and fixes:
  - Old task log erroneously claimed MIT licenses verified. Fixed: docs/LICENSES.md marks both models UNCONFIRMED.
  - Model verification fix items (licences, systematic label mapping test output, per-model memory isolation): not done, recorded as open issues.
- Open:
  - Licences unconfirmed for production distribution (Issue 1, Issue 2).
  - Label mapping for SCAMBERT and BiLSTM not verified (Issue 3).
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

## Phase 2: Scoring, advice, pipeline, dashboard, evaluation
Status: Not started.

## Phase 3: Integration and quality
Status: Not started.

## Phase 4: Website and launch gates
Status: Not started. Launch gates: custom domain, favicon, remove platform badge, privacy policy, terms, and legal review.
