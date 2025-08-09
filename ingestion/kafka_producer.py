# ingestion/kafka_producer.py
"""
Simple Kafka producer that simulates streaming customer events:
 - payment_made
 - payment_missed
 - credit_utilization_spike

Each event contains: applicant_id, event_type, amount, timestamp, current_credit_util
"""

import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "credit_behavior"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=10
)

def random_event(applicant_id):
    ev_type = random.choices(
        ["payment_made", "payment_missed", "utilization_spike"],
        weights=[0.85, 0.1, 0.05],
    )[0]
    event = {
        "applicant_id": applicant_id,
        "event_type": ev_type,
        "amount": round(random.uniform(50, 2000), 2),
        "current_credit_util": round(random.uniform(0.05, 0.95), 2),
        "timestamp": datetime.utcnow().isoformat()
    }
    return event

def run(produce_rate=100, max_applicants=1000):
    """
    produce_rate: events per second
    max_applicants: range of applicant IDs to simulate
    """
    try:
        while True:
            for _ in range(produce_rate):
                aid = random.randint(1, max_applicants)
                ev = random_event(aid)
                producer.send(TOPIC, ev)
            producer.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped producer")

if __name__ == "__main__":
    print(f"Producing to {TOPIC} on {KAFKA_BOOTSTRAP} ...")
    run()
