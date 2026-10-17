# Model Licences

Status is as of the last check. Do not ship any model marked UNCONFIRMED.

| Model | Source | Licence | Status | Notes |
|---|---|---|---|---|
| Digvijay05/SCAMBERT | Hugging Face | Not stated | UNCONFIRMED: do not ship | Model card says "MIT (or your project's license)", which is a template phrase, not a grant. No license field in the YAML header. Contact the author for written permission or a clear licence. |
| St3w31/BiLSTMSpamClassifier | Hugging Face | Not verified | UNCONFIRMED: do not ship | Licence tag not confirmed from the model page. Verify before shipping. Model repo provides no vocab.txt or tokenizer.json; uses bert-base-uncased (Apache 2.0) for tokenization. Output mapping was inferred through testing rather than explicitly declared. |

## Model Candidate Audit

Last checked: 2026-10-17. The Hugging Face model card YAML metadata field is the source of the license identifier below. Card prose alone is not treated as a license grant. A missing `LICENSE` file is recorded separately from the metadata field.

| Candidate checked | YAML `license:` field | README/card prose | Files tab `LICENSE` | Size and parameters | Training domain and languages | License terms and assessment |
|---|---|---|---|---|---|---|
| [Digvijay05/SCAMBERT](https://huggingface.co/Digvijay05/SCAMBERT), currently redirects to [ThunderCrown/SCAMBERT](https://huggingface.co/ThunderCrown/SCAMBERT) | none found | Says `MIT (or your project's license)`; not a standard identifier or a clear grant | none found | 269 MB; 67M parameters | Card describes English SMS and short-form messages; underlying 8,438-sample training data source and language mix are not specified | License unresolved. UNCONFIRMED; do not ship. |
| [ealvaradob/bert-finetuned-phishing](https://huggingface.co/ealvaradob/bert-finetuned-phishing) | `apache-2.0` | Card describes phishing detection across URLs, email, SMS, and websites | none found | 1.34 GB; 336M parameters | Phishing dataset includes URL, email, SMS, and website text. Metadata and card identify English only. English-only limitation for Hinglish. | Apache-2.0: commercial use is permitted; include the license and preserve applicable notices/attribution; no share-alike requirement. The model is large for the intended laptop CPU use. |
| [omarash/sms-spam-distilbert](https://huggingface.co/omarash/sms-spam-distilbert) | `apache-2.0` | Card says English SMS spam/ham; model license follows the base model | none found | 269 MB; 67M parameters | Trained using all 5,574 messages in the UCI SMS Spam Collection. English-only limitation for Hinglish. This is spam detection, not the product's scam definition. | Apache-2.0: commercial use is permitted; include the license and preserve applicable notices/attribution; no share-alike requirement. Compact enough to consider for laptop CPU. UCI evaluation is contaminated because this model was trained on the complete UCI collection. |

Apache-2.0 terms were checked against the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) and the [Apache Software Foundation licensing FAQ](https://apache.org/foundation/license-faq.html). Apply the full license text and notice conditions when distributing; consult the license text for the exact obligations.

### Candidates without a metadata license field

- Digvijay05/SCAMBERT (now redirected to ThunderCrown/SCAMBERT): no `license:` field in the model card YAML; no repository `LICENSE` file. The prose phrase does not resolve licensing. Keep UNCONFIRMED.

### Candidate selection for the swap evaluation

Select `omarash/sms-spam-distilbert` as the first compact candidate to evaluate, subject to attribution and compliance with Apache-2.0. Its UCI result must be labelled contaminated and excluded from generalization conclusions because its training used the full UCI collection. It is English SMS spam detection, so it does not establish Hinglish or Indian scam coverage. The 40-row set must be rerun for a new model; use an independent Indian set before making a fusion or shipping claim.

### Candidate benchmark

Last checked: 2026-10-17. Measurement only; no accuracy evaluation was run. Both snapshots were downloaded into gitignored `models/candidates/` directories. Neither Hugging Face repository contains a separate `LICENSE` file; both metadata fields state `apache-2.0`. Keep the Apache-2.0 text and applicable attribution notices as a shipping step. The benchmark used Transformers on CPU, float32, with tokenization included in each timed inference. Each message length had one warm-up and three timed runs; medians are shown. The exact 40-word and 100-word inputs consisted of repeated synthetic `message` tokens. Each model ran in its own fresh Python process.

| Candidate | `id2label` | Labels | Scam-like positive index from canonical checks | 40-word latency, median (ms) | 100-word latency, median (ms) | RSS before load (MB) | RSS after load (MB) | RSS after 50 inferences (MB) | Peak RSS after load / after 50 inferences (MB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `omarash/sms-spam-distilbert` | `{0: ham, 1: spam}` | 2 | 1 (`spam`) | 22.63 | 42.70 | 415.8 | 702.7 | 707.6 | 718.1 / 718.1 |
| `ealvaradob/bert-finetuned-phishing` | `{0: benign, 1: phishing}` | 2 | 1 (`phishing`) | 150.38 | 318.27 | 415.7 | 450.5 | 1612.7 | 450.5 / 1612.7 |

| Candidate | Canonical 1 class probabilities `(0, 1)` | Canonical 2 `(0, 1)` | Canonical 3 `(0, 1)` | Canonical 4 `(0, 1)` |
|---|---:|---:|---:|---:|
| `omarash/sms-spam-distilbert` | `(0.015586, 0.984414)` | `(0.014156, 0.985844)` | `(0.998204, 0.001796)` | `(0.604594, 0.395406)` |
| `ealvaradob/bert-finetuned-phishing` | `(0.000006, 0.999994)` | `(0.000005, 0.999995)` | `(0.999994, 0.000006)` | `(0.000416, 0.999584)` |

Canonical inputs were the four fixed label-mapping sentences already listed in the Phase 1 evaluation record. The phishing candidate maps class 1 to `phishing`, not scam. It assigns class 1 probability 0.999584 to the canonical safe OTP sentence, so this four-sentence check does not establish a reliable scam mapping. The SMS candidate maps class 1 to `spam`; that is a spam label, not the product's scam definition. No accuracy or generalization claim follows from these checks.

Production per-model figures for comparison are recorded in `docs/PROGRESS.md` under "Production per-model memory profile": SCAMBERT peak 716.1 MiB and BiLSTM peak 288.5 MiB, with an import baseline of 413.2 MiB before any weight load, and load dominating on both. The combined process that holds both models, which is what the user actually receives, peaks at 752.4 MiB with 739.2 MiB resident. The transformers import is paid once in that combined process, so its figure is well below the sum of the two separate peaks.

Memory method: the requested Python `resource` module is unavailable in this Windows runtime. RSS values use `psutil.Process().memory_info().rss`; the peak column uses Windows `peak_wset`, the high-water working-set equivalent. Values are process RSS in MiB rounded to one decimal. The phishing candidate's working set grows sharply during inference; its 1.34 GB checkpoint size understates runtime memory needs. The compact candidate is substantially faster in this CPU benchmark. Both candidates are English-focused, and neither result establishes Hinglish or Indian scam coverage. No production model was changed or selected.

#### Memory investigation

Measured 2026-10-17 in three separate fresh CPU processes, each loading `ealvaradob/bert-finetuned-phishing` from its local candidate snapshot and running 500 inferences on the same synthetic 40-word input. The tokenizer was called for each inference, matching the production wrapper's per-call tokenization pattern. RSS is MiB from `psutil`; the initial reading is after model load and before inference. Each checkpoint records RSS after the next 50 inferences and `gc.collect()`.

| Execution mode | 0 | 50 | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 | 500 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Default grad mode | 450.5 | 1679.4 | 1688.3 | 1688.3 | 1688.3 | 1688.3 | 1688.2 | 1688.3 | 1688.3 | 1688.3 | 1688.3 |
| `torch.inference_mode()` | 450.5 | 1615.3 | 1615.3 | 1615.3 | 1615.3 | 1615.3 | 1615.3 | 1615.3 | 1615.3 | 1615.3 | 1615.3 |
| `torch.no_grad()` | 450.2 | 1599.4 | 1599.5 | 1599.5 | 1599.5 | 1599.5 | 1599.5 | 1599.5 | 1599.5 | 1599.5 | 1599.5 |

`gc.collect()` returned 0 collected objects at every checkpoint. RSS did not fall after collection; the `no_grad` reading rose from 1588.3 MiB immediately before collection at 50 to 1599.4 MiB after it, then plateaued. Growth is not linear: most of the increase happens during the first 50 calls and each mode is essentially flat from 100 through 500. Thus there is no evidence of an ongoing per-inference leak in this loop, but the plateau is above 800 MiB in all modes and is not acceptable for the stated criterion. `inference_mode()` did not avoid the large working-set increase.

Production code inspection: `scamshield/models/transformer.py` lines 31-54 tokenize separately on each `score()` call, then run the forward pass under `torch.no_grad()` at lines 47-48. `score_batch()` also tokenizes its supplied texts each call at lines 67-74 and uses `torch.no_grad()` at lines 75-76. It does not reuse tokenized tensors across calls. No code was changed and no accuracy evaluation was run.
