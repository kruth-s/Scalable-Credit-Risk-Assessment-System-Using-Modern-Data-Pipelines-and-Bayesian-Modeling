# processing/pr.py
import pandas as pd

def transform_loan_data(df: pd.DataFrame) -> pd.DataFrame:
    df["debt_to_income"] = df["loan_amount"] / df["income"]
    df["has_previous_default"] = df["past_defaults"] > 0
    return df
