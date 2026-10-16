Synthetic check set of 40 messages. For sanity checking only. Not a published accuracy claim.

Date: 2026-10-17
Evaluation code revision (HEAD before this results commit): `a6ea1591c00c8624b0058858620ad7f3efc65a3b`
Rows: 20 scam, 20 safe; all sources synthetic.

All metrics use all 40 rows. Missing scores count as not scam and are listed separately. Suspicious band: 30 to below 55; scam-positive boundary: 55.
Suspicious in the first two tables is a numeric score band; a user-facing verdict category may instead be Uncertain.

### Suspicious as not scam

| Configuration | Accuracy | Precision | Recall | F1 | Rows |
|---|---:|---:|---:|---:|---:|
| transformer | 0.700 | 0.667 | 0.800 | 0.727 | 40 |
| lstm | 0.700 | 0.667 | 0.800 | 0.727 | 40 |
| rules | 0.900 | 0.944 | 0.850 | 0.895 | 40 |
| full system | 0.800 | 0.800 | 0.800 | 0.800 | 40 |

### Suspicious as scam

| Configuration | Accuracy | Precision | Recall | F1 | Rows |
|---|---:|---:|---:|---:|---:|
| transformer | 0.675 | 0.640 | 0.800 | 0.711 | 40 |
| lstm | 0.700 | 0.667 | 0.800 | 0.727 | 40 |
| rules | 0.900 | 0.944 | 0.850 | 0.895 | 40 |
| full system | 0.700 | 0.654 | 0.850 | 0.739 | 40 |

### Full system: Uncertain as its own outcome
Uncertain rows are neither scam nor safe and are excluded. For included rows, Suspicious scores count as not scam.
Uncertain rows: 11 total, 4 scam, 7 safe. Included rows: 29 of 40.

| Configuration | Accuracy | Precision | Recall | F1 | Included rows |
|---|---:|---:|---:|---:|---:|
| full system | 0.793 | 0.778 | 0.875 | 0.824 | 29 |

Verdict category by row:

| Row | Actual label | Verdict category | Score | Uncertain |
|---:|---|---|---:|---|
| 1 | scam | High-Risk Scam | 83 | False |
| 2 | scam | Uncertain: verify manually | 43 | True |
| 3 | scam | Likely Scam | 73 | False |
| 4 | scam | High-Risk Scam | 83 | False |
| 5 | scam | Uncertain: verify manually | 16 | True |
| 6 | scam | High-Risk Scam | 100 | False |
| 7 | scam | High-Risk Scam | 80 | False |
| 8 | scam | High-Risk Scam | 96 | False |
| 9 | scam | Uncertain: verify manually | 75 | True |
| 10 | scam | Likely Safe | 29 | False |
| 11 | scam | Likely Scam | 78 | False |
| 12 | scam | Likely Scam | 78 | False |
| 13 | scam | High-Risk Scam | 100 | False |
| 14 | scam | Likely Scam | 75 | False |
| 15 | scam | Likely Safe | 21 | False |
| 16 | scam | High-Risk Scam | 99 | False |
| 17 | scam | High-Risk Scam | 82 | False |
| 18 | scam | High-Risk Scam | 100 | False |
| 19 | scam | High-Risk Scam | 80 | False |
| 20 | scam | Uncertain: verify manually | 77 | True |
| 21 | safe | Likely Safe | 0 | False |
| 22 | safe | High-Risk Scam | 93 | False |
| 23 | safe | Likely Safe | 0 | False |
| 24 | safe | Likely Scam | 73 | False |
| 25 | safe | Uncertain: verify manually | 13 | True |
| 26 | safe | Likely Scam | 73 | False |
| 27 | safe | Likely Safe | 13 | False |
| 28 | safe | Uncertain: verify manually | 53 | True |
| 29 | safe | Uncertain: verify manually | 51 | True |
| 30 | safe | Uncertain: verify manually | 53 | True |
| 31 | safe | Likely Safe | 0 | False |
| 32 | safe | Uncertain: verify manually | 34 | True |
| 33 | safe | Uncertain: verify manually | 18 | True |
| 34 | safe | Likely Safe | 0 | False |
| 35 | safe | Likely Scam | 73 | False |
| 36 | safe | Likely Safe | 0 | False |
| 37 | safe | Uncertain: verify manually | 38 | True |
| 38 | safe | Likely Safe | 0 | False |
| 39 | safe | Likely Safe | 13 | False |
| 40 | safe | Likely Safe | 0 | False |

