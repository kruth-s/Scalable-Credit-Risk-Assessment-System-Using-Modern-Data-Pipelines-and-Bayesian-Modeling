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

    # customer lookup
    st.sidebar.header("Lookup")
    customer_id = st.sidebar.text_input("Customer ID (UUID)")

    if df.empty:
        st.info("No risk scores available yet. Start the stream processor or insert sample rows into `risk_scores` table.")
        return

    st.subheader("Latest risk scores")
    st.dataframe(df.sort_values("last_updated", ascending=False).head(200))

    # if a customer_id is provided, show details
    if customer_id:
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}")
            q = "SELECT * FROM risk_scores WHERE customer_id = %s"
            cust_df = pd.read_sql(q, engine, params=(customer_id,))
        except Exception:
            cust_df = df[df.get('customer_id') == customer_id]

        st.markdown("### Customer details")
        if cust_df.empty:
            st.info("No data for this customer")
        else:
            st.write(cust_df.T)
            # show features if available
            try:
                conn = psycopg2.connect(**pg)
                feat = pd.read_sql("SELECT * FROM features WHERE customer_id = %s", conn, params=(customer_id,))
                conn.close()
            except Exception:
                feat = pd.DataFrame()

            if not feat.empty:
                st.markdown("#### Features")
                st.write(feat.T)

            # try to show simple contribution using logistic model if available
            try:
                import joblib
                model_path = "models/logistic_v1.joblib"
                if os.path.exists(model_path):
                    pipe = joblib.load(model_path)
                    feature_cols = [c for c in ["debt_to_income", "loan_amount", "income"] if c in feat.columns]
                    if feature_cols:
                        X = feat[feature_cols].fillna(0).values
                        coefs = pipe.named_steps['clf'].coef_[0]
                        contrib = {feature_cols[i]: float(coefs[i] * X[0, i]) for i in range(len(feature_cols))}
                        st.markdown("#### Approx. feature contributions (coef * value)")
                        st.json(contrib)
            except Exception:
                pass

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
