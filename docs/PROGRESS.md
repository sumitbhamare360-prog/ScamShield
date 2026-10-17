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
Phase: 3 (Integration and quality), in progress
Next action: owner obtains and anonymizes 20 messages from a colleague who has not seen the rules or evaluation failures; resolve SCAMBERT and BiLSTM licence status. No fusion or weight changes before the independent set. Phase 1 open items 1 and 3 remain open; item 2 is resolved for licence identification with a THIRD_PARTY_NOTICES shipping step outstanding, and item 4 is resolved for peak memory only. Item 1 blocks shipping.
Last updated: 2026-10-17.

## Open issues
1. SCAMBERT licence UNCONFIRMED (blocks shipping). Owner action: confirm or obtain written permission from the author, or choose a licensed replacement. Licence request drafted 2026-10-17, not yet sent; the sent date is to be recorded here once the owner sends it. Publisher re-verified 2026-10-17 against the Hub API: `Digvijay05/SCAMBERT` resolves to `ThunderCrown/SCAMBERT`, one repository renamed rather than two parties, with `author` ThunderCrown, no `license:` field in the card metadata, no licence tag, and no LICENSE file. The owner must answer the redistribution question before sending, because the release path decides whether a redistribution grant is needed or download at install time is enough. Decision 2026-10-17: ask for commercial use with the weights downloaded from Hugging Face at install time and not redistributed, since that is the lighter first request. A redistribution grant for bundling in an installer is deferred until the author replies; if the answer is no or silence, the installer cannot include SCAMBERT and the release needs a download step or a different model.
2. RESOLVED 2026-10-17 for licence identification only. MIT via card metadata (`license:mit`). No LICENSE file in the repository. Identification is not distribution readiness: the repository is not the authority for distribution because it does not carry the licence text, so the distributed build will take the MIT text from the MIT template and the copyright holder from the author's Hugging Face profile, not from a file the repository does not contain. Shipping step, not a current blocker: add a THIRD_PARTY_NOTICES entry holding the MIT licence text and the copyright notice, and include it in any distributed build, the same as the Apache-2.0 duty for the candidate models. Also confirmed from the same page on 2026-10-17: the card declares bert-base-uncased for tokenization only and states the encoder is not BERT (item 6), the output is a logit requiring `torch.sigmoid` (matching `SCAM_OUTPUT_STRUCTURE` in `scamshield/models/lstm.py`), and training used the full UCI SMS Spam Collection, confirming the contamination note. The card does not say which sign means scam, so item 3 stays open.
3. Label mapping consistent with four test sentences; not verified on a broader set. Stays open until the 40-message evaluation runs. The St3w31 card confirms a logit output requiring `torch.sigmoid` but does not state which sign means spam, so it does not close this item. Four fixed sentences tested and recorded:
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
4. RESOLVED 2026-10-17 for peak memory only: memory is now measured per model component. See the "Production per-model memory profile" entry in Phase 3. SCAMBERT peak 716.1 MiB and BiLSTM peak 288.5 MiB, both below the 800 MiB criterion, with load dominating on both and no per-inference growth over 50 inferences. The residual combined-process figure moved to item 10.
5. Claim of verified MIT licenses in old log removed (resolved).
6. Tokenizer for BiLSTM is bert-base-uncased, declared by the author, no vocabulary file in repo. The St3w31 model card states that the model uses the bert-base-uncased tokenizer for tokenization only and that the encoder is not BERT. That is the author's declaration and is not verified against the production load path, where `lstm._get_model()` loads the tokenizer from the local snapshot when present and otherwise from `bert-base-uncased` on the Hub.
7. Scheduled task from an earlier session: the record shows no active schedules, but the removal or non-creation is not documented. Note this in the Phase 2 entry.
8. Full system scores below rules-only on the 40-row synthetic set (rows 2, 5, 10, 15 diagnosed). Action: evaluate any change on a held-out set before changing weights, thresholds, or fusion.
9. No independent held-out set. Owner will obtain 20 messages from a colleague who has not seen the rules or evaluation failures, then anonymize and label them before adding them to the repo or sharing them in prompts. Until then, no fusion, rule, or weight changes.
10. RESOLVED 2026-10-17 for peak memory only: combined serving process memory is now measured, not estimated. The single process that holds both models peaks at 752.4 MiB with 739.2 MiB resident, reproducing at 751.7 MiB on a repeat run. The earlier arithmetic estimate of about 765 MiB was close but was not a measurement and has been replaced. See the "Production per-model memory profile" entry in Phase 3. This closure covers memory at rest and under a single sequential inference loop only. It says nothing about latency under concurrent requests, which is tracked separately as Open issue 11. Note that the 800 MiB figure is a team threshold from our own candidate work, not a platform requirement, and a breach would be an owner decision about the host rather than a reason for a silent model change.
11. The API has not been load-tested. All memory figures come from single fresh processes running one sequential inference loop, so latency and memory under concurrent requests are unknown. Does not block. Action: load-test the API under concurrent requests and record latency percentiles and memory under load. No load-testing dependency or script may be added to the repository without owner approval, because it adds a new tool to the repo and sends traffic to a running service. Owner approval is required first.

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
  - OCR verification found two remaining deprecated 422 references in `/analyze-image`; replaced them with `HTTP_422_UNPROCESSABLE_CONTENT` in Phase 3 commit `e383199`. The image handler no longer emits that deprecation warning.

