#!/usr/bin/env python3
"""
Verifier for h2o-polars-skew-debugger.

Runs the training pipeline, then runs serving on the same inputs,
and checks that:
1. Encoding artifacts are saved (encoders.pkl must exist)
2. Scaler is fitted only on training data (checked via artifact metadata)
3. Serve-time feature values match train-time for the same inputs
4. Predictions are consistent (no skew above threshold)
"""

import sys
import os
import json
import pickle
import subprocess
import numpy as np

ARTIFACTS_DIR = "/workspace/artifacts"
REWARD_FILE = "/logs/verifier/reward.txt"

def write_reward(score, reason):
    os.makedirs("/logs/verifier", exist_ok=True)
    with open(REWARD_FILE, "w") as f:
        f.write(str(score))
    print(f"[verifier] reward={score} | {reason}")

def fail(reason):
    write_reward(0.0, reason)
    sys.exit(0)

def main():
    # Run training
    print("[verifier] Running training pipeline...")
    env = {**os.environ, "PYTHONPATH": "/workspace"}
    result = subprocess.run(
        ["python3", "/workspace/pipeline/train.py"],
        capture_output=True, text=True, cwd="/workspace", env=env
    )
    if result.returncode != 0:
        fail(f"Training pipeline failed:\n{result.stderr[-500:]}")
    print(result.stdout[-300:])

    # CHECK 1: encoders.pkl must be saved
    encoders_path = f"{ARTIFACTS_DIR}/encoders.pkl"
    if not os.path.exists(encoders_path):
        fail(
            "CHECK 1 FAILED: encoders.pkl not found in artifacts. "
            "LabelEncoders must be saved during training so serving uses "
            "identical category-to-integer mappings."
        )

    # CHECK 2: scaler_fitted_on must indicate train-only fitting
    scaler_meta_path = f"{ARTIFACTS_DIR}/scaler_meta.json"
    if not os.path.exists(scaler_meta_path):
        fail(
            "CHECK 2 FAILED: scaler_meta.json not found. "
            "Save a metadata file indicating scaler was fitted on training data only. "
            "Example: json.dump({'fitted_on': 'train_only', 'n_samples': len(X_train)}, f)"
        )
    with open(scaler_meta_path) as f:
        meta = json.load(f)
    if meta.get("fitted_on") != "train_only":
        fail(
            "CHECK 2 FAILED: scaler_meta.json shows scaler was not fitted on train data only. "
            "Fit StandardScaler AFTER the train/test split, on X_train only."
        )

    # CHECK 3: Run serve on deterministic inputs and compare feature values
    print("[verifier] Checking feature consistency...")
    sys.path.insert(0, "/workspace")
    os.environ["PYTHONPATH"] = "/workspace"

    # Import serve module fresh
    import importlib
    import pipeline.serve as serve_module
    importlib.reload(serve_module)

    # Deterministic test inputs
    test_inputs = [
        {"age": 30.0, "income": 50000.0, "tenure_days": 200.0,
         "session_count": 12.0, "page_views": 40.0,
         "plan_type": "basic", "country": "US", "device_type": "desktop"},
        {"age": None, "income": 70000.0, "tenure_days": 500.0,
         "session_count": None, "page_views": 5.0,
         "plan_type": "free", "country": "CA", "device_type": "mobile"},
        {"age": 45.0, "income": None, "tenure_days": 90.0,
         "session_count": 25.0, "page_views": 100.0,
         "plan_type": "enterprise", "country": "UK", "device_type": "tablet"},
    ]

    try:
        preds_serve = serve_module.predict(test_inputs)
    except Exception as e:
        fail(f"Serving pipeline threw an exception: {e}")

    # CHECK 4: Run same inputs through training feature engineering and compare
    print("[verifier] Comparing train vs serve features...")
    import pandas as pd
    import pipeline.train as train_module
    importlib.reload(train_module)

    # Load artifacts
    with open(f"{ARTIFACTS_DIR}/model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(f"{ARTIFACTS_DIR}/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(f"{ARTIFACTS_DIR}/imputation_means.json") as f:
        imputation_means = json.load(f)
    with open(encoders_path, "rb") as f:
        encoders = pickle.load(f)

    from pipeline.features import NUMERIC_FEATURES, CATEGORICAL_FEATURES

    df_test = pd.DataFrame(test_inputs)
    # Apply training-style feature engineering manually using saved artifacts
    for col in NUMERIC_FEATURES:
        df_test[col] = df_test[col].fillna(imputation_means[col])
    for col in CATEGORICAL_FEATURES:
        df_test[col] = encoders[col].transform(df_test[col].astype(str))
    df_test[NUMERIC_FEATURES] = scaler.transform(df_test[NUMERIC_FEATURES])

    X_ref = df_test[NUMERIC_FEATURES + CATEGORICAL_FEATURES].values
    preds_train_style = model.predict_proba(X_ref)[:, 1].tolist()

    # Compare predictions — must be within 1% tolerance
    max_diff = max(abs(a - b) for a, b in zip(preds_serve, preds_train_style))
    if max_diff > 0.01:
        fail(
            f"CHECK 4 FAILED: Train/serve skew detected. "
            f"Max prediction difference: {max_diff:.4f} (threshold: 0.01). "
            f"Serve predictions: {[round(p,4) for p in preds_serve]}. "
            f"Expected: {[round(p,4) for p in preds_train_style]}. "
            f"Check categorical encoding and null imputation consistency."
        )

    write_reward(1.0, f"All checks passed. Max skew: {max_diff:.6f}")

if __name__ == "__main__":
    main()
