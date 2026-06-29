"""
Training pipeline: feature engineering + H2O AutoML training.

Bugs introduced (no comments in production code):
1. StandardScaler fitted on full dataset before split (data leakage)
2. LabelEncoder fitted but not saved — serving will refit with different category order
3. Null imputation uses pandas mean computed on full dataset including test rows
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

# Use sklearn GBM instead of H2O for portability in this task
from sklearn.ensemble import GradientBoostingClassifier

from pipeline.features import (
    NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET,
    PLAN_TYPES, COUNTRIES, DEVICE_TYPES
)

ARTIFACTS_DIR = "/workspace/artifacts"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

np.random.seed(42)
N = 2000

def generate_training_data():
    data = {
        "age": np.random.normal(35, 10, N),
        "income": np.random.normal(60000, 20000, N),
        "tenure_days": np.random.exponential(365, N),
        "session_count": np.random.poisson(15, N),
        "page_views": np.random.poisson(50, N),
        "plan_type": np.random.choice(PLAN_TYPES, N),
        "country": np.random.choice(COUNTRIES, N),
        "device_type": np.random.choice(DEVICE_TYPES, N),
    }
    # Introduce ~10% nulls in numeric features
    for col in ["age", "income", "session_count"]:
        null_idx = np.random.choice(N, int(N * 0.1), replace=False)
        data[col] = data[col].astype(float)
        data[col][null_idx] = np.nan

    df = pd.DataFrame(data)
    # Target: churn based on low session_count and high tenure
    df[TARGET] = ((df["session_count"].fillna(0) < 10) & 
                  (df["tenure_days"] > 300)).astype(int)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # BUG 1: Fit scaler on full df BEFORE split — leaks test distribution into scaler
    # This means serve-time scaling uses different statistics than what was actually
    # used for the training rows. Fix: split first, fit scaler on train only.
    scaler = StandardScaler()
    df[NUMERIC_FEATURES] = scaler.fit_transform(
        df[NUMERIC_FEATURES].fillna(df[NUMERIC_FEATURES].mean())
    )
    # Save scaler (but computed on wrong data)
    with open(f"{ARTIFACTS_DIR}/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    # BUG 2: LabelEncoders fitted here but NOT saved to disk
    # serve.py will refit LabelEncoders independently — if category order differs
    # (e.g. due to Polars sort vs pandas sort), encodings won't match
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    # BUG: encoders dict is never saved
    # Fix: save with pickle so serve.py loads the same mappings

    return df


def train():
    print("Loading training data...")
    df = generate_training_data()

    print("Engineering features...")
    df_features = engineer_features(df)

    # BUG 3: Null imputation statistics computed on full dataset inside engineer_features
    # But split happens AFTER — so imputation already used test set statistics
    # (This is the second part of Bug 1 — split must happen first)
    X = df_features[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df_features[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training model...")
    model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Train accuracy: {train_score:.4f}")
    print(f"Test accuracy:  {test_score:.4f}")

    # Save model
    with open(f"{ARTIFACTS_DIR}/model.pkl", "wb") as f:
        pickle.dump(model, f)

    # Save imputation means (computed on full dataset — bug)
    imputation_means = df[NUMERIC_FEATURES].mean().to_dict()
    with open(f"{ARTIFACTS_DIR}/imputation_means.json", "w") as f:
        json.dump(imputation_means, f)

    print(f"Artifacts saved to {ARTIFACTS_DIR}")
    return train_score, test_score


if __name__ == "__main__":
    train()
