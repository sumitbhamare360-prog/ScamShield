# ScamShield Progress Log

## How to work on this project
1. Read docs/CONTEXT.md and the "Current status" section below. Read nothing else first.
2. Work on the current phase only. Do not start a later phase until the current phase has no open blocking items.
3. When a task finishes, add to the current phase: what was done, problems found, fix applied, commit hash.
4. When something fails, log it under the phase where it happened, and state whether it is fixed or open.
5. Do not change shared contracts in schemas.py without a decision logged in CONTEXT.md.
6. Use pretrained models only. Never train or fine-tune.
7. Never store or log raw message text. Only masked text is persisted.
8. Token economy: search with grep, view with line ranges, do not re-read files you just wrote.
9. Style: no emoji, no em dashes in code, UI text, or docs.
10. When a phase is finished, mark it Complete with the date and commit hash, then move the Current status pointer to the next phase.

## Current status
Phase: 1 (Core modules), in progress
Next action: Resolve Phase 1 open issues, then build links and sender checks.
Last updated: 2026-10-16 at commit df4a225

## Open issues
1. SCAMBERT licence UNCONFIRMED (blocks shipping). Owner action: confirm or obtain written permission from the author, or choose a licensed replacement.
2. BiLSTM licence not verified (blocks shipping). Owner action: check the licence tag on the model page.
3. Label mapping for SCAMBERT and BiLSTM not verified (blocks shipping). Owner action: perform and record systematic test matrix validating label index mapping across representative datasets.
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
Files removed:
- docs/TASKS.md removed during migration to docs/PROGRESS.md.

## Phase 1: Core modules
Status: In progress.

### Preprocessing, masking, rules, OCR
- Status: Complete at commit 7e86d5e.
- Test count: 33 tests passing (tests/test_preprocess.py, tests/test_rules.py). Total test suite count: 38 tests passing.
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
  - Measured CPU latency: SCAMBERT 16.22 ms/msg, BiLSTM 2.08 ms/msg. Process memory: ~762 MB.
- Problems found and fixes:
  - Old task log erroneously claimed MIT licenses verified. Fixed: docs/LICENSES.md marks both models UNCONFIRMED.
- Open:
  - Licences unconfirmed for production distribution (Issue 1, Issue 2).
  - Formal label mapping validation across broader benchmarks (Issue 3).
  - Per-model memory isolation (Issue 4).

### Links and sender checks
- Status: Not started.
- Details: scamshield/links.py and scamshield/sender.py contain NotImplementedError stubs. data/brands.json has empty lists. No test files exist.

### Store and API
- Status: Not started.
- Details: scamshield/store.py contains NotImplementedError stubs. scamshield/api.py has GET /health only. No test files exist.

## Phase 2: Scoring, advice, pipeline, dashboard, evaluation
Status: Not started.

## Phase 3: Integration and quality
Status: Not started.

## Phase 4: Website and launch gates
Status: Not started. Launch gates: custom domain, favicon, remove platform badge, privacy policy, terms, and legal review.
