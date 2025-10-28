# processing/pr.py
import pandas as pd


def transform_loan_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize incoming loan dataframe and compute derived features.

    Accepts dataframes produced by `data/generate_loan_data.py` (which may use
    TitleCase column names) as well as already-normalized frames. Returns a
    dataframe with lowercase columns and two derived columns:
    - debt_to_income: loan_amount / income (safe division)
    - has_previous_default: boolean from past_defaults > 0
    """
    # normalize common TitleCase columns from the generator to lowercase names
    col_map = {
        "Loan_Amount": "loan_amount",
        "Income": "income",
        "Past_Defaults": "past_defaults",
        # keep existing lowercase names as-is if present
    }
    # Only rename columns that are present
    cols_to_rename = {k: v for k, v in col_map.items() if k in df.columns}
    if cols_to_rename:
        df = df.rename(columns=cols_to_rename)

    # Ensure expected columns exist; if not, create sensible defaults
    if "loan_amount" not in df.columns:
        df["loan_amount"] = 0.0
    if "income" not in df.columns:
        df["income"] = 1.0  # avoid division by zero
    if "past_defaults" not in df.columns:
        df["past_defaults"] = 0

    # safe computation
    df["debt_to_income"] = df["loan_amount"].astype(float) / df["income"].replace({0: 1.0})
    df["has_previous_default"] = df["past_defaults"].astype(int) > 0
    return df
