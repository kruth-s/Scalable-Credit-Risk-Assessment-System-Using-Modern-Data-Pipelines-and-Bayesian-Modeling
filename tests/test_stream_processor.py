import json
from datetime import datetime, timedelta

import pytest

from ingestion import stream_processor


class FakeCursor:
    def __init__(self, storage):
        self.storage = storage

    def execute(self, sql, params=None):
        # simple parser for the SELECT and INSERT used in stream_processor
        sql_lower = sql.lower()
        if sql_lower.strip().startswith("select"):
            # expect WHERE customer_id = %s
            cid = params[0]
            row = self.storage.get(cid)
            if row is None:
                self._last = None
            else:
                # return tuple (prior, posterior, last_updated)
                self._last = (row["prior"], row["posterior"], row["last_updated"])
        elif sql_lower.strip().startswith("insert"):
            cid = params[0]
            prior = params[1]
            posterior = params[2]
            last_updated = params[3]
            event = json.loads(params[4]) if isinstance(params[4], str) else params[4]
            # upsert
            self.storage[cid] = {"prior": prior, "posterior": posterior, "last_updated": last_updated, "event": event}
            self._last = None

    def fetchone(self):
        return self._last


class FakeConn:
    def __init__(self):
        self.storage = {}

    def cursor(self):
        return FakeCursor(self.storage)

    def commit(self):
        pass


def test_handle_event_idempotency():
    conn = FakeConn()
    # first event: should be processed
    now = datetime.utcnow()
    ev1 = {"customer_id": "c1", "event_type": "payment_missed", "timestamp": now.isoformat()}
    processed1 = stream_processor.handle_event(conn, ev1)
    assert processed1 is True
    assert "c1" in conn.storage

    # second event older than stored last_updated -> should be skipped
    older = (now - timedelta(minutes=10)).isoformat()
    ev2 = {"customer_id": "c1", "event_type": "payment_made", "timestamp": older}
    processed2 = stream_processor.handle_event(conn, ev2)
    assert processed2 is False
