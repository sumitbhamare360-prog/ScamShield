# Rules Reference

Table of heuristic rules implemented in `scamshield/rules.py`.

| Rule ID | Severity | Reason |
|---|---|---|
| OTP_REQUEST | 0.95 | requests an OTP; real banks and services never ask for it |
| OTP_HINGLISH | 0.90 | requests OTP in Hinglish phrased urgency |
| URGENT_BLOCK | 0.85 | claims your account or service will be immediately blocked or suspended |
| KYC_UPDATE | 0.85 | coerces immediate KYC or PAN update via unverified channels |
| TURANT_VERIFY_HINGLISH | 0.80 | pressures urgent verification in Hinglish to induce panic |
| ACCOUNT_BAND_HINGLISH | 0.85 | threatens account closure in Hinglish |
| UPI_COLLECT | 0.80 | requests approving a UPI collect request or entering PIN to receive funds |
| PRIZE_CLAIM | 0.85 | claims you have won a lottery, gift, or contest requiring a claim action |
| COURIER_FEE | 0.75 | claims parcel or package delivery is stuck and requires immediate fee payment |
| JOB_FEE | 0.80 | offers high daily income or part-time work requiring an initial deposit or fee |
| GUARANTEED_RETURNS | 0.85 | promises unrealistic risk-free high profits or guaranteed investment returns |
| CRYPTO_PROMO | 0.75 | unsolicited cryptocurrency or token investment scheme promotion |
| AUTHORITY_IMPERSONATION | 0.90 | impersonates law enforcement, police, CBI, RBI, or government department |
| DIGITAL_ARREST | 0.95 | fabricates a digital arrest or legal custody notice |
| SHORTENED_LINK | 0.65 | uses URL shorteners commonly associated with masking malicious destinations |
| REMOTE_ACCESS_APP | 0.90 | urges installation of remote screen sharing or access tools |
| APK_DOWNLOAD | 0.85 | requests downloading an Android APK package directly rather than official app stores |
| ELECTRICITY_BILL_CUT | 0.85 | threatens immediate electricity disconnection due to supposed unpaid bill |
| REFUND_TRAP | 0.75 | claims an unexpected refund or tax rebate is waiting to be processed |
| PASSWORD_RESET_UNSOLICITED | 0.70 | unsolicited security alert pushing a password reset or validation link |
| THREAT_OF_ACTION | 0.80 | uses aggressive intimidation or deadline threats |
| FAKE_CUSTOMER_CARE | 0.75 | shares non-standard customer care phone numbers to divert users |
| CREDIT_SCORE_FIX | 0.70 | claims ability to artificially boost CIBIL or credit score instantly |
| PRE_APPROVED_LOAN | 0.70 | unsolicited pre-approved loan with zero documentation requiring processing fee |
| TELEGRAM_INVESTMENT | 0.80 | solicits users to join private Telegram channel for investment or tasks |
| CHARITY_FRAUD | 0.70 | manipulative appeal for emergency donation via direct personal UPI |
| CARD_EXPIRY_SPOOF | 0.75 | falsely claims ATM/Debit card expiration requiring details confirmation |
| OFFER_EXPIRES_SOON | 0.60 | creates artificial scarcity with expiring offer countdown |
