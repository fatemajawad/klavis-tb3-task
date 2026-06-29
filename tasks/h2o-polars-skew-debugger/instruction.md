# H2O + Polars Train/Serve Skew Debugger

## Background

You are a data scientist at a company running an AutoML pipeline. The pipeline trains
models using H2O with Pandas-based feature engineering, then serves predictions using
a Polars-based serving pipeline for performance.

The model trains with high accuracy (~92%) but production predictions are **significantly
worse** than expected. No errors are thrown. The serving pipeline runs fine. But
predictions on the same input data differ between training-time and serve-time feature
engineering.

The pipeline is at `/workspace/pipeline/`.

Key files:
- `pipeline/train.py` — training feature engineering + H2O model training
- `pipeline/serve.py` — serving feature engineering + prediction
- `pipeline/features.py` — shared feature config

## Your Task

Find and fix all bugs causing train/serve skew so the verifier passes.

```bash
cd /workspace
python3 pipeline/train.py    # trains the model, saves artifacts
python3 pipeline/serve.py    # loads model, runs predictions
python3 /tests/verify.py     # checks for skew
```

## What correct behavior looks like

- Null imputation must produce **identical values** in training and serving
- Categorical encoding must produce **identical mappings** in training and serving  
- Feature scaling must be fitted **only on training data** (no leakage from test set)
- Predictions on the same input must match within a small tolerance

## Hints (deliberately vague)

- How does Pandas handle nulls in `.fillna(df.mean())` vs Polars `.fill_null(pl.mean())`?
- When you fit a LabelEncoder during training, where do you save it for serving?
- When should a StandardScaler be fitted — before or after the train/test split?
