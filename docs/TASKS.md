# Workstream Tasks

| ID | Owner | Files owned | Status | Notes | Requests |
|---|---|---|---|---|---|
| S | Scaffolder | scamshield/schemas.py, scamshield/config.py, docs/CONTEXT.md, docs/TASKS.md, README.md, requirements.txt, .gitignore, all stub files | Complete | All directories and stubs generated. Clean schema validation and imports verified. | None |
| A | Agent-A | scamshield/preprocess.py, scamshield/rules.py, scamshield/ocr.py, docs/RULES.md, tests/test_preprocess.py, tests/test_rules.py | Complete | Masking, extraction, 28 rules, and OCR implemented; 33 unit tests passing. | None |
| B | Agent-B | scamshield/models/transformer.py, scamshield/models/lstm.py, scamshield/models/explain.py, scripts/download_models.py, docs/LICENSES.md, tests/test_models.py | Complete | SCAMBERT CPU latency: 16.22 ms/msg (Peak Mem 762.0 MB); BiLSTM CPU latency: 2.08 ms/msg (Peak Mem 763.5 MB); MIT licenses verified; tests passing. | None |
| C | Agent-C | scamshield/links.py, scamshield/sender.py, data/brands.json | Pending | Implements reputation, domain checks, spoof detection, and blocklist checking. | None |
| D | Agent-D | scamshield/scoring.py, scamshield/advice.py, scamshield/pipeline.py | Pending | Implements score fusion, advice/action generation, and full pipeline flow. | None |
| E | Agent-E | scamshield/store.py, scamshield/api.py | Pending | Implements SQLite persistence (masked only) and full REST endpoints. | None |
| F | Agent-F | dashboard/app.py, dashboard/assets/ | Pending | Implements Streamlit interface connecting to API on localhost. | None |
| H | Agent-H | data/eval/, tests/ | Pending | Implements evaluation metrics and test suites across datasets. | None |
| I | Agent-I | scripts/ | Pending | Integration verification, smoke tests, and operational runner scripts. | None |
| W | Agent-W | website/ | Pending | Documentation, user guides, and web asset maintenance. | None |
