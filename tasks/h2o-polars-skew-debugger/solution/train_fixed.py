"""
Training pipeline - FIXED version.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
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
    for col in ["age", "income", "session_count"]:
        null_idx = np.random.choice(N, int(N * 0.1), replace=False)
        data[col] = data[col].astype(float)
        data[col][null_idx] = np.nan

    df = pd.DataFrame(data)
    df[TARGET] = ((df["session_count"].fillna(0) < 10) &
                  (df["tenure_days"] > 300)).astype(int)
    return df


def train():
    print("Loading training data...")
    df = generate_training_data()

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    # FIXED: split FIRST before any fitting
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # FIXED: compute imputation means on train only
    imputation_means = X_train[NUMERIC_FEATURES].mean().to_dict()
    with open(f"{ARTIFACTS_DIR}/imputation_means.json", "w") as f:
        json.dump(imputation_means, f)

    # FIXED: impute using train-only means
    X_train = X_train.copy()
    X_test = X_test.copy()
    for col in NUMERIC_FEATURES:
        X_train[col] = X_train[col].fillna(imputation_means[col])
        X_test[col] = X_test[col].fillna(imputation_means[col])

    # FIXED: fit and save LabelEncoders on training data
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        X_train[col] = le.fit_transform(X_train[col].astype(str))
        X_test[col] = le.transform(X_test[col].astype(str))
        encoders[col] = le
    with open(f"{ARTIFACTS_DIR}/encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)

    # FIXED: fit scaler on X_train only
    scaler = StandardScaler()
    X_train[NUMERIC_FEATURES] = scaler.fit_transform(X_train[NUMERIC_FEATURES])
    X_test[NUMERIC_FEATURES] = scaler.transform(X_test[NUMERIC_FEATURES])

    with open(f"{ARTIFACTS_DIR}/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    # FIXED: save metadata proving scaler fitted on train only
    with open(f"{ARTIFACTS_DIR}/scaler_meta.json", "w") as f:
        json.dump({"fitted_on": "train_only", "n_samples": len(X_train)}, f)

    print("Training model...")
    model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Train accuracy: {train_score:.4f}")
    print(f"Test accuracy:  {test_score:.4f}")

    with open(f"{ARTIFACTS_DIR}/model.pkl", "wb") as f:
        pickle.dump(model, f)

    print(f"Artifacts saved to {ARTIFACTS_DIR}")
    return train_score, test_score


if __name__ == "__main__":
    train()
