import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from uuid import uuid4


TARGET_PATH = '/classroom-data/notice.txt'
STATE_LOCK = RLock()


class NoticeError(Exception):
    def __init__(self, message, status, event=None):
        super().__init__(message)
        self.status = status
        self.event = event


def data_directory():
    return Path(os.environ.get('CLASSROOM_DATA_DIR', '/classroom-data'))


def server_id():
    return os.environ.get('CLASSROOM_SERVER_ID', 'general-01')


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def atomic_write(path, content):
    temporary_path = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix='.notice-', delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def prepare_notice():
    with STATE_LOCK:
        directory = data_directory()
        directory.mkdir(parents=True, exist_ok=True)
        notice_path = directory / 'notice.txt'
        if not notice_path.exists():
            atomic_write(notice_path, '수업 공지입니다.\n내용을 바꾼 뒤 공지 저장을 눌러 보세요.\n'.encode('utf-8'))
        policy_path = directory / 'notice-policy.json'
        if not policy_path.exists():
            policy = {'blocked': False, 'operator': None, 'updated_at': None, 'event_id': None}
            atomic_write(policy_path, json.dumps(policy, ensure_ascii=False).encode('utf-8'))


def read_policy():
    with STATE_LOCK:
        policy = json.loads((data_directory() / 'notice-policy.json').read_text(encoding='utf-8'))
        if not isinstance(policy, dict) or type(policy.get('blocked')) is not bool:
            raise ValueError('공지 정책 파일을 읽을 수 없습니다.')
        return {**policy, 'server_id': server_id(), 'target_path': TARGET_PATH}


def read_notice():
    with STATE_LOCK:
        path = data_directory() / 'notice.txt'
        content = path.read_bytes()
        return {
            'content': content.decode('utf-8'),
            'sha256': hashlib.sha256(content).hexdigest(),
            'modified_at': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            'server_id': server_id(),
            'target_path': TARGET_PATH,
            'policy': read_policy(),
        }


def read_notice_snapshot(digest):
    if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
        raise NoticeError('공지 해시를 확인해 주세요.', 400)
    with STATE_LOCK:
        path = data_directory() / 'notice-snapshots' / (digest + '.txt')
        if not path.exists():
            raise NoticeError('이전 공지의 내용 스냅샷이 없습니다. 공지를 다른 내용으로 저장해 새 사건을 만들어 주세요.', 409)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise NoticeError('공지 스냅샷과 사건 해시가 다릅니다. 기존 자료는 변경하지 않았습니다.', 409)
        return {'content': content.decode('utf-8'), 'sha256': digest, 'server_id': server_id(), 'target_path': TARGET_PATH}


def operation_event(event_type):
    return {
        'event_id': str(uuid4()),
        'occurred_at': timestamp(),
        'event_type': event_type,
        'server_id': server_id(),
        'target_path': TARGET_PATH,
        'request_id': str(uuid4()),
    }


def write_notice(content, username, auth_event_id):
    if not isinstance(content, str) or not content.strip() or len(content) > 4000:
        raise NoticeError('공지 내용을 1~4000자로 입력해 주세요.', 400)
    if not isinstance(auth_event_id, str) or not auth_event_id:
        raise NoticeError('로그인 근거를 연결하려면 로그아웃한 뒤 다시 로그인해 주세요.', 409)
    with STATE_LOCK:
        policy = read_policy()
        if policy['blocked']:
            event = {
                **operation_event('notice_write_denied'),
                'error_code': 'notice_write_blocked',
                'authenticated_username': username,
                'auth_event_id': auth_event_id,
                'sha256': read_notice()['sha256'],
                'policy_operation_id': policy.get('operation_id'),
                'policy_request_id': policy.get('owner_request_id'),
            }
            raise NoticeError('감시 운영자가 공지 변경을 제한했습니다. 조회와 로그인은 계속 사용할 수 있습니다.', 403, event)
        previous = read_notice()
        if content == previous['content']:
            return {**previous, 'changed': False, 'event': None}
        snapshot_directory = data_directory() / 'notice-snapshots'
        snapshot_directory.mkdir(exist_ok=True)
        snapshot_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        snapshot_path = snapshot_directory / (snapshot_hash + '.txt')
        if not snapshot_path.exists():
            atomic_write(snapshot_path, content.encode('utf-8'))
        event = operation_event('file_write')
        atomic_write(data_directory() / 'notice.txt', content.encode('utf-8'))
        current = read_notice()
        event = {
            **event,
            'authenticated_username': username,
            'auth_event_id': auth_event_id,
            'previous_sha256': previous['sha256'],
            'sha256': current['sha256'],
            'notice_snapshot_sha256': snapshot_hash,
            'policy_operation_id': policy.get('operation_id'),
            'policy_request_id': policy.get('request_id'),
        }
        return {**current, 'changed': True, 'event': event}


