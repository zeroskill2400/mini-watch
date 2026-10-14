import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from scapy.all import rdpcap
from db import connect_db

DATA = Path(__file__).parent / "data"


def read_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_audit(raw):
    actor_map = read_json("actor-map.json")
    return {
        "id": raw["id"], "source": "audit_demo", "kind": raw["action"],
        "occurred_at": raw["at"], "actor": actor_map.get(raw["person"]),
        "original_actor": raw["person"], "ip": raw["address"],
    }


def audit_events():
    return [normalize_audit(raw) for raw in read_json("audit-raw.json")]


def failures_before(download, events, max_seconds=300):
    failures = []
    if not download.get("actor"):
        return failures
    for event in events:
        if event["kind"] != "login_failure" or event["actor"] != download["actor"]:
            continue
        gap = (parse_time(download["occurred_at"]) - parse_time(event["occurred_at"])).total_seconds()
        if 0 < gap <= max_seconds:
            failures.append(event)
    return failures


def read_capture(name):
    return rdpcap(str(DATA / name))


def capture_summary(name, seconds=5):
    packets = read_capture(name)
    start = min(float(packet.time) for packet in packets)
    selected = [packet for packet in packets if start <= float(packet.time) < start + seconds]
    return {"name": name, "seconds": seconds, "packets": len(selected),
            "bytes": sum(len(bytes(packet)) for packet in selected)}


def last_event_id():
    with connect_db() as conn:
        return conn.execute("SELECT COALESCE(MAX(id), 0) AS id FROM http_events").fetchone()["id"]


def live_events(after_id, seconds=60, reference_at=None):
    now = reference_at or datetime.now(timezone.utc)
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT * FROM http_events WHERE id > %s AND occurred_at >= %s "
            "AND occurred_at <= %s ORDER BY id",
            (after_id, now - timedelta(seconds=seconds), now),
        ).fetchall()
    for row in rows:
        row["id"] = "http-" + str(row["id"])
        row["source"] = "http_live"
        row["kind"] = row["event_type"]
        row["occurred_at"] = row["occurred_at"].isoformat()
        row["actor"] = None
        row["ip"] = None
    return rows, now.isoformat()
