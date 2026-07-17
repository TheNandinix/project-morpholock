# 🔐 MorphoLock
### Hybrid Hardware-Software Behavioral Attestation Framework for Banking Fraud Prevention

**Team VYUH** | MNNIT Prayagraj Hackathon 2026 — Cyber Security PSBs Hackathon Series
Hosted by MNNIT Allahabad, DFS, IBA, Central Bank of India

---

## The Problem

Traditional software-only behavioral authentication (swipe speed, mouse tracking) can be recorded and replayed by malware and Remote Access Trojans. Authorized Push Payment (APP) scams bypass these defenses entirely because the legitimate, willing user is manipulated into completing the transaction themselves while a fraudster watches via screen-sharing tools.

**MorphoLock solves this with a three-layer biological + contextual + cryptographic defense that cannot be faked by software alone.**

---

## How It Works — Three Layers

### Layer 1 — Biological (Neuromuscular Micro-Tremor Detection)
Every human hand vibrates at 8–12 Hz due to involuntary muscle and nervous system activity — invisible to the eye, impossible for software to fake. An MPU6050 sensor captures accelerometer and gyroscope data at ~100Hz. A Fast Fourier Transform (FFT) isolates this biological frequency band, extracting 12 features (4 per axis: tremor power, peak frequency, total power, low-frequency power for X, Y, Z axes). An Isolation Forest model — trained on the legitimate user's unique tremor signature — flags any mismatch as anomalous.

### Layer 2 — Environmental (Context-Aware Scam Detection)
A real-time process scanner detects active screen-sharing or remote-access tools (AnyDesk, TeamViewer, RustDesk, Zoom, Microsoft Teams). **Critical design decision:** detection of any such tool triggers an automatic hard block — independent of how well the biological tremor matches. This is intentional: APP scams succeed precisely because the legitimate, willing user authorizes the transaction themselves while being coached by a fraudster. A perfect biometric match does not mean the transaction is safe if a third party is actively watching the screen.

### Layer 3 — Cryptographic (Hardware-Bound Signing)
Only if Layers 1 and 2 pass does the system proceed to signing. The bank server issues a one-time challenge (nonce = Transaction ID + Amount + Timestamp). The hardware device — never the software layer — computes `HMAC-SHA256(nonce, secret_key)` using a key that physically never leaves the chip. The resulting token is valid for only 2000 milliseconds and cannot be reused, defeating replay attacks even if intercepted.

---

## System Architecture

User touches sensor

↓

MPU6050 reads Accelerometer + Gyroscope (~100Hz) via Arduino Nano

↓

200 readings streamed over USB Serial to Python backend

↓

FFT signal processing → 12 features extracted (8-12Hz biological band)

↓

