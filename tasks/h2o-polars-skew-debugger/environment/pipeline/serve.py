"""
Serving pipeline: Polars-based feature engineering + prediction.

Uses Polars for performance in production.
"""

import os
import json
import pickle
import numpy as np
import polars as pl
from sklearn.preprocessing import LabelEncoder

from pipeline.features import (
    NUMERIC_FEATURES, CATEGORICAL_FEATURES,
    PLAN_TYPES, COUNTRIES, DEVICE_TYPES
)

ARTIFACTS_DIR = "/workspace/artifacts"


def load_artifacts():
    with open(f"{ARTIFACTS_DIR}/model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(f"{ARTIFACTS_DIR}/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(f"{ARTIFACTS_DIR}/imputation_means.json") as f:
        imputation_means = json.load(f)
    return model, scaler, imputation_means


def engineer_features_polars(df: pl.DataFrame, imputation_means: dict, scaler) -> pl.DataFrame:
    """
    Serving-time feature engineering using Polars.
    Should produce identical features to training pipeline.
    """
    # Null imputation - uses saved means (correct approach)
    for col in NUMERIC_FEATURES:
        mean_val = imputation_means.get(col, 0.0)
        df = df.with_columns(
            pl.col(col).fill_null(mean_val)
        )

    # BUG: LabelEncoders not loaded from training artifacts
    # Instead, new LabelEncoders are fitted here on serve data
    # Polars sorts categoricals differently than pandas in some cases,
    # and serve batches may have different category distributions
    # causing label indices to differ from training
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        serve_values = df[col].cast(pl.Utf8).to_list()
        le.fit(serve_values)  # BUG: should load from artifacts/encoders.pkl
        encoded = le.transform(serve_values)
        df = df.with_columns(pl.Series(col, encoded))
        encoders[col] = le

    # Apply scaler (loaded from artifacts)
    numeric_array = df.select(NUMERIC_FEATURES).to_numpy()
    scaled = scaler.transform(numeric_array)
    for i, col in enumerate(NUMERIC_FEATURES):
        df = df.with_columns(pl.Series(col, scaled[:, i]))

    return df


def predict(input_data: list[dict]) -> list[float]:
    """Generate predictions for a batch of input records."""
    model, scaler, imputation_means = load_artifacts()

    df = pl.DataFrame(input_data)
    df_features = engineer_features_polars(df, imputation_means, scaler)

    X = df_features.select(NUMERIC_FEATURES + CATEGORICAL_FEATURES).to_numpy()
    predictions = model.predict_proba(X)[:, 1]
    return predictions.tolist()


if __name__ == "__main__":
    # Test with sample data
    sample = [
        {"age": 28.0, "income": 55000.0, "tenure_days": 120.0,
         "session_count": 20.0, "page_views": 60.0,
         "plan_type": "pro", "country": "US", "device_type": "desktop"},
        {"age": None, "income": 45000.0, "tenure_days": 400.0,
         "session_count": None, "page_views": 10.0,
         "plan_type": "free", "country": "UK", "device_type": "mobile"},
    ]
    preds = predict(sample)
    print(f"Predictions: {preds}")
