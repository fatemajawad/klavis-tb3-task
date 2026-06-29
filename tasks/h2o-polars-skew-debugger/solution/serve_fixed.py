"""
Serving pipeline - FIXED version. Loads all artifacts from training.
"""

import os
import json
import pickle
import polars as pl

from pipeline.features import NUMERIC_FEATURES, CATEGORICAL_FEATURES

ARTIFACTS_DIR = "/workspace/artifacts"


def load_artifacts():
    with open(f"{ARTIFACTS_DIR}/model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(f"{ARTIFACTS_DIR}/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(f"{ARTIFACTS_DIR}/imputation_means.json") as f:
        imputation_means = json.load(f)
    # FIXED: load saved encoders
    with open(f"{ARTIFACTS_DIR}/encoders.pkl", "rb") as f:
        encoders = pickle.load(f)
    return model, scaler, imputation_means, encoders


def engineer_features_polars(df: pl.DataFrame, imputation_means: dict, scaler, encoders: dict) -> pl.DataFrame:
    # Null imputation using saved train means
    for col in NUMERIC_FEATURES:
        df = df.with_columns(pl.col(col).fill_null(imputation_means[col]))

    # FIXED: use saved encoders from training
    for col in CATEGORICAL_FEATURES:
        le = encoders[col]
        serve_values = df[col].cast(pl.Utf8).to_list()
        encoded = le.transform(serve_values)
        df = df.with_columns(pl.Series(col, encoded))

    # Apply scaler
    numeric_array = df.select(NUMERIC_FEATURES).to_numpy()
    scaled = scaler.transform(numeric_array)
    for i, col in enumerate(NUMERIC_FEATURES):
        df = df.with_columns(pl.Series(col, scaled[:, i]))

    return df


def predict(input_data: list[dict]) -> list[float]:
    model, scaler, imputation_means, encoders = load_artifacts()
    df = pl.DataFrame(input_data)
    df_features = engineer_features_polars(df, imputation_means, scaler, encoders)
    X = df_features.select(NUMERIC_FEATURES + CATEGORICAL_FEATURES).to_numpy()
    predictions = model.predict_proba(X)[:, 1]
    return predictions.tolist()


if __name__ == "__main__":
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
