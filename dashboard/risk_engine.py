from attempt_tracker import get_attempt_status, record_attempt_result
import numpy as np
import joblib
import logging
import os

# Setting up logging - this prints helpful messages while code runs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# RISK SCORE WEIGHTS — must add up to 100
# ─────────────────────────────────────────
W_TREMOR  = 50   # Tremor anomaly carries most weight
W_CONTEXT = 40   # Screen sharing / scam detection
W_TILT    = 10   # Sudden device tilt

# ─────────────────────────────────────────
# LOAD THE ML MODEL
# (Katyayni will create this file — morpholock_model.pkl)
# ─────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), 
             '..', 'models', 'morpholock_model.pkl')

def load_model():
    """Load the trained Isolation Forest model."""
    try:
        model = joblib.load(MODEL_PATH)
        logger.info("ML model loaded successfully")
        return model
    except FileNotFoundError:
        logger.warning("Model file not found — using dummy score for now")
        return None

model = load_model()

# ─────────────────────────────────────────
# MAIN FUNCTION — computes the risk score
# ─────────────────────────────────────────
def compute_risk_score(sensor_window: list, context_result: dict,
                       user_id: str = "default_user") -> dict:
    # ── PROGRESSIVE CRYPTOGRAPHIC RATCHETING ──
    # Check if this user is currently in a hardening state
    # BEFORE scoring the new transaction.
    attempt_status = get_attempt_status(user_id)

    if attempt_status["is_locked"]:
        logger.critical(
            f"Transaction rejected — user in HARD LOCKDOWN, "
            f"{attempt_status['remaining_seconds']}s remaining"
        )
        return {
            "risk_score": 100,
            "decision": "BLOCKED",
            "components": {
                "tremor_risk": 0,
                "context_risk": 0,
                "tilt_risk": 0,
                "threats": []
            },
            "hardening": {
                "level": "HARD_LOCKDOWN",
                "failed_attempts": attempt_status["failed_attempts"],
                "remaining_seconds": attempt_status["remaining_seconds"],
                "message": "Account temporarily locked due to repeated "
                           "failed verification attempts. Secondary "
                           "verification required to unlock."
            }
        }
    """
    Takes live sensor data and context scan result.
    Returns a risk score between 0 and 100 with a decision.

    sensor_window : list of 200 rows, each row = [Ax, Ay, Az, Gx, Gy, Gz]
    context_result: dict from Khushi's context_scanner.py
                    e.g. {"risk_score": 40, "threats": ["AnyDesk"], "status": "THREAT_DETECTED"}
    """

    # ── Component 1: Tremor anomaly score (0 to 50) ──
    if model is None or sensor_window is None or len(sensor_window) < 200:
        # No model yet — flag as high risk
        tremor_risk = 50
        logger.warning("No model loaded or insufficient data — tremor risk set to max")
    else:
        try:
            import sys as _sys, os as _os
            _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'ml_pipeline'))
            from signal_processor import extract_features
            features = extract_features(sensor_window)
            if features is not None:
                # Isolation Forest score: more negative = more anomalous
                raw_score = model.score_samples([features])[0]
                # Convert to 0-50 risk scale
                tremor_risk = max(0, min(50, int((-raw_score) * 100)))
            else:
                tremor_risk = 50
        except ImportError:
            logger.warning("signal_processor.py not available yet — using dummy tremor score")
            tremor_risk = 50
        except Exception as e:
            logger.error(f"Tremor scoring failed: {e}")
            tremor_risk = 50

    # ── Component 2: Context risk from Khushi's scanner (0 to 40) ──
    context_risk = context_result.get("risk_score", 0)
    threats_found = context_result.get("threats", [])

    # ── Component 3: Device tilt risk (0 to 10) ──
    try:
        data = np.array(sensor_window[-20:])  # Last 200ms of data
        Az_vals = data[:, 2]                  # Z-axis acceleration
        tilt_variance = float(np.var(Az_vals))
        tilt_risk = min(10, int(tilt_variance * 50))
    except Exception as e:
        logger.error(f"Tilt scoring failed: {e}")
        tilt_risk = 0

    # ── Final weighted risk score (0 to 100) ──
    total_risk = int(
        (tremor_risk / 50) * W_TREMOR  +
        (context_risk / 40) * W_CONTEXT +
        (tilt_risk    / 10) * W_TILT
    )
    total_risk = max(0, min(100, total_risk))

    # CRITICAL OVERRIDE: any active threat detection is an automatic
    # hard block, regardless of tremor or tilt score. This is because
    # APP scams rely on the legitimate, willing user — biometric match
    # does NOT make the transaction safe if a scammer is watching live.
    if context_result.get("threats"):
        decision = "BLOCKED"
        total_risk = max(total_risk, 85)
        logger.critical(
            f"HARD BLOCK — active threat override: "
            f"{context_result['threats']}"
        )
    elif total_risk < 30:
        decision = "APPROVED"
    elif total_risk < 70:
        decision = "STEP_UP"
    else:
        decision = "BLOCKED"
    result = {
        "risk_score"  : total_risk,
        "decision"    : decision,
        "components"  : {
            "tremor_risk"  : tremor_risk,
            "context_risk" : context_risk,
            "tilt_risk"    : tilt_risk,
            "threats"      : threats_found
        }
    }

    logger.info(f"Risk Score: {total_risk}/100 → Decision: {decision}")
    if threats_found:
        logger.warning(f"Threats detected: {threats_found}")
    # ── Record this attempt's outcome for future hardening ──
    was_approved = (decision == "APPROVED")
    record_attempt_result(user_id, was_approved)

    # ── If user has accumulated soft-drift level failures,
    #    escalate even a borderline APPROVED to STEP_UP ──
    if (attempt_status["hardening_level"] == "SOFT_DRIFT"
            and decision == "APPROVED" and total_risk > 15):
        decision = "STEP_UP"
        logger.warning(
            "SOFT DRIFT active — escalating borderline approval "
            "to STEP_UP as a precaution"
        )

    result["hardening"] = {
        "level": attempt_status["hardening_level"],
        "failed_attempts": attempt_status["failed_attempts"],
        "remaining_seconds": 0,
        "message": None
    }

    return result


# ─────────────────────────────────────────
# TEST — run this file directly to check it works
# python risk_engine.py
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n── MorphoLock Risk Engine Test ──\n")

    # Simulate a LEGITIMATE transaction (human hand, no threats)
    fake_human_data = [[0.01, 0.98, 0.02, 1.1, -0.3, 0.1]] * 200
    fake_context_clear = {"risk_score": 0, "threats": [], "status": "CLEAR"}
    result = compute_risk_score(fake_human_data, fake_context_clear)
    print(f"Test 1 (Human, no threats): Score={result['risk_score']} → {result['decision']}")

    # Simulate a FRAUD scenario (AnyDesk running)
    fake_context_threat = {"risk_score": 40, "threats": ["AnyDesk"], "status": "THREAT_DETECTED"}
    result2 = compute_risk_score(fake_human_data, fake_context_threat)
    print(f"Test 2 (AnyDesk running):   Score={result2['risk_score']} → {result2['decision']}")

    print("\n── Test complete ──\n")