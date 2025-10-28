import os
import streamlit as st
import pandas as pd
import psycopg2


def _pg_conn_from_env():
    return {
        "dbname": os.environ.get("PG_DB", "creditdb"),
        "user": os.environ.get("PG_USER", "postgres"),
        "password": os.environ.get("PG_PASSWORD", "postgres"),
        "host": os.environ.get("PG_HOST", "localhost"),
        "port": int(os.environ.get("PG_PORT", 5432)),
    }


def fetch_scores(pg_conn):
    conn = psycopg2.connect(**pg_conn)
    try:
        df = pd.read_sql("SELECT * FROM risk_scores", conn)
    finally:
        conn.close()
    return df


def main():
    st.set_page_config(page_title="Credit Risk Dashboard", layout="wide")
    st.title("Credit Risk Dashboard")

    pg = _pg_conn_from_env()
    df = fetch_scores(pg)

    if df.empty:
        st.info("No risk scores available yet. Start the stream processor or insert sample rows into `risk_scores` table.")
        return

    st.subheader("Latest risk scores")
    st.dataframe(df.sort_values("last_updated", ascending=False).head(200))

    # import plotly on demand so the module can be imported even if plotly
    # isn't installed in the environment used for static checks
    try:
        import plotly.express as px
    except Exception:
        st.warning("Plotly not installed; install plotly to view charts.")
        return

    score_col = "posterior_prob" if "posterior_prob" in df.columns else ("prior_prob" if "prior_prob" in df.columns else None)
    if score_col:
        fig = px.histogram(df, x=score_col, nbins=30, title="Risk score distribution")
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
