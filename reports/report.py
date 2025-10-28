# reports/report.py
import psycopg2
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html


def fetch_scores(pg_conn):
    conn = psycopg2.connect(**pg_conn)
    df = pd.read_sql("SELECT * FROM risk_scores", conn)
    conn.close()
    return df


def create_dashboard(pg_conn):
    """Create a Dash dashboard that visualizes posterior_prob when available.

    Falls back to prior_prob or legacy `score` column if necessary.
    """
    app = Dash(__name__)
    df = fetch_scores(pg_conn)

    # choose the best available score column
    score_col = None
    for candidate in ("posterior_prob", "prior_prob", "score"):
        if candidate in df.columns:
            score_col = candidate
            break

    if score_col is None:
        # no usable score column; show a message in the dashboard
        fig = px.histogram(title="No score column found in risk_scores table")
    else:
        fig = px.histogram(df, x=score_col, nbins=20, title=f"Risk Score Distribution ({score_col})")

    app.layout = html.Div([
        html.H1("Credit Risk Report"),
        dcc.Graph(figure=fig)
    ])
    return app