## Phase 2: Scoring, advice, pipeline, dashboard, evaluation
Status: Complete at 2026-10-17; reporting close-out commit d476e8e.

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
- API `kind` validation intentionally accepts only exact lowercase values. For example, `Domain ` is rejected even though direct store calls normalize it; the stricter API behavior avoids silently accepting inconsistent payloads.
- Added `tests/*.db` to `.gitignore` so an interrupted API test cannot leave its temporary database eligible for commit.
- Remaining warning: third-party `StarletteDeprecationWarning` from FastAPI's `testclient.py:1` about `httpx` use.
- Commit: ae7cf55.

### Evaluation harness
- Status: Complete at 2026-10-17.
- Test count: 135 tests passing in the full suite; one existing third-party StarletteDeprecationWarning from FastAPI's `testclient.py:1`.
- Corrected comparison uses all 40 rows in both numeric-band tables. Suspicious-as-not-scam: transformer accuracy/F1 0.700/0.727, LSTM 0.700/0.727, rules 0.900/0.895, full system 0.800/0.800. Suspicious-as-scam: transformer 0.675/0.711, LSTM 0.700/0.727, rules 0.900/0.895, full system 0.700/0.739. No scores were unavailable.
- Rules-only outperformed the full system under both treatments. The earlier conclusion comparing different row sets is withdrawn. This set is synthetic and the rule phrases share its construction process, so the rules result is an upper bound, not evidence of generalization.
- Full-system errors and masked examples are listed for both numeric-band treatments in `eval/results.md`. With Suspicious treated as not scam, 1 of 4 false negatives were previously in the Suspicious score band. With Suspicious treated as scam, 5 of 9 false positives were previously in the Suspicious score band.
- Reporting correction: row 2 verdict category is `Uncertain: verify manually`; the first numeric-band table counted its score of 43 as its one Suspicious row. The report now records categories for every row, category totals, and an Uncertain-as-own-outcome table (11 uncertain rows, 4 scam and 7 safe; 29 included).
- Diagnostic: row 2 fired `URGENT_BLOCK` (0.85), row 5 had no rule evidence, row 10 fired `JOB_FEE` (0.80), and row 15 fired `UPI_COLLECT` (0.80). The component table and weighted contributions were reported using masked text; rule scores of 80 on rows 10 and 15 were diluted below 55 by low model contributions, while row 5 is a rule-coverage gap.
- Scoring weights were not tuned and remain unchanged: transformer 0.40, rules 0.20, LSTM 0.15, links 0.15, sender 0.10. Any weight change requires a separate held-out set.
- Problems found and fixes: quoted and normalized CSV fields after validation found shifted columns and leading whitespace; fixed the dataset. Added the repository root to the runner import path after the direct command initially failed. Corrected the evaluator to count all 40 rows in both numeric Suspicious treatments and added category-aware reporting with `--show-row N`. The two existing numeric-band tables retain their prior metrics; the new Uncertain treatment excludes 11 rows and reports its 29-row denominator.
- Full suite after reporting update: 135 passed; one third-party StarletteDeprecationWarning from FastAPI testclient.py.
- Phase 2 reporting close-out commit: d476e8e.