Verdict category counts:

| Verdict category | Rows |
|---|---:|
| Likely Safe | 11 |
| Suspicious | 0 |
| Likely Scam | 7 |
| High-Risk Scam | 11 |
| Uncertain: verify manually | 11 |

Suspicious counts before reclassification:
- transformer: 1 rows (37).
- lstm: 0 rows (none).
- rules: 0 rows (none).
- full system: 6 rows (2, 28, 29, 30, 32, 37).

Unavailable score counts:
- transformer: 0 rows (none).
- lstm: 0 rows (none).
- rules: 0 rows (none).
- full system: 0 rows (none).

### Full-system errors: Suspicious as not scam
- False positives: 4 rows; 0 were Suspicious before reclassification.
  - Row 22 (not Suspicious): Delivery update: your parcel is out for delivery today. Track it in the courier app
  - Row 24 (not Suspicious): Reminder: your appointment is tomorrow at 10 AM. Reply if you need to reschedule
  - Row 26 (not Suspicious): Your monthly bank statement is ready in the official banking app
  - Row 35 (not Suspicious): Your course enrollment is confirmed. Classes start on Monday
- False negatives: 4 rows; 1 were Suspicious before reclassification.
  - Row 2 (Suspicious before reclassification): Bank support bol raha hai OTP turant bhejo warna account band ho jayega
  - Row 5 (not Suspicious): PAN and Aadhaar KYC pending hai. Is link par details verify karo https://update-example.com
  - Row 10 (not Suspicious): Part-time job mila hai. Training fee jama karo aur guaranteed income pao
  - Row 15 (not Suspicious): Main UPI collect request bhej raha hoon, receive karne ke liye PIN enter karo

### Full-system errors: Suspicious as scam
- False positives: 9 rows; 5 were Suspicious before reclassification.
  - Row 22 (not Suspicious): Delivery update: your parcel is out for delivery today. Track it in the courier app
  - Row 24 (not Suspicious): Reminder: your appointment is tomorrow at 10 AM. Reply if you need to reschedule
  - Row 26 (not Suspicious): Your monthly bank statement is ready in the official banking app
  - Row 28 (Suspicious before reclassification): Your library book is due next Friday. Renew it in the library app if needed
  - Row 29 (Suspicious before reclassification): Meeting moved to 3 PM in room 4. Please bring the project notes
  - Row 30 (Suspicious before reclassification): Your electricity bill payment was received. No action is needed
  - Row 32 (Suspicious before reclassification): The train to Pune leaves at 6 PM. The ticket is saved in the railway app
  - Row 35 (not Suspicious): Your course enrollment is confirmed. Classes start on Monday
  - Row 37 (Suspicious before reclassification): Your grocery order has been delivered to the front desk
- False negatives: 3 rows; 0 were Suspicious before reclassification.
  - Row 5 (not Suspicious): PAN and Aadhaar KYC pending hai. Is link par details verify karo https://update-example.com
  - Row 10 (not Suspicious): Part-time job mila hai. Training fee jama karo aur guaranteed income pao
  - Row 15 (not Suspicious): Main UPI collect request bhej raha hoon, receive karne ke liye PIN enter karo

Scoring weights used:
- transformer: 0.40
- rules: 0.20
- lstm: 0.15
- links: 0.15
- sender: 0.10

Scoring weights were not tuned on this set. Results are development sanity checks only.
Rules-only may be optimistic because this synthetic set and its rules share phrasing patterns; treat it as an upper bound, not evidence of generalization.

Check-set row text is synthetic. False-positive and false-negative examples above use preprocessed masked text only.
