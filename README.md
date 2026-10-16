# ScamShield

ScamShield analyzes SMS, WhatsApp, and email messages for signs of scams. It combines pretrained language models with rules and link checks, then explains the result. It can be used through an API or a Streamlit dashboard.

## Setup

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The model runtime packages are not included in `requirements.txt`. Install them before downloading or running the models:

```bash
pip install torch transformers
```

Image OCR requires Tesseract to be installed separately. Put it on `PATH`, or set `TESSERACT_CMD` to the full path of the executable (for example, `C:\Program Files\Tesseract-OCR\tesseract.exe`).

Download the pretrained models:

```bash
python scripts/download_models.py
```

The SCAMBERT and BiLSTM model licences are unconfirmed. Do not ship either model unless its licence is confirmed or written permission is obtained. See [docs/LICENSES.md](docs/LICENSES.md).

## Run the API

```bash
uvicorn scamshield.api:app --reload --port 8000
```

## Run the dashboard

For mock mode, which uses fixed example results and does not call the API:

```bash
SCAMSHIELD_MOCK=1 streamlit run dashboard/app.py
```

For live mode, start the API first, then run:

```bash
streamlit run dashboard/app.py
```

The dashboard uses `http://localhost:8000` by default. Set `SCAMSHIELD_API_URL` to use a different API address.

## Tests

```bash
python -m pytest tests/
```

## Style check

```bash
python scripts/style_check.py
```

## Evaluation

Run the synthetic check set with:

```bash
python eval/run_eval.py
```

The synthetic results are for development checks only, not accuracy claims. The external UCI sample describes spam detection, not scam detection; the LSTM is contaminated by training on that dataset, and possible SCAMBERT contamination is unverified. These results are not accuracy claims. Do not tune scoring weights on an evaluation set.

Spam examples used in external evaluation are from the UCI SMS Spam Collection (Almeida and Gomez Hidalgo), licensed under CC BY 4.0. Source: https://archive.ics.uci.edu/dataset/228/sms%2Bspam%2Bcollection

## Limitations

See [Known limitations in the project context](docs/CONTEXT.md#9-known-limitations) for current model, scoring, and runtime limitations.

## Project documentation

- [docs/CONTEXT.md](docs/CONTEXT.md): architecture, contracts, scoring, and known limitations.
- [docs/PROGRESS.md](docs/PROGRESS.md): project status and open issues.
- [docs/RULES.md](docs/RULES.md): heuristic rules.
- [docs/LICENSES.md](docs/LICENSES.md): model licence audit.
