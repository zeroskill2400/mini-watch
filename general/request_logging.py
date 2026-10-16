import json
import os
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4
import requests
from flask import current_app, g, request

MONITOR_URL = os.environ['MONITOR_URL']
EVENT_TOKEN = os.environ['EVENT_TOKEN']
if len(EVENT_TOKEN) < 32 or EVENT_TOKEN.startswith('CHANGE_ME'):
    raise RuntimeError('EVENT_TOKEN에 직접 생성한 32자 이상의 값을 설정해 주세요.')

LOG_LOCK = Lock()


def authentication_event(username, result):
    event = {
        'event_id': str(uuid4()),
        'occurred_at': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
        'attempted_username': username,
        'event_type': result,
    }
    if result == 'auth_success':
        event['authenticated_username'] = username
    return event


def record_request(response):
    if request.path == '/health':
        return response
    event = {
        'schema_version': 2,
        'source': 'app',
        'server_id': os.environ.get('CLASSROOM_SERVER_ID', 'general-01'),
        'event_id': str(uuid4()),
        'request_id': str(uuid4()),
        'occurred_at': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
        'event_type': 'http_request',
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
    }
    event.update(getattr(g, 'auth_event', {}))
    event.update(getattr(g, 'classroom_event', {}))
    log_line = json.dumps(event, ensure_ascii=False)
    print(log_line, flush=True)
    log_path = os.environ.get('REQUEST_LOG_PATH')
    if log_path:
        try:
            with LOG_LOCK, open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(log_line + '\n')
        except OSError:
            current_app.logger.warning('실습용 JSONL 파일에 요청 기록을 쓰지 못했습니다.')
    if request.path.startswith('/internal/'):
        return response
    try:
        result = requests.post(
            MONITOR_URL,
            json=event,
            headers={'X-Event-Token': EVENT_TOKEN},
            timeout=(3, 10),
        )
        result.raise_for_status()
    except requests.RequestException:
        current_app.logger.warning(
            '감시 서비스에 요청 기록을 보내지 못했습니다. '
            '감시 /health 응답과 연결 설정을 확인한 뒤 다시 시도해 주세요.'
        )
    return response
