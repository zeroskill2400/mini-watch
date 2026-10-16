from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path

from detection_rules import LOGIN_PATHS, parse_time


WINDOW_SECONDS = 300
SAMPLE_LIMIT = 40
MAX_SOURCE_BYTES = 8 * 1024 * 1024
FIELDS = {'event_id', 'request_id', 'occurred_at', 'event_type', 'method', 'path', 'status_code', 'attempted_username', 'authenticated_username', 'auth_event_id', 'server_id'}
SCOPE_NOTE = '공지 저장 시각까지 최대 5분의 일반 앱 서버 전체 요청입니다. nginx 복제 기록과 내부 API·health 요청은 세지 않습니다.'
IDENTITY_NOTE = '실패 때 입력한 계정 이름은 인증된 사용자나 같은 사람의 증거가 아닙니다. 여러 사용자의 요청이 섞일 수 있습니다.'


def content_hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def auth_kind(event):
    if event['method'] != 'POST' or event['path'] not in LOGIN_PATHS:
        return None
    if event['event_type'] == 'auth_failure' and event['status_code'] == 401 and event.get('attempted_username'):
        return 'failure'
    if event['event_type'] == 'auth_success' and event['status_code'] == 200 and event.get('authenticated_username'):
        return 'success'
    return None


def build_history(case):
    directory = Path(os.environ.get('CLASSROOM_LOG_DIR', '/classroom-logs'))
    end = parse_time(case['write']['occurred_at'])
    requested_start = end - timedelta(seconds=WINDOW_SECONDS)
    start = requested_start
    invalid = 0
    duplicates = 0
    excluded_internal = 0
    marker = {}
    limitations = [SCOPE_NOTE, IDENTITY_NOTE, '서버가 읽은 app 원본에 실제로 저장된 완료 요청만 집계합니다. 기록되지 않은 시도는 알 수 없습니다.']
    complete = True
    source_truncated = False
    try:
        marker = json.loads((directory / 'request-history-start.json').read_text(encoding='utf-8'))
        if marker.get('schema_version') != 2 or type(marker.get('start_offset')) is not int or marker['start_offset'] < 0:
            raise ValueError('invalid coverage marker')
        start = max(requested_start, parse_time(marker['started_at']))
        path = directory / 'app.jsonl'
        size = path.stat().st_size
        if size < marker['start_offset'] or start > end:
            raise ValueError('source coverage changed')
        offset = max(marker['start_offset'], size - MAX_SOURCE_BYTES)
        source_truncated = offset != marker['start_offset']
        with path.open('rb') as source:
            source.seek(offset)
            data = source.read(MAX_SOURCE_BYTES)
        lines = data.splitlines(keepends=True)
        if source_truncated:
            lines = lines[1:]
            complete = False
            limitations.append('원본 읽기 상한을 넘어 일부 요청이 빠질 수 있습니다. 표시 건수는 확인한 부분이며 전체 건수로 단정하지 않습니다.')
    except (OSError, ValueError, TypeError, UnicodeError):
        lines = []
        complete = False
        limitations.append('요청 이력의 기록 시작점이나 원본을 확인하지 못했습니다.')
    requests = {}
    seen_events = set()
    for line in lines:
        try:
            if not line.endswith(b'\n'):
                raise ValueError('incomplete line')
            raw = json.loads(line.decode('utf-8'))
            if not isinstance(raw, dict):
                raise ValueError('invalid record')
            occurred = parse_time(raw.get('occurred_at'))
            if not start <= occurred <= end:
                continue
            if raw.get('source') is None or raw.get('server_id') is None:
                raise ValueError('request source missing')
            if raw.get('source') != 'app' or raw.get('server_id') != case['server_id']:
                continue
            if raw.get('path') == '/health' or str(raw.get('path', '')).startswith('/internal/'):
                excluded_internal += 1
                continue
            if any(not isinstance(raw.get(field), str) or not 1 <= len(raw[field]) <= 256 for field in ['event_id', 'request_id', 'method', 'path', 'event_type']):
                raise ValueError('request identity missing')
            if type(raw.get('status_code')) is not int or not 100 <= raw['status_code'] <= 599:
                raise ValueError('status missing')
            event = {field: raw[field] for field in FIELDS if field in raw}
            request_id = event['request_id']
            if event['event_id'] in seen_events:
                duplicates += 1
                continue
            seen_events.add(event['event_id'])
            if request_id in requests:
                duplicates += 1
                previous = requests[request_id]
                if auth_kind(event) and not auth_kind(previous):
                    requests[request_id] = event
            else:
                requests[request_id] = event
        except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
            invalid += 1
    ordered = sorted(requests.values(), key=lambda event: (parse_time(event['occurred_at']), event['event_id']))
    failure_ids = [event['event_id'] for event in ordered if auth_kind(event) == 'failure']
    success_ids = [event['event_id'] for event in ordered if auth_kind(event) == 'success']
    if invalid:
        complete = False
        limitations.append('시각·요청 번호·형식을 확인하지 못한 원본이 있어 이력 전체를 확정할 수 없습니다.')
    trigger_present = any(event['event_id'] == case['write']['event_id'] for event in ordered)
    if not trigger_present:
        complete = False
        limitations.append('이번 공지 저장 요청이 집계 원본에 없습니다. 누락 상태로 대응하지 않습니다.')
    if start > requested_start:
        limitations.append('새 요청 기록 형식의 시작 시각부터 읽었으므로 아직 5분 전체가 아닙니다.')
    selected = ordered if len(ordered) <= SAMPLE_LIMIT else [event for event in ordered if auth_kind(event)][-20:] + [event for event in ordered if not auth_kind(event)][-20:]
    selected = sorted(selected, key=lambda event: (parse_time(event['occurred_at']), event['event_id']))
    if len(ordered) > len(selected):
        limitations.append('건수는 확인한 창 전체에서 집계했지만 상세 원본과 AI 입력은 최대40건 표본입니다.')
    effective_seconds = max(0, (end - start).total_seconds())
    history = {
        'schema_version': 1, 'source': 'app.jsonl', 'scope_note': SCOPE_NOTE, 'identity_note': IDENTITY_NOTE,
        'window': {'requested_seconds': WINDOW_SECONDS, 'started_at': start.isoformat(), 'ended_at': end.isoformat(), 'effective_seconds': round(effective_seconds, 6), 'clipped_to_logging_start': start > requested_start},
        'request_count': len(ordered), 'login_failure_count': len(failure_ids), 'login_success_count': len(success_ids),
        'requests_per_minute': round(len(ordered) * 60 / effective_seconds, 2) if effective_seconds >= 1 else None,
        'timeline': deepcopy(selected), 'failure_event_ids': failure_ids, 'success_event_ids': success_ids,
        'trigger_event_id': case['write']['event_id'],
        'sample': {'limit': SAMPLE_LIMIT, 'total_count': len(ordered), 'shown_count': len(selected), 'truncated': len(selected) < len(ordered)},
        'quality': {'complete': complete, 'invalid_line_count': invalid, 'duplicate_request_count': duplicates, 'older_records_excluded': marker.get('older_records_excluded', 0), 'source_truncated': source_truncated, 'internal_requests_excluded': excluded_internal, 'limitations': limitations},
    }
    history['snapshot_hash'] = content_hash(history)
    return history
