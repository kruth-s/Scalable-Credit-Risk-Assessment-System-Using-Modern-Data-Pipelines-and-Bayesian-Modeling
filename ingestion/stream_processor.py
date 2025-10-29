# ingestion/stream_processor.py
"""
Consumes events from Kafka, does simple feature update and Bayesian risk update,
and writes/updates a 'risk_scores' table in Postgres.
"""

import json
import os
from kafka import KafkaConsumer
import psycopg2
from datetime import datetime
from scipy.stats import beta  # example; we will use simple Bayes math

# Config from environment
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.environ.get("KAFKA_TOPIC", "credit_behavior")
GROUP_ID = os.environ.get("KAFKA_CONSUMER_GROUP", "risk_processor")

PG_CONN = {
    "dbname": os.environ.get("PG_DB", "creditdb"),
    "user": os.environ.get("PG_USER", "youruser"),
    "password": os.environ.get("PG_PASSWORD", "yourpass"),
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", 5432)),
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
                customer_id UUID PRIMARY KEY,
                prior_prob DOUBLE PRECISION,
                posterior_prob DOUBLE PRECISION,
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
    customer_id = event.get("customer_id")
    aid = customer_id
    ev_type = event["event_type"]
    # parse incoming event timestamp
    event_ts = None
    try:
        event_ts = datetime.fromisoformat(event.get("timestamp")) if event.get("timestamp") else None
    except Exception:
        event_ts = None

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
        # get current prior/posterior and last_updated if exists
        cur.execute("SELECT prior_prob, posterior_prob, last_updated FROM risk_scores WHERE customer_id = %s;", (aid,))
        res = cur.fetchone()
        if res:
            prior = res[1]  # use previous posterior as new prior
            last_updated = res[2]
        else:
            prior = PRIOR_ALPHA / (PRIOR_ALPHA + PRIOR_BETA)
            last_updated = None

        # idempotency: skip if event is older than last_updated
        if last_updated is not None and event_ts is not None:
            try:
                # compare naive datetimes (both UTC naive)
                if event_ts <= last_updated:
                    # skip processing
                    return False
            except Exception:
                pass

        posterior = bayes_update(prior, p_e_given_r, p_e_given_not_r)
        now = datetime.utcnow()

        # upsert
        cur.execute("""
            INSERT INTO risk_scores (customer_id, prior_prob, posterior_prob, last_updated, last_event)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                prior_prob = EXCLUDED.prior_prob,
                posterior_prob = EXCLUDED.posterior_prob,
                last_updated = EXCLUDED.last_updated,
                last_event = EXCLUDED.last_event;
        """, (aid, prior, posterior, now, json.dumps(event)))
        conn.commit()
        return True

def run_consumer():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    conn = connect_db()
    ensure_table(conn)
    print("Listening for events...")
    try:
        for msg in consumer:
            ev = msg.value
            try:
                processed = handle_event(conn, ev)
                if processed:
                    # commit the offset only after successful DB write
                    consumer.commit()
            except Exception as e:
                print("Error processing event:", e)
                # do not commit; message will be retried
    except KeyboardInterrupt:
        print("Shutting down consumer")
    finally:
        conn.close()

if __name__ == "__main__":
    run_consumer()
