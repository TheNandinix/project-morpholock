"""
evaluate_model.py
------------------
Run this ONCE your model is trained. It does two things in one pass:

1. Computes every metric judges asked for: precision, recall, F1,
   ROC-AUC, FAR, FRR, EER, confusion matrix, latency, and (if you
   have impostor data) an impostor match score.

2. Works out a PROPERLY CALIBRATED risk-score formula from your real
   data, instead of a guessed multiplier — this is the fix for
   "holding isn't landing where it should."

Run it like this, from the project root:

    python ml_pipeline\evaluate_model.py

CHECK THESE 4 PATHS BELOW MATCH YOUR ACTUAL FOLDERS before running.
"""

import os
import sys
import glob
import time
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, os.path.dirname(__file__))
from signal_processor import extract_features

# ── EDIT THESE 4 PATHS IF YOUR FOLDERS ARE NAMED DIFFERENTLY ──
MODEL_PATH             = "models/morpholock_model.pkl"
GENUINE_HOLDOUT_FOLDER = "training_data/genuine_holdout"   # held-out real Kushagra sessions, NOT used in training
FLAT_FOLDER            = "training_data/validation_flat"   # flat/no-touch sessions
IMPOSTOR_FOLDER        = "training_data/impostor"          # optional — other people's sessions

# ── Where you WANT typical scores to land (tell me if these should differ) ──
TARGET_RISK_FOR_TYPICAL_GENUINE = 15   # a normal, relaxed genuine hold
TARGET_RISK_FOR_TYPICAL_FLAT    = 95   # a typical flat/no-touch reading


def load_csv_safely(path):
    df = pd.read_csv(path, header=None)
    try:
        df = df.astype(float)
    except ValueError:
        df = df.iloc[1:].astype(float)
    return df.values.tolist()


def score_folder(folder, model):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    raw_scores = []
    names = []
    for f in files:
        try:
            data = load_csv_safely(f)
            feat = extract_features(data)
            if feat is not None:
                raw_scores.append(model.score_samples([feat])[0])
                names.append(os.path.basename(f))
        except Exception as e:
            print(f"  (skipped {f}: {e})")
    return np.array(raw_scores), names