def change_policy(blocked, operator):
    if type(blocked) is not bool or not isinstance(operator, str) or not operator.strip() or len(operator) > 80:
        raise NoticeError('blocked는 참/거짓, operator는 운영자 이름이어야 합니다.', 400)
    with STATE_LOCK:
        read_policy()
        event = {**operation_event('notice_policy_changed'), 'blocked': blocked, 'operator': operator.strip()}
        policy = {
            'blocked': blocked,
            'operator': operator.strip(),
            'updated_at': event['occurred_at'],
            'event_id': event['event_id'],
        }
        atomic_write(data_directory() / 'notice-policy.json', json.dumps(policy, ensure_ascii=False).encode('utf-8'))
        return read_policy(), event


def apply_approved_action(blocked, operator, operation_id, request_id, expected_sha256=None):
    if type(blocked) is not bool or not isinstance(operator, str) or operator not in {'class-operator', 'system'}:
        raise NoticeError('허용된 감시 운영자의 조치가 아닙니다.', 403)
    if any(not isinstance(value, str) or not 1 <= len(value) <= 100 for value in [operation_id, request_id]):
        raise NoticeError('조치와 요청 번호를 확인해 주세요.', 400)
    if operation_id != request_id + (':restrict' if blocked else ':restore'):
        raise NoticeError('요청에 연결된 고정 조치 번호만 사용할 수 있습니다.', 400)
    if operator == 'system' and (not blocked or not request_id.startswith('run-') or not isinstance(expected_sha256, str) or re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is None):
        raise NoticeError('자동 실행은 현재 공지 해시를 확인한 저장 제한만 허용합니다. 복구에는 사람의 승인이 필요합니다.', 403)
    with STATE_LOCK:
        previous = read_policy()
        receipts = previous.get('receipts', {})
        if operation_id in receipts:
            receipt = receipts[operation_id]
            if receipt['blocked'] != blocked or receipt['request_id'] != request_id:
                raise NoticeError('같은 조치 번호를 다른 작업에 사용할 수 없습니다.', 409)
            return {**receipt, 'replayed': True}, None
        if blocked and expected_sha256 is not None and expected_sha256 != read_notice()['sha256']:
            raise NoticeError('사건 이후 공지 내용이 바뀌었습니다. 현재 변경의 새 사건을 확인해 주세요.', 409)
        owner = previous.get('owner_request_id')
        if previous['blocked'] and owner != request_id:
            raise NoticeError('다른 대응 요청이 공지 저장을 제한 중입니다. 먼저 그 요청에서 복구해 주세요.', 409)
        if not blocked and owner != request_id:
            raise NoticeError('이 요청이 적용한 제한만 해제할 수 있습니다.', 409)
        event = {
            **operation_event('notice_policy_changed'),
            'blocked': blocked,
            'operator': operator,
            'operation_id': operation_id,
            'response_request_id': request_id,
            'sha256': read_notice()['sha256'],
        }
        policy = {
            'blocked': blocked,
            'operator': operator,
            'updated_at': event['occurred_at'],
            'event_id': event['event_id'],
            'operation_id': operation_id,
            'request_id': request_id,
            'owner_request_id': request_id if blocked else None,
            'server_id': server_id(),
            'target_path': TARGET_PATH,
            'sha256': event['sha256'],
        }
        receipts[operation_id] = policy
        atomic_write(data_directory() / 'notice-policy.json', json.dumps({**policy, 'receipts': receipts}, ensure_ascii=False).encode('utf-8'))
        return {**policy, 'replayed': False}, event
