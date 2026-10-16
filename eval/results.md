Synthetic check set of 40 messages. For sanity checking only. Not a published accuracy claim.

Date: 2026-10-16
Evaluation code revision (HEAD before this results commit): `832fd41cf6d44054cd582f4f46730a400451fe47`
Rows: 20 scam, 20 safe; all sources synthetic.

Metrics exclude Suspicious scores from binary classification. Missing scores count as not positive and are listed separately.

| Configuration | Accuracy | Precision | Recall | F1 | Included rows |
|---|---:|---:|---:|---:|---:|
| transformer | 0.692 | 0.667 | 0.800 | 0.727 | 39 |
| lstm | 0.700 | 0.667 | 0.800 | 0.727 | 40 |
| rules | 0.900 | 0.944 | 0.850 | 0.895 | 40 |
| full system | 0.794 | 0.800 | 0.842 | 0.821 | 34 |

Suspicious result counts:
- transformer: 1 rows (37).
- lstm: 0 rows (none).
- rules: 0 rows (none).
- full system: 6 rows (2, 28, 29, 30, 32, 37).

Unavailable score counts:
- transformer: 0 rows (none).
- lstm: 0 rows (none).
- rules: 0 rows (none).
- full system: 0 rows (none).

### transformer
- False positives:
  - Row 22: Delivery update: your parcel is out for delivery today. Track it in the courier app
  - Row 24: Reminder: your appointment is tomorrow at 10 AM. Reply if you need to reschedule
  - Row 26: Your monthly bank statement is ready in the official banking app
  - Row 28: Your library book is due next Friday. Renew it in the library app if needed
  - Row 29: Meeting moved to 3 PM in room 4. Please bring the project notes
  - Row 30: Your electricity bill payment was received. No action is needed
  - Row 32: The train to Pune leaves at 6 PM. The ticket is saved in the railway app
  - Row 35: Your course enrollment is confirmed. Classes start on Monday
- False negatives:
  - Row 2: Bank support bol raha hai OTP turant bhejo warna account band ho jayega
  - Row 5: PAN and Aadhaar KYC pending hai. Is link par details verify karo https://update-example.com
  - Row 10: Part-time job mila hai. Training fee jama karo aur guaranteed income pao
  - Row 15: Main UPI collect request bhej raha hoon, receive karne ke liye PIN enter karo

### lstm
- False positives:
  - Row 22: Delivery update: your parcel is out for delivery today. Track it in the courier app
  - Row 24: Reminder: your appointment is tomorrow at 10 AM. Reply if you need to reschedule
  - Row 25: I sent you Rs 500 for the shared groceries yesterday
  - Row 26: Your monthly bank statement is ready in the official banking app
  - Row 29: Meeting moved to 3 PM in room 4. Please bring the project notes
  - Row 33: Your medicine refill is ready for pickup at the clinic pharmacy
  - Row 35: Your course enrollment is confirmed. Classes start on Monday
  - Row 37: Your grocery order has been delivered to the front desk
- False negatives:
  - Row 9: Work from home job offer: earn daily, pay a registration fee to begin
  - Row 10: Part-time job mila hai. Training fee jama karo aur guaranteed income pao
  - Row 15: Main UPI collect request bhej raha hoon, receive karne ke liye PIN enter karo
  - Row 20: Income tax department final notice: pay the penalty today or face legal action

### rules
- False positives:
  - Row 22: Delivery update: your parcel is out for delivery today. Track it in the courier app
- False negatives:
  - Row 3: Your verification code is [OTP:****]. Tell it to our agent to stop account closure
  - Row 5: PAN and Aadhaar KYC pending hai. Is link par details verify karo https://update-example.com
  - Row 14: Please pay via UPI to confirm your booking. Scan this link https://pay-example.com

### full system
- False positives:
  - Row 22: Delivery update: your parcel is out for delivery today. Track it in the courier app
  - Row 24: Reminder: your appointment is tomorrow at 10 AM. Reply if you need to reschedule
  - Row 26: Your monthly bank statement is ready in the official banking app
  - Row 35: Your course enrollment is confirmed. Classes start on Monday
- False negatives:
  - Row 5: PAN and Aadhaar KYC pending hai. Is link par details verify karo https://update-example.com
  - Row 10: Part-time job mila hai. Training fee jama karo aur guaranteed income pao
  - Row 15: Main UPI collect request bhej raha hoon, receive karne ke liye PIN enter karo

Scoring weights used:
- transformer: 0.40
- rules: 0.20
- lstm: 0.15
- links: 0.15
- sender: 0.10

Scoring weights were not tuned on this set. Results are development sanity checks only.

Check-set row text is synthetic. False-positive and false-negative examples above use preprocessed masked text only.
