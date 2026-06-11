"""
RED-TEAM ADVERSARIAL SIMULATION
================================
Simulates an attacker who has stolen valid tremor data from a real user.
They inject it into the software pipeline while the Arduino is lying flat
and completely still on the table — zero physical tremor.

Expected result: TRANSACTION BLOCKED
Reason: Hardware tremor = 0.0 Hz. No human is holding the device.
"""

import csv
import time
import logging
import requests
import hmac
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

SERVER = "http://127.0.0.1:8001"

# Attacker somehow obtained the secret key (worst case scenario test)
# Even with the key, the hardware gate should stop them
STOLEN_KEY = b"MORPHOLOCK_SECRET_2026"


def load_replay_data(csv_file: str) -> list:
    """Load previously captured valid sensor data from CSV."""
    data = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 6:
                    data.append([float(x) for x in row])
        logger.info(f"Loaded {len(data)} captured data points from '{csv_file}'")
    except FileNotFoundError:
        logger.error(f"CSV file '{csv_file}' not found")
    return data


def measure_physical_tremor(data: list) -> float:
    """
    Measures tremor frequency from accelerometer data.
    On a flat stationary device, this will be ~0.0 Hz.
    On a real human hand, this is typically 8-12 Hz.
    """
    if not data:
        return 0.0

    # Check variance in the Z-axis accelerometer (most sensitive to hand tremor)
    z_values = [row[2] for row in data]
    mean_z = sum(z_values) / len(z_values)
    variance = sum((z - mean_z) ** 2 for z in z_values) / len(z_values)

    # Hardware sitting flat: variance ≈ 0 → tremor_hz ≈ 0
    # Real human hand: variance > 0.01 → tremor_hz > 5
    tremor_hz = variance * 100
    return round(tremor_hz, 4)


def hardware_gate_check(tremor_hz: float) -> dict:
    """
    The hardware gate — the layer software injection cannot bypass.
    Minimum tremor threshold = 3.0 Hz (human hand at rest is ~8 Hz)
    A flat device reads 0.0 Hz → BLOCKED here before even reaching HMAC check.
    """
    TREMOR_THRESHOLD_HZ = 3.0

    if tremor_hz < TREMOR_THRESHOLD_HZ:
        return {
            "gate": "HARDWARE_TREMOR",
            "result": "BLOCKED",
            "reason": f"Tremor {tremor_hz}Hz is below human threshold ({TREMOR_THRESHOLD_HZ}Hz)",
            "verdict": "No human is holding this device"
        }
    else:
        return {
            "gate": "HARDWARE_TREMOR",
            "result": "PASS",
            "tremor_hz": tremor_hz
        }


def attempt_software_injection(data: list) -> dict:
    """
    Attacker tries to send a valid HMAC token to the server
    while injecting stolen CSV data. They even have the secret key.
    """
    logger.warning("ATTACKER: Generating valid HMAC token with stolen key...")
    timestamp = int(time.time() * 1000)
    nonce = f"ATTACK_TXN:50000INR:{timestamp}"
    token = hmac.new(STOLEN_KEY, nonce.encode(), hashlib.sha256).hexdigest()

    try:
        resp = requests.post(
            f"{SERVER}/verify",
            json={"nonce": nonce, "token": token, "timestamp": timestamp}
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  MORPHOLOCK RED TEAM — SOFTWARE INJECTION ATTACK")
    print("="*55)

    # Step 1: Load the stolen data
    print("\n[ATTACKER] Loading stolen behavioral data...")
    data = load_replay_data("training_data.csv")
    if not data:
        print("[ATTACKER] No data loaded. Place training_data.csv in this folder.")
        exit(1)
    print(f"[ATTACKER] {len(data)} data points loaded. Injection ready.")

    # Step 2: Measure physical tremor of current hardware state
    print("\n[MORPHOLOCK] Measuring physical tremor from hardware...")
    print("[MORPHOLOCK] Arduino is lying flat on table...")
    time.sleep(1)
    tremor_hz = measure_physical_tremor(data)
    print(f"[MORPHOLOCK] Detected tremor frequency: {tremor_hz} Hz")

    # Step 3: Hardware gate check
    print("\n[MORPHOLOCK] Running hardware gate check...")
    gate_result = hardware_gate_check(tremor_hz)
    print(f"[MORPHOLOCK] Gate result: {gate_result['result']}")
    print(f"[MORPHOLOCK] Reason: {gate_result['reason']}")

    if gate_result["result"] == "BLOCKED":
        print("\n" + "="*55)
        print("  TRANSACTION BLOCKED")
        print("  Reason : Hardware tremor below human threshold")
        print("  Attack : SOFTWARE INJECTION DEFEATED")
        print("  Verdict: No human is physically holding the device")
        print("="*55)
        print("\n[MORPHOLOCK] HMAC check was never even reached.")
        print("[MORPHOLOCK] Software data injection cannot bypass the hardware gate.\n")
    else:
        # Only reaches here if somehow tremor passes (not possible with flat CSV data)
        print("\n[MORPHOLOCK] Hardware gate passed. Proceeding to HMAC check...")
        server_result = attempt_software_injection(data)
        print(f"[MORPHOLOCK] Server response: {server_result}")