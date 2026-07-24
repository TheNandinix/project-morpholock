"""
main_pipeline.py
----------------
The coordinator of the entire MorphoLock system.
Reads live sensor data from Arduino, runs risk scoring,
sends SIGN command if approved, verifies HMAC token.

Author: Nandini (Team Lead)
"""

import serial
import time
import logging
import sys
import os
import requests

# ── Tell Python where to find our other project files ──
# This adds the project root folder to Python's search path
# So we can import risk_engine and context_scanner from anywhere
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dashboard.risk_engine import compute_risk_score

# ─────────────────────────────────────────────────────
# LOGGING SETUP
# Every important event gets printed with a timestamp
# ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# CONFIGURATION
# All settings in one place — easy to change
# ─────────────────────────────────────────────────────
COM_PORT         = "COM4"       # Kushagra's Arduino port
BAUD_RATE        = 115200       # Must match Arduino firmware
SAMPLES_NEEDED   = 200          # 2 seconds at 100Hz
VERIFY_URL       = "http://127.0.0.1:8001/verify"  # Khushi's server
TOKEN_VALID_MS   = 2000         # Token expires after 2 seconds


# ─────────────────────────────────────────────────────
# RISK SCORE SCALER (Added to map raw scores to 0-100)
# ─────────────────────────────────────────────────────
def scale_risk_score(raw_score: float) -> int:
    """
    Maps the raw Isolation Forest scores (e.g., 35 for holding, 46 for flat) 
    to a clean 0-100 percentage scale for the UI and logic.
    """
    min_score = 35.0  # Safe/Holding baseline
    max_score = 46.0  # Danger/Flat baseline
    
    # Calculate percentage
    risk = ((raw_score - min_score) / (max_score - min_score)) * 100
    
    # Clip between 0 and 100 to prevent weird numbers
    return int(max(0, min(100, risk)))


# ─────────────────────────────────────────────────────
# MOCK VERIFICATION
# Temporary stand-in for Khushi's verification server
# ─────────────────────────────────────────────────────
def mock_verify(nonce: str, token: str, timestamp: int) -> dict:
    logger.warning("Using MOCK verification — replace with real server later")
    return {
        "status": "APPROVED",
        "nonce": nonce,
        "age_ms": 150,
        "mock": True
    }


# ─────────────────────────────────────────────────────
# STEP 1 — READ SENSOR DATA FROM ARDUINO
# ─────────────────────────────────────────────────────
def collect_sensor_data(port: str = COM_PORT) -> list:
    logger.info(f"Connecting to Arduino on {port}...")
    window = []

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
        time.sleep(2)
        ser.flushInput()
        logger.info("Arduino connected. Collecting sensor data...")

        while len(window) < SAMPLES_NEEDED:
            try:
                raw = ser.readline().decode('utf-8').strip()
                if not raw or raw.startswith("READY") or raw.startswith("STATUS"):
                    continue

                parts = raw.split(",")
                if len(parts) == 6:
                    row = [float(x) for x in parts]
                    window.append(row)

            except (ValueError, UnicodeDecodeError):
                logger.debug("Skipped corrupted data line")
                continue

        ser.close()
        logger.info(f"Collected {len(window)} sensor readings successfully")
        return window, ser

    except serial.SerialException as e:
        logger.error(f"Could not connect to Arduino on {port}: {e}")
        logger.error("Check: Is Arduino plugged in? Is COM4 correct? Is Serial Monitor closed?")
        return None, None


# ─────────────────────────────────────────────────────
# STEP 2 — GET HMAC TOKEN FROM ARDUINO
# ─────────────────────────────────────────────────────
def request_signing(port: str, nonce: str) -> str:
    logger.info(f"Requesting HMAC signing for nonce: {nonce}")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
        time.sleep(1)

        command = f"SIGN:{nonce}\n"
        ser.write(command.encode())
        logger.info(f"Sent command: {command.strip()}")

        reply = ser.readline().decode('utf-8').strip()
        ser.close()

        if reply.startswith("TOKEN:"):
            token = reply[6:]
            logger.info(f"Token received: {token[:16]}...")
            return token
        else:
            logger.error(f"Unexpected reply from Arduino: {reply}")
            return None

    except serial.SerialException as e:
        logger.error(f"Signing failed — serial error: {e}")
        return None


# ─────────────────────────────────────────────────────
# STEP 3 — VERIFY TOKEN WITH BANK SERVER
# ─────────────────────────────────────────────────────
def verify_with_server(nonce: str, token: str) -> dict:
    timestamp_ms = int(time.time() * 1000)

    try:
        response = requests.post(
            VERIFY_URL,
            json={
                "nonce": nonce,
                "token": token,
                "timestamp": timestamp_ms
            },
            timeout=2 
        )
        return response.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.warning("Verification server not reachable — using mock")
        return mock_verify(nonce, token, timestamp_ms)


