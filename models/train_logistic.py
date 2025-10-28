"""Train a logistic baseline from loan_applications and features stored in Postgres.

This script is intentionally minimal for demo purposes. It will:
 - connect to Postgres
 - load loan_applications, compute simple features via processing.pr.transform_loan_data if needed
 - train a sklearn pipeline (StandardScaler + LogisticRegression)
 - save artifact to models/logistic_v1.joblib
 - write metadata to model_registry table
"""
import os
import joblib
import psycopg2
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from processing.pr import transform_loan_data

# Postgres connection (use env or defaults)
PG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", 5432)),
    "dbname": os.environ.get("PG_DB", "credit_risk"),
    "user": os.environ.get("PG_USER", "kruth"),
    "password": os.environ.get("PG_PASSWORD", "password"),
}

def get_conn():
    return psycopg2.connect(**PG)


def load_applications():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT * FROM loan_applications", conn)
    finally:
        conn.close()
    return df


def main():
    os.makedirs("models", exist_ok=True)
    df = load_applications()
    if df.empty:
        print("No loan_applications found in Postgres (load sample CSV first). Exiting.")
        return

    # normalize and create features
    df = transform_loan_data(df)
    # simple feature set
    feature_cols = [c for c in ["debt_to_income", "loan_amount", "income"] if c in df.columns]
    if not feature_cols:
        print("No suitable feature columns found after transform. Exiting.")
        return

    X = df[feature_cols].fillna(0)
    if "label_default" in df.columns:
        y = df["label_default"].astype(int)
    else:
        print("No label_default column found; creating a dummy label (all zeros) for demo")
        y = pd.Series([0] * len(df))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000))
    ])
    pipe.fit(X_train, y_train)

    # evaluate
    preds = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, preds) if len(set(y_test)) > 1 else None
    print(f"Trained logistic model. AUC: {auc}")

    artifact_path = "models/logistic_v1.joblib"
    joblib.dump(pipe, artifact_path)

    # register model metadata
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS model_registry (model_version TEXT PRIMARY KEY, model_path TEXT, created_at TIMESTAMP DEFAULT now(), metrics JSONB);")
            cur.execute("INSERT INTO model_registry (model_version, model_path, metrics) VALUES (%s,%s,%s) ON CONFLICT (model_version) DO UPDATE SET model_path = EXCLUDED.model_path, metrics = EXCLUDED.metrics;",
                        ("logistic_v1", artifact_path, psycopg2.extras.Json({"auc": auc})))
        conn.commit()
    finally:
        conn.close()

    print(f"Model saved to {artifact_path} and registered.")


if __name__ == "__main__":
    import psycopg2.extras
    main()
