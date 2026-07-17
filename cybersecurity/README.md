# Cybersecurity Module — MorphoLock

**Owner:** Khushi Gupta (@khushi-builds)
**Branch:** `cybersecurity`

## What this module does

This module is the software security layer of MorphoLock.

It handles three things:

* Detecting scam-risk environments
* Verifying hardware tokens
* Simulating adversarial attacks

## Files

### `context_scanner.py`

Scans running processes for known remote access and screen-sharing tools (AnyDesk, TeamViewer, RustDesk, Zoom, Teams, etc).

Returns a risk integer from 0–100.

* 0 = safe environment
* 60+ = high risk, transaction should be blocked
* 90+ = critical, immediate block

Run:
`python context_scanner.py`

### `verification_server.py`

FastAPI server that acts as the bank backend.

Receives HMAC-SHA256 tokens from the Arduino and verifies:

1. Token has not been used before (replay attack prevention)
2. Token is less than 2000ms old (expiry check)
3. Token signature is valid (authenticity check)

Run:
`uvicorn verification_server:app --reload --port 8001`

### `redteam_attack.py`

Adversarial simulation script.

Loads stolen valid CSV data and attempts to inject it into the pipeline while hardware is stationary.

Demonstrates that software injection cannot bypass the hardware tremor gate.

Run:
`python redteam_attack.py`

### `test_verify.py`

Test script for the verification server.

Runs four scenarios:

* Valid token
* Replay attack
* Expired token
* Tampered token

Run:
`python test_verify.py`

### `training_data.csv`

Mock sensor data (10 samples) used for red-team testing.

Will be replaced with real enrollment data once hardware is ready.

## How to install dependencies

```bash
pip install psutil fastapi uvicorn pydantic requests
```

## Demo Evidence

* CLEAR scan (Risk 0/100) and THREAT scan (Risk 60/100) from Context Scanner
* Verification tests passing: APPROVED, REPLAY BLOCKED, EXPIRED, INVALID
* Red-Team attack defeated: SOFTWARE INJECTION DEFEATED, Tremor 0.012Hz
