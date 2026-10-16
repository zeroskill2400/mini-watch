import json
import logging
import os
from pathlib import Path
import sqlite3
from threading import Event, Lock, Thread

from detection_rules import parse_time
from investigation_service import read_investigation
from soar_service import now
from url_playbook_service import candidate, create_automatic_run
from url_playbook_store import read_run, transaction


POLL_INTERVAL_SECONDS = 1
WORKER = None
STOP = Event()
START_LOCK = Lock()


def prepare_automation():
    with transaction() as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS playbook_automation (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS playbook_auto_events (write_event_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        existing = connection.execute('SELECT payload FROM playbook_automation WHERE id=1').fetchone()
        if existing:
            return json.loads(existing['payload'])
        state = {'activated_at': now(), 'status': 'watching', 'last_poll_at': None, 'last_error': None}
        connection.execute('INSERT INTO playbook_automation (id,payload) VALUES (1,?)', (json.dumps(state, ensure_ascii=False),))
        return state


def read_state(connection):
    row = connection.execute('SELECT payload FROM playbook_automation WHERE id=1').fetchone()
    return json.loads(row['payload']) if row else None


def save_state(connection, state):
    connection.execute('UPDATE playbook_automation SET payload=? WHERE id=1', (json.dumps(state, ensure_ascii=False),))


def automation_status():
    status = {
        'enabled': os.environ.get('PLAYBOOK_DISABLE_AUTO_WORKER') != '1',
        'actor': 'system', 'trigger': 'notice_file_change', 'poll_interval_seconds': POLL_INTERVAL_SECONDS,
        'activated_at': None, 'status': 'not_started', 'last_poll_at': None, 'last_error': None,
        'processed_count': 0, 'failed_count': 0, 'latest_events': [],
    }
    filename = Path(os.environ.get('SOAR_STATE_PATH', '/detection-state/soar.sqlite3'))
    if not filename.exists():
        return status
    connection = sqlite3.connect(filename.resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        state = read_state(connection)
        if state:
            status.update(state)
        events = [json.loads(row['payload']) for row in connection.execute('SELECT payload FROM playbook_auto_events ORDER BY rowid DESC')]
        status.update({
            'processed_count': sum(item['status'] in {'completed', 'failed'} for item in events),
            'failed_count': sum(item['status'] == 'failed' for item in events),
            'latest_events': events[:30],
        })
        return status
    except sqlite3.OperationalError:
        return status
    finally:
        connection.close()


def claim_event(selected):
    event = {
        'write_event_id': selected['case']['write']['event_id'],
        'sensor_event_id': selected['case']['sensor']['event_id'],
        'case_id': selected['case_id'], 'run_id': None, 'status': 'processing',
        'started_at': now(), 'finished_at': None, 'error': None,
    }
    with transaction() as connection:
        result = connection.execute('INSERT OR IGNORE INTO playbook_auto_events (write_event_id,payload) VALUES (?,?)', (event['write_event_id'], json.dumps(event, ensure_ascii=False)))
        if result.rowcount != 1:
            return None
        state = read_state(connection)
        state['status'] = 'processing'
        save_state(connection, state)
    return event


def finish_event(event, record=None, error=None):
    if record:
        event['run_id'] = record['id']
        if record['state'] in {'error', 'recovery_error', 'running', 'recovering'}:
            error = record.get('last_error') or '자동 실행 결과를 완료하지 못했습니다.'
    event.update({'status': 'failed' if error else 'completed', 'error': error, 'finished_at': now()})
    with transaction() as connection:
        connection.execute('UPDATE playbook_auto_events SET payload=? WHERE write_event_id=?', (json.dumps(event, ensure_ascii=False), event['write_event_id']))
        state = read_state(connection)
        state.update({'status': 'error' if error else 'watching', 'last_error': error})
        save_state(connection, state)


def recover_auto_events():
    with transaction() as connection:
        events = [json.loads(row['payload']) for row in connection.execute('SELECT payload FROM playbook_auto_events')]
    for event in events:
        if event['status'] != 'processing':
            continue
        record = read_run(execution_key='auto:' + event['write_event_id'])
        error = None if record and record['state'] not in {'running', 'recovering', 'error', 'recovery_error'} else '재시작 전에 자동 실행 결과를 마치지 못했습니다. 이전 사건을 자동 재실행하지 않습니다. 실제 조치가 적용됐다면 해당 실행에서 확인하거나 복구해 주세요.'
        finish_event(event, record, error)


def worker_tick():
    status = automation_status()
    if not status['activated_at']:
        return
    activation = parse_time(status['activated_at'])
    report = read_investigation(limit=None, started_at=status['activated_at'])
    strict = report['correlation'].get('require_same_hash') is True
    cases = sorted(report['cases'], key=lambda item: (parse_time(item['write']['occurred_at']), parse_time(item['sensor']['occurred_at']), item['id']))
    for case in cases:
        if parse_time(case['write']['occurred_at']) <= activation:
            continue
        selected = candidate(case, strict)
        if not selected['eligible']:
            continue
        event = claim_event(selected)
        if event is None:
            continue
        try:
            record = create_automatic_run(selected, status['activated_at'])
            finish_event(event, record)
        except Exception as error:
            finish_event(event, error=str(error) or '자동 실행을 시작하지 못했습니다. 다음 새 공지 사건에서 다시 확인해 주세요.')
            logging.exception('새 공지 사건의 자동 실행에 실패했습니다. 같은 사건은 다시 실행하지 않습니다.')
    with transaction() as connection:
        state = read_state(connection)
        state['last_poll_at'] = now()
        save_state(connection, state)


def worker_loop():
    while not STOP.is_set():
        try:
            worker_tick()
        except Exception:
            logging.exception('공지 자동 감지에 실패했습니다. 다음 주기에 감지를 계속합니다.')
            try:
                with transaction() as connection:
                    state = read_state(connection)
                    state.update({'status': 'error', 'last_poll_at': now(), 'last_error': '공지 사건을 읽지 못했습니다. 서버가 다음 주기에 다시 확인합니다. 기존 실행은 보존합니다.'})
                    save_state(connection, state)
            except Exception:
                logging.exception('자동 감지 오류 상태를 기록하지 못했습니다.')
        STOP.wait(POLL_INTERVAL_SECONDS)


def start_auto_worker():
    global WORKER
    if os.environ.get('PLAYBOOK_DISABLE_AUTO_WORKER') == '1':
        return None
    with START_LOCK:
        if WORKER is not None and WORKER.is_alive():
            return WORKER
        prepare_automation()
        recover_auto_events()
        STOP.clear()
        WORKER = Thread(target=worker_loop, name='notice-playbook-auto-worker', daemon=True)
        WORKER.start()
        return WORKER
