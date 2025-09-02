# storage/str.py
import psycopg2

def get_connection(pg_conn):
    return psycopg2.connect(**pg_conn)

def save_risk_score(pg_conn, user_id, score):
    with get_connection(pg_conn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO risk_scores (user_id, score, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                score = EXCLUDED.score, updated_at = EXCLUDED.updated_at;
            """, (user_id, score))
