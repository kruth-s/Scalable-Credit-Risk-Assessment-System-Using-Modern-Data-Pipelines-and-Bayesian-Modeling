# ingestion/kafka_producer.py
"""
Simple Kafka producer that simulates streaming customer events:
 - payment_made
 - payment_missed
 - credit_utilization_spike

Each event contains: applicant_id, event_type, amount, timestamp, current_credit_util
"""

import argparse
import json
import os
import random
import time
from datetime import datetime
from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.environ.get("KAFKA_TOPIC", "credit_behavior")


def get_producer(bootstrap_servers=KAFKA_BOOTSTRAP):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8"),
        linger_ms=10,
    )


import uuid


def random_event(customer_id):
    ev_type = random.choices(
        ["payment_made", "payment_missed", "utilization_spike"],
        weights=[0.85, 0.1, 0.05],
    )[0]
    event = {
        "customer_id": str(customer_id),
        "event_type": ev_type,
        "amount": round(random.uniform(50, 2000), 2),
        "current_credit_util": round(random.uniform(0.05, 0.95), 2),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return event


def run(produce_rate=100, max_applicants=1000, total_count=None, bootstrap=KAFKA_BOOTSTRAP, topic=TOPIC):
    """Produce events. If total_count is provided, produce that many events then exit."""
    producer = get_producer(bootstrap)
    sent = 0
    # prepare a list of customer UUIDs to sample from (keeps keys stable)
    if isinstance(max_applicants, int):
        customers = [uuid.uuid4() for _ in range(max_applicants)]
    else:
        customers = max_applicants

    try:
        while True:
            batch = produce_rate if total_count is None else min(produce_rate, total_count - sent)
            for _ in range(batch):
                cust = random.choice(customers)
                ev = random_event(cust)
                # use customer_id as key (string) to ensure partition affinity
                producer.send(topic, value=ev, key=str(cust))
                sent += 1
                if total_count is not None and sent >= total_count:
                    break
            producer.flush()
            if total_count is not None and sent >= total_count:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped producer")
    finally:
        try:
            producer.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=int, default=100, help="events per second")
    parser.add_argument("--max-customers", type=int, default=1000)
    parser.add_argument("--count", type=int, default=None, help="total events to emit then exit")
    parser.add_argument("--bootstrap", type=str, default=os.environ.get("KAFKA_BOOTSTRAP", KAFKA_BOOTSTRAP))
    parser.add_argument("--topic", type=str, default=os.environ.get("KAFKA_TOPIC", TOPIC))
    args = parser.parse_args()
    print(f"Producing to {args.topic} on {args.bootstrap} ...")
    run(produce_rate=args.rate, max_applicants=args.max_customers, total_count=args.count, bootstrap=args.bootstrap, topic=args.topic)


if __name__ == "__main__":
    main()