Isolation Forest scores tremor match (trained on owner's signature)

↓

Context scanner checks for active remote-access tools

↓

Risk Engine combines all signals:

• Active threat detected → HARD BLOCK (overrides everything)

• Score < 30  → APPROVED → proceed to signing

• Score 30-69 → STEP-UP → request secondary verification

• Score ≥ 70  → BLOCKED

↓

Arduino computes HMAC-SHA256(nonce, secret_key) → returns signed token

↓

Verification server checks token validity + expiry (<2000ms)

↓

TRANSACTION APPROVED or REJECTED

---

## Repository Structure

project-morpholock/

├── hardware/              Arduino firmware — 100Hz sampling, HMAC signing

├── cybersecurity/         Context scanner, verification server, red-team attack simulation

├── ml_pipeline/           FFT feature extraction, Isolation Forest training, data enrollment

├── dashboard/             Risk engine, transaction pipeline, live Streamlit dashboard

├── data/                  Training CSV files (not version controlled)

├── models/                Trained model file morpholock_model.pkl (not version controlled)

└── requirements.txt       Python dependencies

---

## Configuration

Before running, set the following:

1. **Serial port** — `main_pipeline.py` defaults to `COM4`. Open Device Manager → 
   Ports (COM & LPT) to find your actual port, and update the `SERIAL_PORT` 
   variable at the top of `main_pipeline.py` accordingly.
2. **HMAC secret key** — stored in `hardware/hmac_signing.ino` as `secret_key`. 
   For your own deployment, regenerate this value and re-flash the Arduino 
   before use; never reuse the key committed in this repository's history.
3. **Model path** — place `morpholock_model.pkl` at `models/morpholock_model.pkl`. 
   To train your own model from scratch, run `enroll_data.py` to capture your 
   tremor signature, then `train_model.py` to train it.

## Environment Requirements

- Python 3.10.x
- **scikit-learn==1.6.1 (required, exact version)** — the shipped model was 
  trained on this version; mismatched versions produce load warnings
- Arduino IDE 1.8.x or 2.x, with the MPU6050 library installed
- Tested on Windows 11; should run on macOS/Linux with no code changes, 
  but only Windows has been verified

## License

MIT License — see LICENSE file.

## Running the System

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the live dashboard
streamlit run dashboard/app.py

# Run a single transaction test (requires Arduino on COM4)
python dashboard/main_pipeline.py

# Run the cybersecurity verification server
uvicorn cybersecurity.verification_server:app --port 8001
```

---

## The Demo

The dashboard presents four controls:
- **Human transaction** — simulates a legitimate user → green APPROVED
- **Replay attack** — simulates a flat, motionless device (software injection) → red BLOCKED
- **Screen-share threat** — simulates AnyDesk detection → red BLOCKED (hard override)
- **Live sensor** — connects to the actual Arduino hardware for a real end-to-end transaction

The first three are simulation controls for demonstration reliability; the fourth drives the real physical pipeline.

---

## Production Deployment Vision

| Channel | Where the sensor lives | Where the key lives |
|---|---|---|
| Mobile / UPI | Phone's built-in IMU (SensorManager / CoreMotion) | ARM TrustZone / Secure Enclave |
| Internet Banking | Paired mobile device (cross-device push attestation) | User's phone Secure Enclave |
| ATM | Encrypted PIN Pad (EPP) — embedded IMU | EPP hardware module |

The Arduino Nano + MPU6050 prototype is a direct physical stand-in for hardware already present in production banking infrastructure — every component maps to a real, deployable equivalent.

---

## Regulatory Compliance — DPDP Act 2023

**Zero Biometric Data Transmission.** Raw physiological time-series data and frequency-domain features are processed entirely within local device memory and immediately discarded. The only artifact transmitted over the banking network is the mathematically irreversible HMAC-SHA256 token — not the underlying biometric data itself. This satisfies Section 4(1)(b) (purpose limitation) and Section 8(7) (data minimization) of the DPDP Act 2023.

---

## Honest Limitations & Roadmap

We believe transparency about current constraints is essential to responsible security engineering:

- **Single-user enrollment per device.** The model is trained on one individual's tremor signature. A different person (e.g., a family member using a shared device) will correctly be flagged as anomalous — this is by design, not a flaw. The system routes such cases to secondary verification (OTP/face-ID) rather than a hard lock, preserving legitimate shared-access use cases common in Indian households while still requiring explicit owner approval.
- **Signature-based threat detection.** The context scanner currently recognizes named remote-access applications. A production system would extend this with telephony-state detection (active call during transaction) and behavioral hesitation-pattern analysis characteristic of guided scam victims.
- **Retraining boundary.** Only transactions that complete via frictionless biometric APPROVAL are eligible for the rolling retraining window — sessions requiring step-up verification are explicitly excluded, preventing model drift toward accepting unauthorized users over time.

---

## Team VYUH

| Member | Role | Contribution |
|---|---|---|
| Nandini | Team Lead, Systems Integrator | Risk engine, transaction pipeline, dashboard, integration |
| Kushagra | Hardware Lead | Arduino firmware, sensor calibration, HMAC signing |
| Khushi | Cybersecurity Lead | Context scanning, verification server, adversarial testing |
| Katyayni | ML Developer | Signal processing, feature engineering, model training |

---

*Built for the Cyber Security PSBs Hackathon Series 2026.*