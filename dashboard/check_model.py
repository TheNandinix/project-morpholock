"""
Run this any time after (re)training the model, BEFORE testing with
real hardware. It takes one second and tells you immediately whether
the saved model file is healthy — no Arduino needed.

Run it like this, from the F:\\project-morpholock folder:

    python dashboard\\check_model.py
"""

import os
import sys
import glob
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "morpholock_model.pkl")
CSV_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "raw_recordings")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml_pipeline"))
from signal_processor import extract_features

print(f"Checking: {MODEL_PATH}")
model = joblib.load(MODEL_PATH)
n = model.n_features_in_

print(f"This model expects {n} features.")
if n == 12:
    print("Feature count CORRECT (4 x 3 axes).")
else:
    print(f"WRONG — your live pipeline sends 12 features, but this model expects {n}.")
    print("Do NOT test with hardware yet. Re-run 'python train_model.py' from inside")
    print("the ml_pipeline folder specifically, then run this check again.")
    sys.exit(1)

# ── Show where the model's OWN training data scores ──
# If live "holding" tests score much worse (more anomalous) than the
# model's own training examples, something is inconsistent between
# training-time and live-time feature extraction.
print("\nChecking a sample of your own training recordings...")
files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))[:20]
scores = []
for f in files:
    try:
        df = pd.read_csv(f, header=None)
        try:
            df = df.astype(float)
        except ValueError:
            df = df.iloc[1:].astype(float)
        feat = extract_features(df.values.tolist())
        if feat is not None:
            raw = model.score_samples([feat])[0]
            scores.append(raw)
    except Exception as e:
        print(f"  (skipped {f}: {e})")

if scores:
    print(f"\nSampled {len(scores)} of your own training recordings:")
    print(f"  Raw score range : {min(scores):.5f} to {max(scores):.5f}")
    print(f"  Raw score average: {np.mean(scores):.5f}")
    print("\nCompare this to the raw scores you got from live testing.")
    print("If live 'holding' scores are noticeably WORSE (more negative)")
    print("than this training range, something is inconsistent between")
    print("training-time and live-time feature extraction — tell me the")
    print("numbers and I'll dig further before you collect more data.")
else:
    print("Could not sample any training files — check the folder path.")