## Phase 3: Integration and quality
Status: In progress.
- Quality list:
  - Validate model probabilities are within [0, 1] before constructing CheckResult scores.
  - README must cite the UCI SMS Spam Collection (Almeida and Gómez Hidalgo) under CC BY 4.0.
  - BiLSTM (St3w31) licence remains unverified and independently blocks shipping.
  - The Transformer currently has weight 0.40; replacing it changes every verdict. Defer a model swap and any fusion or weight decision until an independent Indian set exists.

### Uncertain verdict review and dashboard presentation
- Analysis of the 40-row synthetic set is diagnostic only, not tuning evidence. Of 11 uncertain rows, 4 are scam and 7 are safe. Each standalone model is correct on 5 of 11 uncertain rows. The disagreement pattern is mixed: LSTM confident while transformer is not on rows 2, 5, 29, 33, and 37; transformer confident while LSTM is not on rows 9, 20, 28, and 30; rows 25 and 32 are moderate. No uncertain row scores at least 80; rows 9 and 20 score 55 to 79. Across all 40 rows, mean absolute disagreement is 0.245902, maximum is 0.999633, and 11 are above 0.4. This corrects the earlier hypothesis that LSTM is the main driver.
- Dashboard now presents uncertain scores of 55 or higher with the headline "Likely scam. The two models disagree, so verify before acting." Scores below 55 use "Verify manually. The two models disagree." The score and unchanged verdict category remain visible; other categories render as before.
- Test count: 138 passing in the full suite; one third-party StarletteDeprecationWarning from FastAPI's test client.
- Held-out independence audit found 7 safe rows in `heldout_v2.csv` overlap everyday topics in the 40-row `check_set.csv`, above the threshold of 2. Overlaps include OTP/authentication, shop/transfer receipts, rail tickets, delivery notices, group contributions, and shared-cost payments.
- Row replaced because its safe phrase overlapped check_set.csv row 37. Replacement chosen before any evaluation run. The replacement still shared a travel-ticket topic with safe check_set.csv row 32.
- `heldout.csv`, `heldout_v2.csv`, and the moved agent draft are superseded and were never evaluated. No independent held-out result exists. The owner selected the public SMS dataset option as the next source to review; obtain an independent set from outside the project before evaluation. Do not tune weights, thresholds, or fusion until then.
- Dashboard presentation commit: dbb1b63.

### External public dataset pre-registration
- Source: UCI SMS Spam Collection. Licence checked: “This dataset is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license”; sharing and adaptation are permitted with appropriate credit. Source: https://archive.ics.uci.edu/dataset/228/sms%2Bspam%2Bcollection.
- Mapping: spam = positive label, ham = negative label. Results describe spam detection, not scam detection.
- Seed: 20261017. Sample 20 spam and 20 ham with random.Random(20261017) from the file's rows.
- Exclusion rule, fixed now: drop a sampled row only if it contains a digit run of 10 or more, or an email address. Replace it by drawing the next unsampled row from the same class using the same seed order. Record every replacement.
- LSTM is reported but flagged: “Contaminated, trained on this dataset. Excluded from conclusions.”
- No tuning on this set. If a result is poor, record it; do not change code.
- Evaluation interpretation: this is a spam-detection generalization check, not a scam-detection or Indian-coverage result. SCAMBERT training-source overlap is unknown. Rules are expected to perform poorly on Western spam; that is a coverage finding, not a fusion finding.
- Pre-registration was committed before downloading or sampling any dataset rows.

