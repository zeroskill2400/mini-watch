import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from detection_rules import build_detection, normalize_auth_event
from learning.log_data import read_complete_lines

STATE_PATH = Path(os.environ.get("DETECTION_STATE_PATH", "/detection-state/observations.sqlite3"))


def connect_state():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(STATE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS observations "
        "(sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, started_at TEXT NOT NULL)"
    )
    return connection


def start_observation():
    observation = {
        "id": str(uuid4()),
        "started_at": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
    }
    with connect_state() as connection:
        connection.execute(
            "INSERT INTO observations (id, started_at) VALUES (?, ?)",
            (observation["id"], observation["started_at"]),
        )
    connection.close()
    return observation


def current_observation():
    with connect_state() as connection:
        row = connection.execute(
            "SELECT id, started_at FROM observations ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
    connection.close()
    return dict(row) if row else None


def prepare_observation():
    connection = connect_state()
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT id, started_at FROM observations ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)
            observation = {
                "id": str(uuid4()),
                "started_at": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            }
            connection.execute(
                "INSERT INTO observations (id, started_at) VALUES (?, ?)",
                (observation["id"], observation["started_at"]),
            )
            return observation
    finally:
        connection.close()


def read_detection():
    events = []
    invalid_line_count = 0
    for line in read_complete_lines("app.jsonl"):
        try:
            event = normalize_auth_event(json.loads(line))
        except (ValueError, TypeError, OverflowError):
            invalid_line_count += 1
            continue
        if event:
            events.append(event)
    return build_detection(
        events, current_observation(), datetime.now(timezone.utc), invalid_line_count
    )
