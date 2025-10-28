import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib
from typing import Tuple


def train_logistic(X: pd.DataFrame, y: pd.Series, out_path: str = "models/logistic.pkl") -> LogisticRegression:
    """Train a logistic regression model and persist it to out_path."""
    model = LogisticRegression(max_iter=200)
    model.fit(X, y)
    joblib.dump(model, out_path)
    return model


def load_model(path: str = "models/logistic.pkl") -> LogisticRegression:
    return joblib.load(path)


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """A tiny helper that creates simple features and a binary target if present.

    This is a convenience for local training/evaluation. It expects `df` to
    contain `loan_amount`, `income` and optionally `defaulted`.
    """
    df = df.copy()
    if "loan_amount" in df.columns and "income" in df.columns:
        df["debt_to_income"] = df["loan_amount"] / df["income"].replace({0: 1})

    feature_cols = [c for c in ["debt_to_income", "loan_amount", "income"] if c in df.columns]
    X = df[feature_cols]
    y = df["defaulted"] if "defaulted" in df.columns else pd.Series([0] * len(df))
    return X, y
