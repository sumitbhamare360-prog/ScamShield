# ScamShield

Multichannel scam detection and explanation pipeline for SMS, WhatsApp, and Email.

## Quick Setup
1. Clone the repository and navigate into the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download pretrained models:
   ```bash
   python scripts/download_models.py
   ```

## Running the Application
- Start the API backend:
  ```bash
  uvicorn scamshield.api:app --reload --port 8000
  ```
- Start the Streamlit dashboard:
  ```bash
  streamlit run dashboard/app.py
  ```
- Run tests:
  ```bash
  python -m pytest tests/
  ```

## Documentation
- [docs/CONTEXT.md](docs/CONTEXT.md): Project architecture, data flow, contracts, scoring bands, and decisions.
- [docs/PROGRESS.md](docs/PROGRESS.md): Phase progress, current status, and open issues.
- [docs/RULES.md](docs/RULES.md): Heuristic rules reference table.
- [docs/LICENSES.md](docs/LICENSES.md): Model license audit status.
