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
| [omarash/sms-spam-distilbert](https://huggingface.co/omarash/sms-spam-distilbert) | `apache-2.0` | Card says English SMS spam/ham; model license follows the base model | none found | 269 MB; 67M parameters | Trained using all 5,574 messages in the UCI SMS Spam Collection. English-only limitation for Hinglish. This is spam detection, not the product's scam definition. | Apache-2.0: commercial use is permitted; include the license and preserve applicable notices/attribution; no share-alike requirement. Compact enough to consider for laptop CPU, but runtime is not benchmarked. UCI evaluation is contaminated because this model was trained on the complete UCI collection. |

Apache-2.0 terms were checked against the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html) and the [Apache Software Foundation licensing FAQ](https://apache.org/foundation/license-faq.html). Apply the full license text and notice conditions when distributing; consult the license text for the exact obligations.

### Candidates without a metadata license field

- Digvijay05/SCAMBERT (now redirected to ThunderCrown/SCAMBERT): no `license:` field in the model card YAML; no repository `LICENSE` file. The prose phrase does not resolve licensing. Keep UNCONFIRMED.

### Candidate selection for the swap evaluation

Select `omarash/sms-spam-distilbert` as the first compact candidate to evaluate, subject to attribution and compliance with Apache-2.0. Its UCI result must be labelled contaminated and excluded from generalization conclusions because its training used the full UCI collection. It is English SMS spam detection, so it does not establish Hinglish or Indian scam coverage. The 40-row set must be rerun for a new model; use an independent Indian set before making a fusion or shipping claim.
