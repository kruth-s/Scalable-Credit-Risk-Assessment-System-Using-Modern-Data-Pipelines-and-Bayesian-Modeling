# ingestion/stream_processor.py
"""
Consumes events from Kafka, does simple feature update and Bayesian risk update,
and writes/updates a 'risk_scores' table in Postgres.
"""

import json
from kafka import KafkaConsumer
import psycopg2
from datetime import datetime
from scipy.stats import beta  # example; we will use simple Bayes math

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "credit_behavior"
PG_CONN = {
    "dbname": "creditdb",
    "user": "youruser",
    "password": "yourpass",
    "host": "localhost",
    "port": 5432
}

# Example hyperparams for Bayes (naive)
# P(risk) prior modeled as Beta(alpha, beta)
PRIOR_ALPHA = 2.0
PRIOR_BETA = 8.0

def connect_db():
    return psycopg2.connect(**PG_CONN)

def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS risk_scores (
                applicant_id INT PRIMARY KEY,
                prior_prob FLOAT,
                posterior_prob FLOAT,
                last_updated TIMESTAMP,
                last_event JSONB
            );
        """)
        conn.commit()

def bayes_update(prior, evidence_likelihood, evidence_not_likelihood):
    """
    naive Bayes update:
    prior -> P(R)
    evidence_likelihood -> P(E | R)
    evidence_not_likelihood -> P(E | ~R)
    returns posterior P(R | E)
    """
    numerator = evidence_likelihood * prior
    denominator = numerator + evidence_not_likelihood * (1 - prior)
    if denominator == 0:
        return prior
    return numerator / denominator

def handle_event(conn, event):
    aid = event["applicant_id"]
    ev_type = event["event_type"]

    # map event to likelihoods (these are naive / tunable)
    if ev_type == "payment_missed":
        p_e_given_r = 0.8
        p_e_given_not_r = 0.2
    elif ev_type == "utilization_spike":
        p_e_given_r = 0.6
        p_e_given_not_r = 0.3
    else:  # payment_made
        p_e_given_r = 0.2
        p_e_given_not_r = 0.5

    with conn.cursor() as cur:
        # get current prior/posterior if exists
        cur.execute("SELECT prior_prob, posterior_prob FROM risk_scores WHERE applicant_id = %s;", (aid,))
        res = cur.fetchone()
        if res:
            prior = res[1]  # use previous posterior as new prior
        else:
            prior = PRIOR_ALPHA / (PRIOR_ALPHA + PRIOR_BETA)

        posterior = bayes_update(prior, p_e_given_r, p_e_given_not_r)
        now = datetime.utcnow()

        # upsert
        cur.execute("""
            INSERT INTO risk_scores (applicant_id, prior_prob, posterior_prob, last_updated, last_event)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (applicant_id) DO UPDATE SET
                prior_prob = EXCLUDED.prior_prob,
                posterior_prob = EXCLUDED.posterior_prob,
                last_updated = EXCLUDED.last_updated,
                last_event = EXCLUDED.last_event;
        """, (aid, prior, posterior, now, json.dumps(event)))
        conn.commit()

def run_consumer():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    conn = connect_db()
    ensure_table(conn)
    print("Listening for events...")
    try:
        for msg in consumer:
            ev = msg.value
            handle_event(conn, ev)
    except KeyboardInterrupt:
        print("Shutting down consumer")
    finally:
        conn.close()

if __name__ == "__main__":
    run_consumer()
