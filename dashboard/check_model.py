import os
import joblib
import numpy as np

MODEL_PATH = "ml_pipeline/models/morpholock_model.pkl"

if not os.path.exists(MODEL_PATH):
    print(f"❌ ERROR — Model file not found at {MODEL_PATH}")
    exit(1)

try:
    model = joblib.load(MODEL_PATH)
    
    # Check dimensions using a dummy 12-feature matrix sample
    dummy_input = np.zeros((1, 12))
    model.predict(dummy_input)
    
    print("✅ CORRECT — safe to test")
except Exception as e:
    print(f"❌ WRONG MODEL loaded: {e}")