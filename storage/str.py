# storage/str.py
import psycopg2
import psycopg2.extras
from datetime import datetime


def get_connection(pg_conn):
    """Return a new psycopg2 connection using a dict of connection params."""
    return psycopg2.connect(**pg_conn)


def save_risk_score(pg_conn, applicant_id, prior_prob=None, posterior_prob=None, last_event=None):
    """Upsert a risk score row into canonical `risk_scores` table.

    The table schema (created if missing):
      applicant_id INT PRIMARY KEY,
      prior_prob FLOAT,
      posterior_prob FLOAT,
      last_updated TIMESTAMP,
      last_event JSONB
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS risk_scores (
        applicant_id INTEGER PRIMARY KEY,
        prior_prob DOUBLE PRECISION,
        posterior_prob DOUBLE PRECISION,
        last_updated TIMESTAMP,
        last_event JSONB
    );
    """

    insert_sql = """
    INSERT INTO risk_scores (applicant_id, prior_prob, posterior_prob, last_updated, last_event)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (applicant_id) DO UPDATE SET
      prior_prob = COALESCE(EXCLUDED.prior_prob, risk_scores.prior_prob),
      posterior_prob = COALESCE(EXCLUDED.posterior_prob, risk_scores.posterior_prob),
      last_updated = EXCLUDED.last_updated,
      last_event = EXCLUDED.last_event;
    """

    with get_connection(pg_conn) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
            cur.execute(insert_sql, (
                applicant_id,
                prior_prob,
                posterior_prob,
                datetime.utcnow(),
                psycopg2.extras.Json(last_event) if last_event is not None else None,
            ))
        conn.commit()