# ─────────────────────────────────────────────────────
# MASTER FUNCTION — run_transaction
# ─────────────────────────────────────────────────────
def run_transaction(transaction_id: str, amount: float) -> dict:
    logger.info("=" * 50)
    logger.info(f"NEW TRANSACTION: {transaction_id} | Amount: ₹{amount}")
    logger.info("=" * 50)

    timestamp = int(time.time())
    nonce = f"{transaction_id}_{int(amount)}_{timestamp}"
    logger.info(f"Nonce generated: {nonce}")

    # ── STEP 1: Collect sensor data ──
    window, _ = collect_sensor_data()
    if window is None:
        return {
            "decision": "BLOCKED",
            "reason": "Hardware not connected",
            "risk_score": 100,
            "transaction_id": transaction_id
        }

    # ── STEP 2: Get context scan ──
    try:
        from cybersecurity.context_scanner import scan_environment
        context_result = scan_environment()
    except ImportError:
        logger.warning("context_scanner.py not found — using empty context")
        context_result = {"risk_score": 0, "threats": [], "status": "UNKNOWN"}

    # ── STEP 3: Compute risk score & Scale it ──
    risk_result = compute_risk_score(window, context_result)
    raw_risk_score = risk_result["risk_score"]
    
    # SCALE THE SCORE (maps 35-46 to 0-100)
    risk_score = scale_risk_score(raw_risk_score)
    risk_result["risk_score"] = risk_score
    
    # Overwrite the decision logic based on the shiny new 0-100 scale!
    if risk_score > 70:
        decision = "BLOCKED"
    elif risk_score > 30:
        decision = "STEP_UP"
    else:
        decision = "APPROVED"
        
    risk_result["decision"] = decision

    logger.info(f"Raw Score: {raw_risk_score:.2f} -> Mapped Risk Score: {risk_score}/100 → {decision}")

    # ── STEP 4: Branch based on decision ──
    if decision == "BLOCKED":
        logger.warning(f"TRANSACTION BLOCKED | Score: {risk_score}")
        return {
            "decision"      : "BLOCKED",
            "risk_score"    : risk_score,
            "reason"        : "High risk detected",
            "threats"       : risk_result["components"]["threats"],
            "transaction_id": transaction_id,
            "amount"        : amount,
            "nonce"         : nonce,
            "sensor_window" : window,
            "components"    : risk_result["components"]
        }

    elif decision == "STEP_UP":
        logger.warning(f"STEP-UP REQUIRED | Score: {risk_score}")
        return {
            "decision"      : "STEP_UP",
            "risk_score"    : risk_score,
            "reason"        : "Additional verification required",
            "transaction_id": transaction_id,
            "amount"        : amount,
            "nonce"         : nonce,
            "sensor_window" : window,
            "components"    : risk_result["components"]
        }

    else:  # APPROVED
        # ── STEP 5: Request HMAC signing from Arduino ──
        token = request_signing(COM_PORT, nonce)
        if token is None:
            return {
                "decision"      : "BLOCKED",
                "reason"        : "Hardware signing failed",
                "risk_score"    : risk_score,
                "transaction_id": transaction_id
            }

        # ── STEP 6: Verify token with bank server ──
        verification = verify_with_server(nonce, token)
        final_status = verification.get("status", "REJECTED")

        logger.info(f"Bank verification: {final_status}")
        logger.info("=" * 50)

        return {
            "decision"      : final_status,
            "risk_score"    : risk_score,
            "token"         : token[:16] + "...",  
            "verification"  : verification,
            "transaction_id": transaction_id,
            "amount"        : amount,
            "nonce"         : nonce,
            "sensor_window" : window,
            "components"    : risk_result["components"]
        }


# ─────────────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n── MorphoLock Pipeline Test ──\n")
    print("Make sure Arduino is plugged into COM4")
    print("Hold the sensor naturally when prompted\n")

    input("Press ENTER when ready to start transaction test...")

    result = run_transaction("TXN001", 5000.0)

    print("\n── RESULT ──")
    print(f"Decision    : {result['decision']}")
    print(f"Risk Score  : {result.get('risk_score', 'N/A')}/100")
    print(f"Transaction : {result.get('transaction_id')}")
    print(f"Amount      : ₹{result.get('amount', 'N/A')}")
    if result.get('threats'):
        print(f"Threats     : {result['threats']}")
    print()