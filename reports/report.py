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
    app = Dash(__name__)
    df = fetch_scores(pg_conn)
    fig = px.histogram(df, x="score", nbins=20, title="Risk Score Distribution")
    
    app.layout = html.Div([
        html.H1("Credit Risk Report"),
        dcc.Graph(figure=fig)
    ])
    return app