### External UCI spam sample (secondary diagnostic)
- Source: Almeida & Hidalgo (2011), UCI SMS Spam Collection, DOI https://doi.org/10.24432/C5CC84; dataset page https://archive.ics.uci.edu/dataset/228/sms%2Bspam%2Bcollection. UCI states CC BY 4.0 and permits sharing/adaptation with appropriate credit. The citation and attribution are included in `eval/external_results.md`.
- Sample: 40 rows, 20 spam mapped to `scam` and 20 ham mapped to `safe`; source field is `uci_sms_spam_collection`. The raw archive is kept outside the repository. Sampling used seed 20261017 and the preregistered digit-run/email exclusion.
- Replacements (one-based source row positions; excluded -> accepted): spam 4809->135, 390->4603, 5485->2805, 241->16, 57->251, 1689->4238, 2712->4579, 1090->1598, 4170->3863. Eleven subsequent spam candidates were also excluded by the fixed rule: 3969, 3, 4349, 1994, 2054, 2792, 4387, 5253, 2221, 1715, 5471. Ham had no exclusions or replacements.
- Results are spam-detection results only, not scam-detection accuracy and not evidence of Indian coverage. The first Suspicious-as-not-scam table has transformer, LSTM, and full system at 1.000 accuracy; rules-only is 0.550. LSTM is contaminated because it was trained on this dataset and is excluded from conclusions.
- Transformer result on the UCI sample (1.000) is marked "possible contamination, unverified. Excluded from conclusions." SCAMBERT training data is unlisted and overlap is plausible. With 40 of 40 correct, the approximate 95% accuracy interval is 0.91 to 1.00. The full-system tie means fusion passes through the transformer; it is not evidence about fusion. The absence of full-system false positives and false negatives is a positive plumbing check, not accuracy evidence.
- Rules-only low recall on this Western spam sample is a coverage finding, not a fusion finding.
- In the Suspicious-as-scam treatment, transformer and full system are 1.000 accuracy, LSTM is 0.975 (contaminated), and rules-only is 0.550. Category counts: Likely Safe 19, Suspicious 0, Likely Scam 18, High-Risk Scam 2, Uncertain 1 (ham). The Uncertain treatment excludes that one ham row and includes 39. Full-system false positives and false negatives are both zero at the 55-point boundary.
- No rules, weights, thresholds, or fusion changes were made. The UCI result is secondary; an independent owner-supplied set is still required before any fusion changes.
- Results commit: 99a80f5.

### Batched highlight scoring
- Highlights: 40-word median 581 ms (target 1,500 ms, met). 100-word median 3,156 ms (target 3,000 ms, missed). Accepted as a known limit. Option for later: sentence-level explanation for long messages, requires owner approval.
- Added `transformer.score_batch(texts)` using one padded model forward pass and optional batched scoring in `explain.highlights`; the single-text scorer and per-word explanation fallback remain available. Pipeline highlights still receive masked text only.
- Latency was measured end-to-end with real, warmed models and `use_reputation=False`, on the same synthetic messages before and after batching. Each figure is the median of three timed runs after a warm-up call. For 40 words: 979.2 ms before (runs 979.2, 952.5, 986.3 ms), 581.3 ms after (592.4, 581.3, 578.8 ms). For 100 words: 4,575.4 ms before (4,407.6, 4,701.1, 4,575.4 ms), 3,156.1 ms after (3,156.1, 3,142.9, 3,168.7 ms).
- The 40-word target of under 1,500 ms is met. The 100-word target of under 3,000 ms is missed; record 3,156.1 ms and stop this optimization task without changing model scores, weights, or thresholds.
- Added tests comparing batched and individual transformer probabilities on five samples within 1e-4, checking fixed-score explanation output and fallback behavior, and checking masked text reaches batch scoring.
- Full test suite: 142 passed; one third-party StarletteDeprecationWarning from FastAPI's test client.

### Style check and README
- Added `scripts/style_check.py` to scan tracked files for prohibited punctuation, emoji, and visual style violations, excluding evaluation CSV data and raw dataset paths. Added setup, model download and licence status, API and dashboard modes, test and style commands, evaluation caveats, UCI attribution, and limitations link to README.md.
- Style check initially reported en dashes at `scamshield/preprocess.py:19` and `scamshield/preprocess.py:20`. Replaced the literal separators with `\u2013` regex escapes, preserving separator behavior while removing the style violations. Resolved in Phase 1 commit `90bf956`; the style check now passes.
- Follow-up source check: `inspect.getsource` returned the two regex lines with escaped `\\u2013` sequences and no literal en-dash character; the `<U+2013>` shown in the earlier Before note was display notation only.
- Full test suite: 142 passed, one third-party `StarletteDeprecationWarning` from FastAPI's `testclient.py:1`.

