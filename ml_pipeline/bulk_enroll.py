r"""
Bulk enrollment helper — collects MANY sessions in one run, instead
of re-running enroll_data.py by hand over and over.

Only use this if the original enrollment recordings are confirmed
lost. This creates brand new session_XXX.csv files in
data\raw_recordings, picking up numbering after whatever's already
there (so it won't overwrite anything by accident).

Run it like this, from the F:\project-morpholock folder
(adjust the number below if you want more or fewer sessions):

    python ml_pipeline\bulk_enroll.py

Tips while running:
- Hold the sensor naturally, the way you actually would for a real
  transaction — don't hold unnaturally still, genuine tremor is the
  whole point.
- Small natural variety between sessions (slightly different grip,
  posture, hand) makes the model more robust, not less accurate.
- You can stop early any time with Ctrl+C — whatever sessions were
  already saved stay saved.
"""

r"""
Bulk recording helper — collects MANY sessions in one run, instead
of re-running enroll_data.py by hand over and over. Handles BOTH
genuine hold sessions and flat/no-touch sessions — it asks which
one you're doing when you start it, so this one file covers both.

Run it like this, from the F:\project-morpholock folder:

    python ml_pipeline\bulk_enroll.py

You can stop early any time with Ctrl+C — whatever sessions were
already saved stay saved.
"""

import os
import sys
import glob
import time
import serial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))
from main_pipeline import COM_PORT, BAUD_RATE

sys.path.insert(0, os.path.dirname(__file__))
from enroll_data import collect_one_session

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def next_session_id(out_folder):
    os.makedirs(out_folder, exist_ok=True)
    existing = glob.glob(os.path.join(out_folder, "session_*.csv"))
    if not existing:
        return 1
    nums = [int(os.path.basename(f).split("_")[1].split(".")[0]) for f in existing]
    return max(nums) + 1


def main():
    print("What are you recording right now?")
    print("  1 = Genuine hold (Kushagra's real hand, for TRAINING)")
    print("  2 = Flat / no-touch (device untouched, for VALIDATION only)")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        out_folder = os.path.join(PROJECT_ROOT, "data", "raw_recordings")
        default_count = 50
        prompt_text = "Hold the sensor naturally"
    elif choice == "2":
        out_folder = os.path.join(PROJECT_ROOT, "data", "validation_flat")
        default_count = 30
        prompt_text = "Leave the device FLAT and UNTOUCHED (wait a few seconds after placing it down)"
    else:
        print("Invalid choice, exiting.")
        return

    count_input = input(f"How many sessions? (press Enter for default {default_count}): ").strip()
    target_sessions = int(count_input) if count_input else default_count

    print(f"\nConnecting to Arduino on {COM_PORT}...")
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=3)
    time.sleep(2)
    print("Connected.\n")

    start_id = next_session_id(out_folder)
    print(f"Saving to: {out_folder}")
    print(f"Starting from session_{start_id:03d}. Target: {target_sessions} sessions.\n")

    for i in range(target_sessions):
        session_id = start_id + i
        input(f"[{i+1}/{target_sessions}] {prompt_text}, "
              f"then press Enter to start recording session_{session_id:03d}...")
        path = collect_one_session(ser, session_id, out_folder)
        print(f"  Saved: {path}\n")

    ser.close()
    print("Done.")


if __name__ == "__main__":
    main()