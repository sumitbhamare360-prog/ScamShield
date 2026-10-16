External public dataset, spam treated as scam-positive. Spam detection only. LSTM contaminated. Not a scam-detection accuracy claim.

Source: Almeida & Hidalgo (2011), UCI SMS Spam Collection, https://doi.org/10.24432/C5CC84; UCI dataset page https://archive.ics.uci.edu/dataset/228/sms%2Bspam%2Bcollection. Licensed CC BY 4.0; attribution is provided.
Date: 2026-10-17
Evaluation code revision (HEAD before this results commit): `fd62cbfd15fdfaa4c9ad807c020da5a4060f3810`
Rows: 20 spam (mapped to scam-positive), 20 ham (mapped to safe). Sample size: 40.
Sampling: seed 20261017; class-specific rows were shuffled in original file order using one random.Random instance (spam then ham). The first 20 rows of each class were selected; excluded rows were replaced by the next unsampled eligible row in that class draw order.
Exclusion rule: a sampled row was excluded only for a digit run of 10 or more or an email address. Replacement positions are listed below as one-based source row positions; no message text is included in the log.
Model/data limitations: the LSTM was trained on this dataset, so its result is contaminated and excluded from conclusions. SCAMBERT training sources are not listed in its model card; overlap with this dataset is unknown, so its result is not clean evidence of generalization. This dataset measures English/mostly Western spam detection, not Indian scam coverage.
Rules are expected to perform poorly on Western spam. That is a rules coverage finding, not evidence about fusion quality.
Spam-positive boundary: 55.0; Suspicious score band: 30.0 to below 55.0. Missing scores count as not scam and are listed separately.

Replacement log (source row positions are one-based; excluded replacement candidates are skipped):
- spam: 4809->135, 390->4603, 5485->2805, 241->16, 57->251, 1689->4238, 2712->4579, 1090->1598, 4170->3863; excluded replacement candidates: 3969, 3, 4349, 1994, 2054, 2792, 4387, 5253, 2221, 1715, 5471.
- ham: none; excluded replacement candidates: none.

### Suspicious as not scam

| Configuration | Accuracy | Precision | Recall | F1 | Rows |
|---|---:|---:|---:|---:|---:|
| transformer | 1.000 | 1.000 | 1.000 | 1.000 | 40 |
| lstm (contaminated; excluded from conclusions) | 1.000 | 1.000 | 1.000 | 1.000 | 40 |
| rules | 0.550 | 1.000 | 0.100 | 0.182 | 40 |
| full system | 1.000 | 1.000 | 1.000 | 1.000 | 40 |

### Suspicious as scam

| Configuration | Accuracy | Precision | Recall | F1 | Rows |
|---|---:|---:|---:|---:|---:|
| transformer | 1.000 | 1.000 | 1.000 | 1.000 | 40 |
| lstm (contaminated; excluded from conclusions) | 0.975 | 0.952 | 1.000 | 0.976 | 40 |
| rules | 0.550 | 1.000 | 0.100 | 0.182 | 40 |
| full system | 1.000 | 1.000 | 1.000 | 1.000 | 40 |

### Full system: Uncertain as its own outcome
Uncertain rows are neither scam nor safe and are excluded. For included rows, Suspicious scores count as not scam.
Uncertain rows: 1 total, 0 spam, 1 ham. Included rows: 39 of 40.

| Configuration | Accuracy | Precision | Recall | F1 | Included rows |
|---|---:|---:|---:|---:|---:|
| full system | 1.000 | 1.000 | 1.000 | 1.000 | 39 |

Verdict category counts:

| Verdict category | Rows |
|---|---:|
| Likely Safe | 19 |
| Suspicious | 0 |
| Likely Scam | 18 |
| High-Risk Scam | 2 |
| Uncertain: verify manually | 1 |

Uncertain rows (true labels use the spam/ham mapping):

| Row | True label | Transformer probability | LSTM probability | Numeric score | Category |
|---:|---|---:|---:|---:|---|
| 31 | safe | 0.0003283685364294797 | 0.4307398200035095 | 9 | Uncertain: verify manually |

### Full-system false positives and false negatives (score >= scam-positive boundary)
- False positives: none.
- False negatives: none.

Unavailable scores:
- transformer: 0 rows (none).
- lstm (contaminated; excluded from conclusions): 0 rows (none).
- rules: 0 rows (none).
- full system: 0 rows (none).

### Interpretation
- Observed best by accuracy in the Suspicious-as-not-scam treatment is a three-way tie: transformer, LSTM, and full system at 1.000; the LSTM is contaminated, SCAMBERT overlap is unknown, and the full system includes both models. These figures do not establish which configuration generalizes. Rules-only scores 0.550.
- Descriptively, the full system ties transformer-only in both treatments and LSTM-only in the first treatment, exceeds LSTM-only in the second treatment, and exceeds rules-only in both. The LSTM comparisons are contaminated; transformer and full-system generalization remain uncertain because SCAMBERT training-source overlap is unknown.
- Transformer result: training-source overlap is unknown because the SCAMBERT model card does not list training sources; treat its score as inconclusive evidence of generalization.
- Rules-only performance on Western spam is expected to be low because this rule set targets Indian scam patterns. This is a coverage finding, not a fusion finding.
- No weights, rules, thresholds, or fusion behavior were changed or tuned on this set.