### Integration pass
Status: Complete, 2026-10-17 at commit `d69300d`.
- `.gitignore` already contains `tests/*.db`; verified `tests/test_api_store.db` is ignored. No separate ignore change was needed.
- Clean clone: cloned `main` at `59bd0fa` into a new directory outside the working folder. Initial documented model download failed because `torch` and `transformers` were not installed by `requirements.txt`; README was clarified to install these runtime packages before downloading models. The corrected clean clone completed the sequence in about 6 minutes 17 seconds excluding the 62.61-second model download, under the 10-minute target. The model download completed successfully.
- At the original clean-clone integration run, Tesseract was not installed on that QA host and OCR was not exercised. This is resolved by the OCR verification below.
- Clean-clone tests after model download: 142 passed. Final style check printed `style check passed`; final full suite: 142 passed with one third-party `StarletteDeprecationWarning` from FastAPI's `testclient.py:1`.
- Live API: `/health` returned `status=ok` and `models_loaded=true`. A synthetic analysis returned a populated verdict and `scan_id`.
- Live dashboard: the same synthetic analysis displayed its verdict card, score, category, confidence, masked-text highlight, evidence checks, and report download control.
- API stopped: dashboard remained usable. The `ScamShield service is not running` warning appeared when opening API-backed History; reloading Analyze kept the form and navigation available but did not proactively show the warning.
- Privacy check: PASS. Searched the live SQLite database bytes for the placeholder phone and OTP; neither raw value was present. Only the pass result is recorded; no message content is stored in this log.
- README fix: documented installation of `torch` and `transformers`, which are required by the model downloader but absent from `requirements.txt`.
- Remaining independent set and model licence issues are unchanged; this integration pass does not resolve them.

