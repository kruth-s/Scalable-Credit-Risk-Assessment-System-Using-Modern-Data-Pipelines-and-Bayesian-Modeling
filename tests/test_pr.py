import pandas as pd
from processing.pr import transform_loan_data


def test_transform_happy_path():
    df = pd.DataFrame({
        "Loan_Amount": [1000, 2000],
        "Income": [5000, 4000],
        "Past_Defaults": [0, 1],
    })
    out = transform_loan_data(df)
    assert "debt_to_income" in out.columns
    assert "has_previous_default" in out.columns
    assert out.loc[0, "debt_to_income"] == 1000 / 5000
    assert out.loc[1, "has_previous_default"] is True


def test_transform_missing_columns():
    df = pd.DataFrame({"some_col": [1, 2]})
    out = transform_loan_data(df)
    # defaulted safe values should exist
    assert "debt_to_income" in out.columns
    assert "has_previous_default" in out.columns
    # when income missing, division uses replacement of 1 to avoid div by zero
    assert (out["debt_to_income"] >= 0).all()
