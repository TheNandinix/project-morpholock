"""
attempt_tracker.py
-------------------
Tracks failed authentication attempts per session and implements
Progressive Cryptographic Ratcheting:

  Attempts 1-2 failed  -> Soft Drift (minor warning, retry allowed)
  Attempt 3+ failed    -> Hard Hardening (lockdown + secondary verification required)
  Successful APPROVED  -> Counter resets to zero

This directly satisfies the requirement: "harden the login process
after unsuccessful login attempts."

Author: Nandini (Team Lead)
"""

import time
import logging
import json
import os

logger = logging.getLogger(__name__)

# ── Configuration ──
SOFT_THRESHOLD   = 2     # Attempts 1-2 = soft warning
HARD_THRESHOLD   = 3     # Attempt 3+ = hard lockdown
LOCKDOWN_SECONDS = 120   # 2 minute cooldown after hard lockdown triggers

# ── Where attempt state is stored ──
# A simple JSON file acts as our session store for this prototype.
# In production this would be a Redis cache or database table
# keyed by user_id / device_id.
STATE_FILE = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'attempt_state.json'
)


def _load_state() -> dict:
    """Load the current attempt state from disk."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_state(state: dict):
    """Persist attempt state to disk."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_attempt_status(user_id: str = "default_user") -> dict:
    """
    Returns the current hardening status for this user BEFORE
    scoring the new transaction. Called at the start of every
    transaction to check if the user is currently locked out.
    """
    state = _load_state()
    user_state = state.get(user_id, {
        "failed_attempts": 0,
        "locked_until": 0,
        "last_attempt": 0
    })

    now = time.time()
    locked_until = user_state.get("locked_until", 0)

    if now < locked_until:
        remaining = int(locked_until - now)
        logger.warning(
            f"User '{user_id}' is in HARD LOCKDOWN. "
            f"{remaining}s remaining."
        )
        return {
            "is_locked": True,
            "remaining_seconds": remaining,
            "failed_attempts": user_state["failed_attempts"],
            "hardening_level": "HARD_LOCKDOWN"
        }

    failed = user_state["failed_attempts"]

    if failed >= HARD_THRESHOLD:
        level = "HARD_LOCKDOWN"
    elif failed >= SOFT_THRESHOLD:
        level = "SOFT_DRIFT"
    else:
        level = "NORMAL"

    return {
        "is_locked": False,
        "remaining_seconds": 0,
        "failed_attempts": failed,
        "hardening_level": level
    }


def record_attempt_result(user_id: str, was_approved: bool):
    """
    Called AFTER every transaction completes. Updates the
    failed-attempt counter based on the outcome.

    was_approved=True  -> resets counter to 0 (legitimate success)
    was_approved=False -> increments counter, may trigger lockdown
    """
    state = _load_state()
    user_state = state.get(user_id, {
        "failed_attempts": 0,
        "locked_until": 0,
        "last_attempt": 0
    })

    now = time.time()
    user_state["last_attempt"] = now

    if was_approved:
        if user_state["failed_attempts"] > 0:
            logger.info(
                f"User '{user_id}' succeeded — "
                f"resetting failed attempt counter to 0"
            )
        user_state["failed_attempts"] = 0
        user_state["locked_until"] = 0
    else:
        user_state["failed_attempts"] += 1
        failed = user_state["failed_attempts"]

        if failed == SOFT_THRESHOLD:
            logger.warning(
                f"User '{user_id}' — SOFT DRIFT triggered "
                f"({failed} failed attempts). Minor step-up issued."
            )
        elif failed >= HARD_THRESHOLD:
            user_state["locked_until"] = now + LOCKDOWN_SECONDS
            logger.critical(
                f"User '{user_id}' — HARD LOCKDOWN triggered "
                f"({failed} failed attempts). "
                f"Locked for {LOCKDOWN_SECONDS}s. "
                f"Secondary verification now mandatory."
            )

    state[user_id] = user_state
    _save_state(state)


def reset_attempts(user_id: str = "default_user"):
    """Manual reset — useful for demo purposes between test runs."""
    state = _load_state()
    if user_id in state:
        del state[user_id]
        _save_state(state)
    logger.info(f"Attempt counter manually reset for '{user_id}'")


if __name__ == "__main__":
    print("Testing attempt_tracker.py...\n")

    test_user = "demo_user"
    reset_attempts(test_user)

    # Simulate 4 failed attempts in a row
    for i in range(4):
        status = get_attempt_status(test_user)
        print(f"Before attempt {i+1}: "
              f"level={status['hardening_level']}, "
              f"locked={status['is_locked']}")

        if status["is_locked"]:
            print(f"  -> BLOCKED — {status['remaining_seconds']}s remaining\n")
            continue

        record_attempt_result(test_user, was_approved=False)
        print(f"  -> Recorded as FAILED\n")

    final = get_attempt_status(test_user)
    print(f"Final state: {final}")
    print("\nNow simulating a successful transaction...")
    record_attempt_result(test_user, was_approved=True)
    after_success = get_attempt_status(test_user)
    print(f"After success: {after_success}")
    print("\nTest complete.")