### OCR verification
Status: Complete, 2026-10-17 at commit `4848507`.
- Installed UB Mannheim Tesseract `v5.4.0.20240606`. The executable was installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` but was not on the current shell's PATH. Added `TESSERACT_CMD` support in `scamshield/ocr.py` and documented the environment variable in README.md.
- Generated a runtime-only synthetic screenshot with the requested placeholder message. Direct `ocr.extract_text` output:
  > Your account is blocked. Share OTP 482913 now or call
  > 9876543210. Visit https://example.com/verify
- Keyword check: blocked found; OTP found; 482913 found; example.com found. Result: 4/4, pass.
- Live `/analyze-image`: HTTP 200, JSON verdict with `scan_id`. Response body contained neither raw placeholder number nor the complete unmasked OCR output. SQLite check passed: the stored `masked_text` contains phone and OTP mask markers and neither raw value; the database bytes also contain neither raw value.
- Initial failure-path observation (2026-10-17): missing Tesseract returned 422. Corrected this behavior in the OCR error-path fix below.
- Corrected failure paths: missing Tesseract or `pytesseract` now returns HTTP 503 with `{"error":"ocr_unavailable","message":"Screenshot reading is not available on this server. Paste the message text instead."}`. Invalid image upload and empty OCR results continue to return HTTP 422 JSON with `error` and `message`. Replaced both deprecated 422 constants in the image handler with `HTTP_422_UNPROCESSABLE_CONTENT`; this removes the handler deprecation warning.
- Style check passed. Full suite: 147 passed, 0 skipped, with one third-party Starlette test-client deprecation warning.
- OCR error-path correction committed as `Phase 3: OCR unavailable returns 503` at `e383199`.
- Added `tests/test_ocr.py` with an always-run missing-binary check and a live OCR keyword check. Full suite: 144 passed, 0 skipped, one third-party Starlette test-client deprecation warning. Style check passed.
- OCR is marked Complete because the keyword criterion and live endpoint privacy check passed. The generated screenshot was not committed.

### Candidate model benchmark
- Measurement only; no accuracy evaluation was run. Downloaded `omarash/sms-spam-distilbert` and `ealvaradob/bert-finetuned-phishing` into gitignored candidate directories without changing either production model.
- `omarash/sms-spam-distilbert`: `{0: ham, 1: spam}`, 2 labels, positive spam index 1. Canonical probabilities, classes 0 and 1: `(0.015586, 0.984414)`, `(0.014156, 0.985844)`, `(0.998204, 0.001796)`, `(0.604594, 0.395406)`.
- `ealvaradob/bert-finetuned-phishing`: `{0: benign, 1: phishing}`, 2 labels, phishing index 1. Canonical probabilities: `(0.000006, 0.999994)`, `(0.000005, 0.999995)`, `(0.999994, 0.000006)`, `(0.000416, 0.999584)`. The safe OTP canonical sentence is classified as phishing with high probability; four canonical checks do not establish a reliable scam mapping.
- CPU per-message medians (three timed runs after a warm-up): SMS DistilBERT 22.63 ms at 40 words and 42.70 ms at 100 words; phishing BERT 150.38 ms and 318.27 ms. Process RSS before load / after load / after 50 inferences: SMS DistilBERT 415.8 / 702.7 / 707.6 MiB; phishing BERT 415.7 / 450.5 / 1612.7 MiB. Peak working set after load / after 50 inferences: 718.1 / 718.1 MiB and 450.5 / 1612.7 MiB, respectively.
- Windows Python does not provide `resource`; memory was measured with `psutil` RSS and Windows `peak_wset` in a fresh process per model. Neither Hugging Face repository contains a separate LICENSE file; both metadata fields state `apache-2.0`. Preserve the license text and applicable notices before shipping. No model swap, production change, or accuracy evaluation was performed. Detailed probabilities and method are in `docs/LICENSES.md`.

### Production per-model memory profile
Status: Complete, 2026-10-17, at commits `edebd81` (profiler) and `b79cd8b` (log entries). Measurement only. No model, weight, threshold, or fusion setting was changed.

- Added `scripts/profile_model_memory.py` to profile the two production models, `models/scambert` (SCAMBERT) and `models/bilstm` (BiLSTM). The candidate models are out of scope. The script lives outside the `scamshield` package, is committed, and is not used at runtime. It requires `psutil`, which is a development-only dependency listed in `requirements-dev.txt` and deliberately kept out of the production `requirements.txt`.
- Method matches the candidate benchmark in `docs/LICENSES.md` so the figures are comparable: one fresh Python process per model, RSS from `psutil.Process().memory_info().rss`, and the Windows high-water working set `peak_wset`, in MiB rounded to one decimal. Runtime: Python 3.14.3, torch 2.10.0+cpu, transformers 5.17.0, 8 torch threads, `torch.no_grad()` inside `score()`. Both models loaded from their local snapshots, with no Hub download.
- Load path: `scamshield.models.transformer.score` and `scamshield.models.lstm.score`, each of which calls the module `_get_model()` lazy singleton builder on first use. Because the first production call performs load and inference together, "after load" is ambiguous, so both readings are reported.
- `peak_wset` is a per-process high water mark that never decreases, so the growth between consecutive readings is the meaningful figure. Cells are `rss / peak` in MiB with peak growth in brackets.
- Three modes per model plus one combined process: `staged` calls `_get_model()` and measures it with no inference yet, then measures the first `score()` separately; `first-call` preloads nothing, so one `score()` performs load and inference together, which is the production first-request path; `combined` imports both model modules in one fresh process, loads and runs one inference on each, and records peak after each. The API holds both models in a single process, so the combined figure is what a user actually receives.
- Inputs are fixed synthetic strings of the repeated placeholder word `message` at 40 and 100 words. No real message text is used, printed, or stored.

| Model | Mode | Baseline after imports | Load, singleton built | First inference | After 50 inferences |
|---|---|---:|---:|---:|---:|
| SCAMBERT | staged | 413.2 / 413.2 | 700.4 / 706.9 (+287.2 / +293.7) | 705.7 / 706.9 (+5.3 / +0.0) | 709.1 / 709.1 (+3.4 / +2.2) |
| SCAMBERT | first-call | 414.4 / 414.4 | 705.8 / 716.1 (+291.4 / +301.7) combined | n/a | 705.9 / 716.1 (+0.1 / +0.0) |
| BiLSTM | staged | 237.8 / 237.8 | 269.6 / 286.4 (+31.8 / +48.6) | 273.5 / 286.4 (+3.9 / +0.0) | 275.0 / 286.4 (+1.5 / +0.0) |
| BiLSTM | first-call | 238.3 / 238.3 | 275.3 / 288.5 (+37.0 / +50.2) combined | n/a | 275.3 / 288.5 (+0.0 / +0.0) |

Combined process, the figure a user receives, one fresh process holding both models, transformer loaded first:

| Stage | rss / peak (MiB) | Growth since previous |
|---|---:|---:|
| Baseline after importing both modules | 414.8 / 414.8 | n/a |
| After SCAMBERT first inference | 706.3 / 707.4 | +291.5 / +292.6 |
| After BiLSTM first inference | 737.7 / 752.4 | +31.4 / +45.0 |
| After 50 inferences of each | 739.2 / 752.4 | +1.5 / +0.0 |

The combined peak is **752.4 MiB**, with 739.2 MiB resident after 50 inferences of each model. A repeat full run gave 751.7 MiB peak and 738.8 MiB resident, so the combined figure reproduces within 1 MiB. Both models are held in one process, so this is below the 800 MiB team threshold. The measurement is a single sequential inference loop in one process, not concurrent load; see Open issue 11.

| Model | 40-word median latency (ms) | 100-word median latency (ms) |
|---|---:|---:|
| SCAMBERT | 20.26 | 46.02 |
| BiLSTM | 2.72 | 3.93 |

Latency uses one warm-up and three timed runs, medians shown, tokenization included, measured in the staged run only. Latency is a repeatability check, not the objective: a repeat single-model run gave BiLSTM 1.91 ms and 3.75 ms, so treat the short-message figures as indicative.

Findings:
1. Load dominates memory on both production models. Peak working set is reached when the weights load, before any inference. The first inference adds 0.0 peak for both models.
2. No per-inference growth over 50 inferences. SCAMBERT adds 2.2 MiB peak, BiLSTM adds 0.0, and the combined process adds 0.0.
3. The combined serving process peaks at **752.4 MiB** with 739.2 MiB resident, which is the figure that matters for the product, since the API holds both models in one process. It is below the 800 MiB criterion by 47.6 MiB.
4. The combined figure is well below the sum of the two separate peaks, 716.1 plus 288.5 equals 1004.6 MiB, because the transformers import is paid once in a combined process rather than once per model. The combined baseline of 414.8 MiB matches the transformer-only baseline of 413.2 MiB, not the sum of the two baselines, which confirms that shared cost.
5. Both production models are also individually below the 800 MiB criterion: SCAMBERT peak 716.1 MiB and BiLSTM peak 288.5 MiB. SCAMBERT has about 84 MiB of headroom, so it is inside the limit but not comfortable on its own.
6. Caveat on the criterion: the 800 MiB threshold is a team threshold taken from our own candidate benchmark work, not a platform requirement. It is also not purely a model measure, because roughly 176 MiB of the SCAMBERT figure is fixed transformers import cost rather than model weight. That import cost does not make the model lighter or heavier; it means the criterion is being applied to a process figure that includes library overhead. If a combined figure ever exceeds the threshold, the response is an owner decision about the host, such as host sizing or process limits, and never a silent model change.
7. The import baseline differs by module: 413.2 MiB for `transformer` against 237.8 MiB for `lstm`, because `transformer.py` imports `AutoTokenizer` and `AutoModelForSequenceClassification` while `lstm.py` imports only `BertTokenizer`.
8. The load ambiguity is small but real. Staged "after load" peak is 706.9 against first-call 716.1 for SCAMBERT, and 286.4 against 288.5 for BiLSTM. Use the staged figure as the per-model peak and the first-call figure as the production first-request path. Run-to-run variation on these peaks is a few MiB, and the transformer first-call peak ranged from 707.5 to 716.1 across two runs, so single-run differences under about 10 MiB are not meaningful.
9. SCAMBERT latency of 20.26 ms at 40 words and 46.02 ms at 100 words is in line with the compact `omarash/sms-spam-distilbert` candidate at 22.63 ms and 42.70 ms recorded in `docs/LICENSES.md`, so that swap offers no latency gain.
10. The synthetic repeated-token inputs are out of distribution, so the first-score values, 0.749855 for SCAMBERT and 0.999947 for BiLSTM, are recorded only to confirm the measured path executed. They are not accuracy evidence.
11. Style check passed. Full suite: 147 passed, 0 skipped, one third-party Starlette test-client deprecation warning. The profiler is measurement tooling and adds no test.

## Phase 4: Website and launch gates
Status: Not started. Launch gates: custom domain, favicon, remove platform badge, privacy policy, terms, and legal review.