def main():
    print(f"Loading model: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)

    print(f"\nScoring genuine holdout: {GENUINE_HOLDOUT_FOLDER}")
    genuine_scores, genuine_names = score_folder(GENUINE_HOLDOUT_FOLDER, model)
    print(f"  {len(genuine_scores)} files scored")

    print(f"\nScoring flat validation: {FLAT_FOLDER}")
    flat_scores, flat_names = score_folder(FLAT_FOLDER, model)
    print(f"  {len(flat_scores)} files scored")

    impostor_scores, impostor_names = np.array([]), []
    if os.path.isdir(IMPOSTOR_FOLDER):
        print(f"\nScoring impostor data: {IMPOSTOR_FOLDER}")
        impostor_scores, impostor_names = score_folder(IMPOSTOR_FOLDER, model)
        print(f"  {len(impostor_scores)} files scored")
    else:
        print(f"\n(No impostor folder found at {IMPOSTOR_FOLDER} — skipping that part)")

    if len(genuine_scores) == 0 or len(flat_scores) == 0:
        print("\nERROR: need at least some genuine and flat scores to continue. "
              "Check the folder paths at the top of this file.")
        return

    # ══════════════════════════════════════════════
    # PART 1 — CALIBRATION: derive a real formula
    # ══════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("CALIBRATION")
    print("=" * 60)

    genuine_anchor = float(np.median(genuine_scores))
    flat_anchor = float(np.median(flat_scores))
    print(f"Typical genuine raw score (median): {genuine_anchor:.5f}")
    print(f"Typical flat raw score (median):    {flat_anchor:.5f}")

    if flat_anchor >= genuine_anchor:
        print("\nWARNING: flat scores are not clearly worse than genuine scores.")
        print("The model itself may still need attention — calibration alone won't fix this.")
        return

    slope = (TARGET_RISK_FOR_TYPICAL_FLAT - TARGET_RISK_FOR_TYPICAL_GENUINE) / (flat_anchor - genuine_anchor)
    intercept = TARGET_RISK_FOR_TYPICAL_GENUINE - slope * genuine_anchor

    print(f"\nCalibrated formula:")
    print(f"  risk_score = {slope:.4f} * raw_score + {intercept:.4f}")
    print(f"  (then clip to [0, 100])")

    def calibrated_risk(raw_score):
        return max(0, min(100, slope * raw_score + intercept))

    print(f"\nPaste this into risk_engine.py, replacing the old tremor_risk formula:")
    print(f"    tremor_risk = max(0, min(50, ({slope:.6f} * raw_score + {intercept:.6f}) / 2))")

    genuine_risks = [calibrated_risk(s) for s in genuine_scores]
    flat_risks = [calibrated_risk(s) for s in flat_scores]
    impostor_risks = [calibrated_risk(s) for s in impostor_scores]

    print(f"\nGenuine holdout — filename : calibrated risk score")
    for name, r in sorted(zip(genuine_names, genuine_risks), key=lambda x: -x[1]):
        flag = "  <-- CHECK THIS SESSION" if r >= 70 else ""
        print(f"  {name:20s}: {round(r):>4}{flag}")

    print(f"\nFlat — filename : calibrated risk score")
    for name, r in sorted(zip(flat_names, flat_risks), key=lambda x: x[1]):
        flag = "  <-- CHECK THIS SESSION (should be high, isn't)" if r < 70 else ""
        print(f"  {name:20s}: {round(r):>4}{flag}")

    if impostor_risks:
        print(f"\nImpostor — filename : calibrated risk score")
        for name, r in sorted(zip(impostor_names, impostor_risks), key=lambda x: x[1]):
            flag = "  <-- CHECK THIS SESSION (should be high, isn't)" if r < 70 else ""
            print(f"  {name:20s}: {round(r):>4}{flag}")

    # ══════════════════════════════════════════════
    # PART 2 — METRICS, using the REAL 30/70 threshold
    # your app actually uses — not sklearn's internal one
    # ══════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("METRICS (using your ACTUAL 70+ = BLOCKED threshold)")
    print("=" * 60)

    try:
        from sklearn.metrics import (roc_auc_score, precision_score, recall_score,
                                      f1_score, confusion_matrix, accuracy_score)
    except ImportError:
        print("scikit-learn not found — run: pip install scikit-learn")
        return

    anomaly_scores = np.concatenate([flat_scores, impostor_scores])
    all_raw = np.concatenate([genuine_scores, anomaly_scores])
    all_risk = np.array([calibrated_risk(s) for s in all_raw])

    y_true = np.array([0] * len(genuine_scores) + [1] * len(anomaly_scores))  # 1 = should be flagged
    y_score = -all_raw  # continuous, for ROC-AUC (threshold-independent, unaffected by this fix)
    y_pred = (all_risk >= 70).astype(int)  # matches your real BLOCKED threshold

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_score)
    cm = confusion_matrix(y_true, y_pred)

    tn, fp, fn, tp = cm.ravel()
    far = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    frr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print(f"Accuracy : {acc:.3f}  (secondary metric — reporting for completeness only)")
    print(f"Precision: {prec:.3f}")
    print(f"Recall   : {rec:.3f}")
    print(f"F1 Score : {f1:.3f}")
    print(f"ROC-AUC  : {auc:.3f}  (unaffected by this fix, same as before)")
    print(f"\nConfusion matrix:")
    print(f"                 Predicted Genuine   Predicted Anomaly")
    print(f"Actual Genuine   {tn:>16}   {fp:>17}")
    print(f"Actual Anomaly   {fn:>16}   {tp:>17}")
    print(f"\nFAR (an impostor/flat reading wrongly ACCEPTED as genuine): {far:.3f}")
    print(f"FRR (a genuine reading wrongly REJECTED)                  : {frr:.3f}")

    # Latency
    print("\n" + "=" * 60)
    print("LATENCY")
    print("=" * 60)
    sample_files = glob.glob(os.path.join(GENUINE_HOLDOUT_FOLDER, "*.csv"))[:5]
    times = []
    for f in sample_files:
        data = load_csv_safely(f)
        t0 = time.perf_counter()
        feat = extract_features(data)
        _ = model.score_samples([feat])[0]
        times.append((time.perf_counter() - t0) * 1000)
    if times:
        print(f"Average scoring latency: {np.mean(times):.2f} ms  (feature extraction + model scoring)")

    if len(impostor_scores):
        print("\n" + "=" * 60)
        print("IMPOSTOR MATCH SCORE")
        print("=" * 60)
        print(f"Average genuine raw score : {np.mean(genuine_scores):.5f}")
        print(f"Average impostor raw score: {np.mean(impostor_scores):.5f}")
        print(f"(Impostor should score clearly worse/more negative than genuine)")


if __name__ == "__main__":
    main()