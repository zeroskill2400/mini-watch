from contextlib import contextmanager
import json

from soar_store import connect_state


@contextmanager
def transaction():
    connection = connect_state()
    connection.execute('CREATE TABLE IF NOT EXISTS url_playbook_runs (id TEXT PRIMARY KEY, execution_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)')
    try:
        connection.execute('BEGIN IMMEDIATE')
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def save_run(record):
    with transaction() as connection:
        connection.execute('INSERT INTO url_playbook_runs (id, execution_key, payload) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (record['id'], record['execution_key'], json.dumps(record, ensure_ascii=False)))


def read_run(identifier=None, execution_key=None):
    field, value = ('id', identifier) if identifier is not None else ('execution_key', execution_key)
    with transaction() as connection:
        row = connection.execute('SELECT payload FROM url_playbook_runs WHERE ' + field + '=?', (value,)).fetchone()
        return json.loads(row['payload']) if row else None


def list_runs():
    with transaction() as connection:
        return [json.loads(row['payload']) for row in connection.execute('SELECT payload FROM url_playbook_runs ORDER BY rowid DESC')]
