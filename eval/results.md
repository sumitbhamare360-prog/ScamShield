Synthetic check set of 40 messages. For sanity checking only. Not a published accuracy claim.

Date: 2026-10-16
Evaluation code revision (HEAD before this results commit): `5f8e846c6dce0066c0d30b0a7ff4bed4897f312f`
Rows: 20 scam, 20 safe; all sources synthetic.

All metrics use all 40 rows. Missing scores count as not scam and are listed separately. Suspicious band: 30 to below 55; scam-positive boundary: 55.

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
