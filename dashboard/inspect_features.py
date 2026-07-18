r"""
Shows the RAW 12 features extracted from one real sensor capture —
not the final blended score. Run this once flat, once while holding,
and compare the numbers directly. This tells us exactly which
features (if any) actually separate a real hand from nothing.

Run it like this, from the F:\project-morpholock folder:

    python dashboard\inspect_features.py

Hold the sensor (or leave it flat) when it says "Collecting..."
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml_pipeline"))
from signal_processor import extract_features

sys.path.insert(0, os.path.dirname(__file__))
from main_pipeline import collect_sensor_data

LABELS = []
for axis in ["Ax", "Ay", "Az"]:
    for feat in ["tremor_power", "peak_freq", "total_power", "low_power"]:
        LABELS.append(f"{axis}_{feat}")

print("Collecting 200 real sensor readings now...")
window, _ = collect_sensor_data()

if window is None:
    print("Could not collect data — check Arduino connection / COM port.")
else:
    features = extract_features(window)
    print("\n--- RAW FEATURE VALUES ---")
    for label, value in zip(LABELS, features):
        print(f"{label:20s} = {value:.6f}")
    print("\nCopy this whole block and send it, once for FLAT and once for HOLDING.")