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
# MOCK VERIFICATION
# Temporary stand-in for Khushi's verification server
# Used when her server is not running yet
# When her server is ready — this function is never called
# ─────────────────────────────────────────────────────
def mock_verify(nonce: str, token: str, timestamp: int) -> dict:
    """
    Simulates what Khushi's verification server will do.
    Accepts any token for now — just for testing.
    DELETE this function once verification_server.py is running.
    """
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
    """
    Opens serial connection to Arduino.
    Reads exactly 200 lines of sensor data.
    Each line = Ax,Ay,Az,Gx,Gy,Gz (6 float values)
    Returns a list of 200 rows.
    """
    logger.info(f"Connecting to Arduino on {port}...")
    window = []

    try:
        # Open the serial port
        # timeout=3 means: if no data arrives for 3 seconds, stop waiting
        ser = serial.Serial(port, BAUD_RATE, timeout=3)

        # Wait 2 seconds — Arduino resets when serial opens
        # If we don't wait, we read garbage data during the reset
        time.sleep(2)
        ser.flushInput()  # Clear any leftover data from before
        logger.info("Arduino connected. Collecting sensor data...")

        # Keep reading lines until we have 200 clean ones
        while len(window) < SAMPLES_NEEDED:
            try:
                # Read one line from Arduino
                raw = ser.readline().decode('utf-8').strip()

                # Skip status messages like "READY" or "STATUS:..."
                if not raw or raw.startswith("READY") or raw.startswith("STATUS"):
                    continue

                # Split "0.012,0.987,0.003,1.23,-0.45,0.01" into 6 values
                parts = raw.split(",")
                if len(parts) == 6:
                    row = [float(x) for x in parts]
                    window.append(row)

            except (ValueError, UnicodeDecodeError):
                # Bad line — just skip it, don't crash
                logger.debug("Skipped corrupted data line")
                continue

        ser.close()
        logger.info(f"Collected {len(window)} sensor readings successfully")
        return window, ser  # Return data and keep ser reference for signing

    except serial.SerialException as e:
        logger.error(f"Could not connect to Arduino on {port}: {e}")
        logger.error("Check: Is Arduino plugged in? Is COM4 correct? Is Serial Monitor closed?")
        return None, None


# ─────────────────────────────────────────────────────
# STEP 2 — GET HMAC TOKEN FROM ARDUINO
# ─────────────────────────────────────────────────────
def request_signing(port: str, nonce: str) -> str:
    """
    Sends SIGN:nonce command to Arduino.
    Arduino computes HMAC-SHA256 and replies TOKEN:hexstring.
    Returns the hex token string.
    """
    logger.info(f"Requesting HMAC signing for nonce: {nonce}")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
        time.sleep(1)

        # Send the sign command
        # encode() converts string to bytes — serial can only send bytes
        command = f"SIGN:{nonce}\n"
        ser.write(command.encode())
        logger.info(f"Sent command: {command.strip()}")

        # Wait for Arduino's reply
        reply = ser.readline().decode('utf-8').strip()
        ser.close()

        if reply.startswith("TOKEN:"):
            token = reply[6:]  # Remove "TOKEN:" prefix, keep the hex
            logger.info(f"Token received: {token[:16]}...") # Log first 16 chars only
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
    """
    Sends token to Khushi's verification server.
    Falls back to mock if server is not running.
    """
    timestamp_ms = int(time.time() * 1000)

    try:
        # Try real server first
        response = requests.post(
            VERIFY_URL,
            json={
                "nonce": nonce,
                "token": token,
                "timestamp": timestamp_ms
            },
            timeout=2  # Don't wait more than 2 seconds
        )
        return response.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        # Server not running or too slow to respond — use mock instead
        logger.warning("Verification server not reachable — using mock")
        return mock_verify(nonce, token, timestamp_ms)


# ─────────────────────────────────────────────────────
# MASTER FUNCTION — run_transaction
# This is the function the dashboard will call
# ─────────────────────────────────────────────────────
def run_transaction(transaction_id: str, amount: float) -> dict:
    """
    Full MorphoLock transaction pipeline.

    transaction_id : unique ID e.g. "TXN001"
    amount         : transaction amount e.g. 5000.0

    Returns complete result dict with decision and all details.
    """
    logger.info("=" * 50)
    logger.info(f"NEW TRANSACTION: {transaction_id} | Amount: ₹{amount}")
    logger.info("=" * 50)

    # Build the nonce — this is the challenge the bank sends
    # Format: TransactionID_Amount_Timestamp
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

    # ── STEP 2: Get context scan from Khushi's scanner ──
    try:
        from cybersecurity.context_scanner import scan_environment
        context_result = scan_environment()
    except ImportError:
        # Khushi's file not available yet — use empty context
        logger.warning("context_scanner.py not found — using empty context")
        context_result = {"risk_score": 0, "threats": [], "status": "UNKNOWN"}

    # ── STEP 3: Compute risk score ──
    risk_result = compute_risk_score(window, context_result)
    risk_score = risk_result["risk_score"]
    decision   = risk_result["decision"]

    logger.info(f"Risk Score: {risk_score}/100 → {decision}")

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
            "token"         : token[:16] + "...",  # Partial token for display
            "verification"  : verification,
            "transaction_id": transaction_id,
            "amount"        : amount,
            "nonce"         : nonce,
            "sensor_window" : window,
            "components"    : risk_result["components"]
        }


# ─────────────────────────────────────────────────────
# TEST — run this file directly to test the pipeline
# python dashboard/main_pipeline.py
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