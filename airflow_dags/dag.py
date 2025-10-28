"""A minimal Airflow DAG (Python) to demonstrate batch ingestion.

This DAG is a lightweight placeholder that reads `data/loan_applications.csv`,
runs `processing.pr.transform_loan_data`, and writes a transformed CSV to /tmp.

Install and enable Apache Airflow to use this DAG. It's intentionally simple
so it can be replaced with your production DAG logic later.
"""
from datetime import datetime, timedelta
import importlib
import sys
import os

# try to import transform function from processing.pr, adjusting sys.path if needed
try:
    from processing.pr import transform_loan_data
except Exception:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from processing.pr import transform_loan_data

# Airflow is optional for static checks in dev environments; make imports resilient
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except Exception:
    DAG = None
    PythonOperator = None
    AIRFLOW_AVAILABLE = False

import pandas as pd

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def ingest_and_transform():
    df = pd.read_csv("data/loan_applications.csv")
    df = transform_loan_data(df)
    out = "/tmp/transformed_loans.csv"
    df.to_csv(out, index=False)


if AIRFLOW_AVAILABLE:
    with DAG("batch_ingest", default_args=default_args, schedule_interval="@daily", catchup=False) as dag:
        task_ingest = PythonOperator(
            task_id="ingest_and_transform",
            python_callable=ingest_and_transform,
        )
else:
    # placeholder so module can be imported in environments without Airflow
    dag = None
