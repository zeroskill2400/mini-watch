import json
import os
from pathlib import Path
import sqlite3


def connect_state():
    filename = Path(os.environ.get('SOAR_STATE_PATH', '/detection-state/soar.sqlite3'))
    filename.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(filename, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute('CREATE TABLE IF NOT EXISTS response_requests (id TEXT PRIMARY KEY, case_id TEXT UNIQUE NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL)')
    return connection


def prepare_state():
    connection = connect_state()
    connection.close()


def save_request(connection, record):
    connection.execute('INSERT INTO response_requests (id, case_id, state, payload) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET state=excluded.state, payload=excluded.payload', (record['id'], record['case_id'], record['state'], json.dumps(record, ensure_ascii=False)))


def read_request(connection, identifier):
    row = connection.execute('SELECT payload FROM response_requests WHERE id=?', (identifier,)).fetchone()
    return json.loads(row['payload']) if row else None


def list_requests():
    connection = connect_state()
    try:
        return [json.loads(row['payload']) for row in connection.execute('SELECT payload FROM response_requests ORDER BY rowid DESC')]
    finally:
        connection.close()
