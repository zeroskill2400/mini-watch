from collections import deque
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import logging
import os
from threading import Lock, Thread
import time
from uuid import uuid4

import requests

from ai_client import AIError, ai_status, analyze_case
from correlation_rules import correlation_status
from detection_rules import normalize_auth_event, parse_time
from investigation_service import read_investigation, read_records, SERVER_ID, TARGET_PATH
from playbook import SoarError, action_step, begin_step, create_run, current_playbook, ensure_run, finish_step, require_step, skip_remaining, skip_step, step_record
import legacy_rules as soar_rules
from soar_store import connect_state, list_requests, read_request, save_request as store_request


ACTION_URL = 'http://general-api:5000/internal/notice-action'
POLICY_URL = 'http://general-api:5000/internal/notice-policy'
OPERATOR = 'class-operator'
PROCESS_LOCK = Lock()
WORKER_STARTED = False


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


@contextmanager
def transaction():
    connection = connect_state()
    try:
        connection.execute('BEGIN IMMEDIATE')
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def require_operator(operator):
    if operator != OPERATOR:
        raise SoarError('수업 감시 운영자만 대응 요청을 처리할 수 있습니다.', 403)


def required_request(connection, identifier):
    record = read_request(connection, identifier)
    if record is None:
        raise SoarError('대응 요청을 찾지 못했습니다.', 404)
    return ensure_run(record)


def save_request(connection, record):
    store_request(connection, ensure_run(record))


def history(record, event_type, operator, message):
    record['updated_at'] = now()
    record['history'].append({'at': record['updated_at'], 'type': event_type, 'operator': operator, 'message': message})


def rules():
    return {
        'request_min_failures': soar_rules.REQUEST_MIN_FAILURES,
        'notification_prompt': soar_rules.NOTIFICATION_PROMPT,
        'rejection_message': soar_rules.REJECTION_MESSAGE,
        'execute_approved': soar_rules.EXECUTE_APPROVED,
    }


def qualifying_failures(case, observation):
    if not observation:
        return []
    start = parse_time(observation['started_at'])
    end = parse_time(case['auth_success']['occurred_at'])
    events = {}
    for raw in read_records('app.jsonl'):
        try:
            event = normalize_auth_event(raw)
        except (ValueError, TypeError, OverflowError):
            continue
        if event and event['event_type'] == 'auth_failure' and event['attempted_username'] == case['username'] and start <= parse_time(event['occurred_at']) <= end:
            events.setdefault(event['event_id'], event)
    best = []
    window = deque()
    for event in sorted(events.values(), key=lambda item: (parse_time(item['occurred_at']), item['event_id'])):
        event_time = parse_time(event['occurred_at'])
        while window and (event_time - parse_time(window[0]['occurred_at'])).total_seconds() > 60:
            window.popleft()
        window.append(event)
        if len(window) > len(best):
            best = list(window)
    return best


def candidates(state, records):
    by_case = {record['case_id']: record['id'] for record in records}
    threshold = soar_rules.REQUEST_MIN_FAILURES
    valid_threshold = type(threshold) is int and 1 <= threshold <= 100
    playbook = current_playbook()
    selected = []
    for case in state['cases']:
        evidence = qualifying_failures(case, state['observation'])
        matched = state['correlation'].get('require_same_hash') is True and case.get('hash_matches') is True
        eligible = playbook['valid'] and valid_threshold and matched and len(evidence) >= threshold
        reason = '대응 요청 대상입니다. 공격 확정은 아니며 아직 조치하지 않습니다.' if eligible else '정상 로그인 전 60초 구간의 실패 수가 요청 기준에 못 미칩니다.'
        if not matched:
            reason = '서버·파일·해시가 일치한 실제 사건만 요청할 수 있습니다.'
        if not valid_threshold:
            reason = 'REQUEST_MIN_FAILURES는 1~100 사이의 정수여야 합니다.'
        if not playbook['valid']:
            reason = playbook['error']
        selected.append({'case_id': case['id'], 'case': case, 'evidence': evidence, 'failure_count': len(evidence), 'eligible': eligible, 'reason': reason, 'request_id': by_case.get(case['id'])})
    return selected


def read_soar():
    state = read_investigation()
    records = [ensure_run(record) for record in list_requests()]
    return {'rules': rules(), 'playbook': current_playbook(), 'ai': ai_status(), 'policy': state['policy'], 'observation': state['observation'], 'candidates': candidates(state, records), 'requests': records}


def create_request(case_id, operator):
    require_operator(operator)
    playbook = current_playbook()
    state = read_investigation()
    selected = next((item for item in candidates(state, list_requests()) if item['case_id'] == case_id), None)
    with transaction() as connection:
        previous = connection.execute('SELECT id FROM response_requests WHERE case_id=?', (case_id,)).fetchone()
        if previous:
            return required_request(connection, previous['id'])
        if not playbook['valid']:
            raise SoarError(playbook['error'])
        if selected is None:
            raise SoarError('현재 관찰의 실제 사건을 먼저 선택해 주세요.', 404)
        if not selected['eligible']:
            raise SoarError(selected['reason'])
        snapshot = deepcopy(selected['case'])
        snapshot['evidence'] = list({event['event_id']: event for event in snapshot['evidence'] + selected['evidence']}.values())
        record = {
            'id': str(uuid4()), 'case_id': case_id, 'state': 'awaiting_notification',
            'created_at': now(), 'updated_at': now(), 'created_by': operator,
            'case_snapshot': snapshot, 'failure_count': selected['failure_count'],
            'failure_evidence': selected['evidence'], 'request_min_failures': soar_rules.REQUEST_MIN_FAILURES,
            'notification': None, 'notification_history': [], 'approval': None,
            'restriction': None, 'verification': None, 'recovery': None,
            'recovery_approval': None, 'recovery_verification': None,
            'history': [], 'last_error': None,
        }
        history(record, 'created', operator, '사건 근거를 고정하여 대응 요청을 저장했습니다. 공지 저장은 아직 제한하지 않습니다.')
        create_run(record, playbook)
        save_request(connection, record)
        return record


def notify_request(identifier, operator):
    require_operator(operator)
    prompt = soar_rules.NOTIFICATION_PROMPT
    with transaction() as connection:
        record = required_request(connection, identifier)
        if record['state'] not in {'awaiting_notification', 'awaiting_approval'}:
            raise SoarError('승인 전 요청에서만 AI 알림을 만들 수 있습니다.')
        begin_step(record, 'ai_notify', operator, '실제 AI 알림 요청을 시작합니다.', repeat=True)
        step_record(record, 'ai_notify')['attempts'][-1]['input'] = {'notification_prompt': prompt}
        record['state'] = 'notifying'
        record['last_error'] = None
        history(record, 'notification_requested', operator, '실제 AI API에 담당자 알림 요약을 요청합니다. 조치는 실행하지 않습니다.')
        save_request(connection, record)
    try:
        analysis = analyze_case(record['case_snapshot'], {'require_same_hash': True, 'identity_note': correlation_status()['identity_note']}, prompt)
    except AIError as error:
        with transaction() as connection:
            record = required_request(connection, identifier)
            record['state'] = 'awaiting_approval' if record['notification'] else 'awaiting_notification'
            record['last_error'] = str(error)
            finish_step(record, 'ai_notify', 'failed', str(error), keep_success=bool(record['notification']))
            history(record, 'notification_failed', operator, str(error))
            save_request(connection, record)
        raise SoarError(str(error), error.status) from error
    with transaction() as connection:
        record = required_request(connection, identifier)
        notification = {'id': str(uuid4()), 'created_at': now(), **analysis}
        record['notification'] = notification
        record['notification_history'].append(notification)
        record['state'] = 'awaiting_approval'
        record['last_error'] = None
        finish_step(record, 'ai_notify', 'succeeded', '실제 AI 응답과 입력 근거를 저장했습니다.', analysis['result']['evidence_ids'])
        history(record, 'notified', operator, '실제 AI 응답과 입력 근거를 알림함에 저장했습니다. 사람이 확인하고 승인하거나 거절합니다.')
        save_request(connection, record)
        return record


def decide_request(identifier, decision, operator):
    require_operator(operator)
    with transaction() as connection:
        record = required_request(connection, identifier)
        if decision == 'cancel':
            if record['state'] != 'approved':
                raise SoarError('아직 실행되지 않은 승인 대기 요청만 취소할 수 있습니다.')
            record['state'] = 'cancelled'
            skip_remaining(record, '사람이 실행 전에 승인을 취소하여 남은 단계를 실행하지 않습니다.')
            history(record, 'cancelled', operator, '실행 전 승인을 취소했습니다. 조치하지 않습니다.')
        else:
            if record['state'] != 'awaiting_approval' or not record['notification']:
                raise SoarError('실제 AI 알림을 확인한 승인 대기 요청에서 판단해 주세요.')
            begin_step(record, 'human_approval', operator, '사람의 승인 또는 거절을 기록합니다.')
            if decision == 'reject':
                record['state'] = 'rejected'
                finish_step(record, 'human_approval', 'rejected', soar_rules.REJECTION_MESSAGE)
                skip_remaining(record, '사람이 거절하여 남은 단계를 실행하지 않습니다.')
                history(record, 'rejected', operator, soar_rules.REJECTION_MESSAGE)
            elif decision == 'approve':
                record['approval'] = {'operator': operator, 'at': now()}
                record['state'] = 'approved'
                finish_step(record, 'human_approval', 'succeeded', '사람이 이 실행에 고정된 액션을 승인했습니다.')
                history(record, 'approved', operator, '사람이 플레이북에 고정된 액션을 승인했습니다. 실행 연결 설정에 따라 자동으로 처리합니다.')
            else:
                raise SoarError('허용되지 않은 판단입니다.', 400)
        record['last_error'] = None
        save_request(connection, record)
    if decision == 'approve':
        process_request(identifier)
    return get_request(identifier)


def get_request(identifier):
    connection = connect_state()
    try:
        return required_request(connection, identifier)
    finally:
        connection.close()


def action_request(record, recovery):
    operation_id = record['id'] + (':restore' if recovery else ':restrict')
    token = os.environ.get('EVENT_TOKEN', '')
    if not token:
        raise SoarError('내부 조치 연결 설정이 없습니다.', 503)
    payload = {'blocked': not recovery, 'operator': OPERATOR, 'operation_id': operation_id, 'request_id': record['id']}
    try:
        response = requests.post(ACTION_URL, headers={'X-Event-Token': token}, json=payload, timeout=(3, 10), allow_redirects=False)
        if response.status_code != 200:
            raise SoarError('일반 서비스가 조치를 완료하지 못했습니다. 실제 상태를 확인한 뒤 다시 확인해 주세요.', 502)
        result = response.json()
        if not isinstance(result, dict) or result.get('operation_id') != operation_id or result.get('request_id') != record['id'] or result.get('blocked') is not (not recovery) or result.get('server_id') != SERVER_ID or result.get('target_path') != TARGET_PATH or not result.get('event_id'):
            raise SoarError('조치 응답의 대상이나 실행 번호가 맞지 않습니다.', 502)
        return result
    except (requests.RequestException, ValueError) as error:
        raise SoarError('조치 응답을 확인하지 못했습니다. 완료로 처리하지 않습니다. 같은 실행 번호로 다시 확인할 수 있습니다.', 502) from error


def current_action_policy():
    try:
        response = requests.get(POLICY_URL, headers={'X-Event-Token': os.environ.get('EVENT_TOKEN', '')}, timeout=(3, 10), allow_redirects=False)
        if response.status_code != 200:
            raise SoarError('현재 정책을 확인하지 못했습니다. 결과를 완료로 바꾸지 않습니다.', 502)
        policy = response.json()
        if not isinstance(policy, dict) or type(policy.get('blocked')) is not bool or policy.get('server_id') != SERVER_ID or policy.get('target_path') != TARGET_PATH:
            raise SoarError('현재 정책의 대상과 상태를 확인하지 못했습니다.', 502)
        return policy
    except (requests.RequestException, ValueError) as error:
        raise SoarError('현재 정책에 연결하지 못했습니다. 완료로 처리하지 않습니다.', 502) from error


def process_request(identifier):
    if not PROCESS_LOCK.acquire(blocking=False):
        return
    try:
        with transaction() as connection:
            record = required_request(connection, identifier)
            state = record['state']
            recovery = state in {'recovery_approved', 'recovering'}
            if state not in {'approved', 'executing', 'recovery_approved', 'recovering'}:
                return
            step_id = 'restore_notice' if recovery else action_step(record)
            require_step(record, step_id)
            if not recovery and soar_rules.EXECUTE_APPROVED is not True:
                return
            approval = record['recovery_approval'] if recovery else record['approval']
            target = record['case_snapshot']
            if not approval or approval.get('operator') != OPERATOR or not record['notification'] or target.get('server_id') != SERVER_ID or target.get('target_path') != TARGET_PATH or target.get('hash_matches') is not True:
                raise SoarError('사람 승인과 허용된 대상 확인 없이 실행할 수 없습니다.', 403)
            begin_step(record, step_id, OPERATOR, '고정된 플레이북의 다음 자동 액션을 실행합니다.', resume=True)
            if step_id != 'record_only':
                step_record(record, step_id)['attempts'][-1]['operation_id'] = identifier + (':restore' if recovery else ':restrict')
            record['state'] = 'recovering' if recovery else 'executing'
            record['last_error'] = None
            if state in {'approved', 'recovery_approved'}:
                history(record, record['state'], OPERATOR, '승인된 플레이북 액션을 자동 처리합니다.')
            if step_id == 'record_only':
                finish_step(record, step_id, 'succeeded', '정의가 record_only이므로 기록만 남겼습니다. 정책 API를 호출하지 않았습니다.')
                skip_remaining(record, '기록 전용 액션이므로 제한403 확인과 저장 허용 복구 단계는 실행하지 않습니다.')
                record['state'] = 'completed_no_action'
                history(record, 'completed_no_action', OPERATOR, '플레이북에 정의한 기록 전용 액션으로 종료했습니다. 공지 저장 정책은 바꾸지 않았습니다.')
                save_request(connection, record)
                return
            save_request(connection, record)
        try:
            result = action_request(record, recovery)
        except SoarError as error:
            with transaction() as connection:
                record = required_request(connection, identifier)
                record['state'] = 'recovery_error' if recovery else 'execution_error'
                record['last_error'] = str(error)
                finish_step(record, step_id, 'failed', str(error))
                history(record, record['state'], OPERATOR, str(error))
                save_request(connection, record)
            return
        with transaction() as connection:
            record = required_request(connection, identifier)
            record['recovery' if recovery else 'restriction'] = result
            record['state'] = 'restored' if recovery else 'restricted'
            finish_step(record, step_id, 'succeeded', '일반 서비스의 실제 조치 영수증을 확인했습니다.', [result['event_id']], result['operation_id'])
            history(record, record['state'], OPERATOR, '저장 허용을 복구했습니다. 일반 사이트에서 다른 내용으로 실제 저장200을 확인해 주세요.' if recovery else '공지 저장 제한을 적용했습니다. 일반 사이트에서 실제 저장을 시도해 정책403을 확인해 주세요.')
            save_request(connection, record)
    finally:
        PROCESS_LOCK.release()


def verification_evidence(record):
    identifier = record['id']
    recovery = record['state'] == 'restored'
    action = record['recovery'] if recovery else record['restriction']
    policy = current_action_policy()
    if policy['blocked'] is not (not recovery) or policy.get('operation_id') != action['operation_id']:
        raise SoarError('현재 정책이 이 요청의 조치와 다릅니다. 상태를 확인한 뒤 다시 진행해 주세요.')
    event_type = 'file_write' if recovery else 'notice_write_denied'
    expected_status = 200 if recovery else 403
    evidence = []
    for raw in read_records('app.jsonl'):
        if raw.get('event_type') != event_type or raw.get('status_code') != expected_status or raw.get('method') != 'POST' or raw.get('path') not in {'/notice', '/api/notice'}:
            continue
        if raw.get('server_id') != SERVER_ID or raw.get('target_path') != TARGET_PATH or raw.get('policy_operation_id') != action['operation_id'] or raw.get('policy_request_id') != identifier:
            continue
        if parse_time(raw['occurred_at']) < parse_time(action['updated_at']):
            continue
        if not recovery and (raw.get('error_code') != 'notice_write_blocked' or raw.get('sha256') != action['sha256']):
            continue
        if recovery and raw.get('sha256') == raw.get('previous_sha256'):
            continue
        evidence.append(raw)
    if not evidence:
        raise SoarError('이 조치에 연결된 실제 저장 결과가 아직 없습니다. 일반 사이트에서 다른 공지 내용을 저장한 뒤 다시 확인해 주세요. 로그인 오류나 입력 확인403은 조치 근거가 아닙니다.')
    return max(evidence, key=lambda item: parse_time(item['occurred_at'])), expected_status, action


def verify_request(identifier, operator):
    require_operator(operator)
    with transaction() as connection:
        record = required_request(connection, identifier)
        if record['state'] not in {'restricted', 'restored'}:
            raise SoarError('제한 또는 복구 조치 뒤 일반 사이트에서 실제 저장을 시도한 다음 확인해 주세요.')
        recovery = record['state'] == 'restored'
        step_id = 'verify_restored' if recovery else 'verify_denied'
        attempt_id = begin_step(record, step_id, operator, '실제 원본에서 이 조치의 저장 결과를 확인합니다.')
        save_request(connection, record)
    try:
        raw, expected_status, action = verification_evidence(record)
    except SoarError as error:
        with transaction() as connection:
            current = required_request(connection, identifier)
            selected = step_record(current, step_id)
            if current['state'] == record['state'] and selected['attempts'][-1]['id'] == attempt_id and selected['status'] == 'running':
                finish_step(current, step_id, 'failed', str(error))
                history(current, 'verification_failed', operator, str(error))
                save_request(connection, current)
        raise
    with transaction() as connection:
        current = required_request(connection, identifier)
        if current['state'] != record['state'] or step_record(current, step_id)['attempts'][-1]['id'] != attempt_id:
            raise SoarError('요청 상태가 바뀌었습니다. 다시 조회해 주세요.')
        current['recovery_verification' if recovery else 'verification'] = {'event_id': raw['event_id'], 'occurred_at': raw['occurred_at'], 'status_code': expected_status, 'expected_outcome': 'save_succeeded' if recovery else 'policy_denied', 'raw': raw, 'policy_operation_id': action['operation_id']}
        current['state'] = 'completed' if recovery else 'verified'
        finish_step(current, step_id, 'succeeded', '이 조치에 연결된 실제 저장 결과 원본을 확인했습니다.', [raw['event_id']], action['operation_id'])
        history(current, current['state'], operator, '실제 공지 저장200과 새 파일 내용을 확인했습니다. 저장 허용 복구이며 공지 원문 복원은 아닙니다.' if recovery else '실제 정책 거절403과 제한 당시 파일 해시 보존을 확인했습니다.')
        save_request(connection, current)
        return current


def recover_request(identifier, operator):
    require_operator(operator)
    policy = current_action_policy()
    with transaction() as connection:
        record = required_request(connection, identifier)
        if record['state'] == 'execution_error' and policy['blocked'] and policy.get('owner_request_id') == identifier:
            receipt = policy.get('receipts', {}).get(identifier + ':restrict')
            if receipt and receipt.get('blocked') is True:
                if step_record(record, 'restrict_notice')['status'] != 'succeeded':
                    begin_step(record, 'restrict_notice', operator, '응답 유실 뒤 실제 조치 영수증을 조회합니다.', resume=True)
                    finish_step(record, 'restrict_notice', 'succeeded', '실제 적용 영수증으로 제한 결과를 재확인했습니다.', [receipt['event_id']], receipt['operation_id'])
                record['restriction'] = receipt
                record['state'] = 'restricted'
                history(record, 'restriction_reconciled', operator, '응답 유실 뒤 실제 적용 영수증을 확인했습니다. 중복 실행하지 않습니다.')
        if record['state'] not in {'restricted', 'verified'}:
            raise SoarError('이 요청이 적용한 공지 제한을 먼저 확인해 주세요.')
        if policy['blocked'] is not True or policy.get('owner_request_id') != identifier:
            raise SoarError('이 요청이 소유한 현재 제한만 복구할 수 있습니다.')
        if step_record(record, 'verify_denied')['status'] != 'succeeded':
            skip_step(record, 'verify_denied', '사람이 정책403 확인보다 안전 복구를 먼저 승인했습니다.403을 확인한 것으로 표시하지 않습니다.')
        begin_step(record, 'human_recovery_approval', operator, '사람의 저장 허용 복구 승인을 기록합니다.')
        record['recovery_approval'] = {'operator': operator, 'at': now()}
        record['state'] = 'recovery_approved'
        finish_step(record, 'human_recovery_approval', 'succeeded', '사람이 저장 허용 복구를 승인했습니다.')
        history(record, 'recovery_approved', operator, '사람이 저장 허용 복구를 승인했습니다. 실행 연결 설정과 관계없이 안전하게 해제합니다.')
        save_request(connection, record)
    process_request(identifier)
    return get_request(identifier)


def retry_request(identifier, operator):
    require_operator(operator)
    with transaction() as connection:
        record = required_request(connection, identifier)
        if record['state'] not in {'execution_error', 'recovery_error'}:
            raise SoarError('응답을 확인하지 못한 조치에서만 다시 확인할 수 있습니다.')
        if record['state'] == 'execution_error' and soar_rules.EXECUTE_APPROVED is not True:
            raise SoarError('제한 실행 연결이 꺼져 있습니다. 이미 제한이 적용됐다면 저장 허용 복구를 승인할 수 있습니다. 새 제한 실행은 True로 연결한 뒤 다시 확인해 주세요.')
        record['state'] = 'recovery_approved' if record['state'] == 'recovery_error' else 'approved'
        history(record, 'retry_requested', operator, '같은 실행 번호로 다시 확인합니다. 이미 적용된 조치는 중복 적용하지 않습니다.')
        save_request(connection, record)
    process_request(identifier)
    return get_request(identifier)


def worker_tick():
    for record in list_requests():
        if record['state'] in {'approved', 'executing', 'recovery_approved', 'recovering'}:
            process_request(record['id'])


def worker_loop():
    while True:
        try:
            worker_tick()
        except Exception:
            logging.exception('대응 자동 처리 확인에 실패했습니다. 완료 상태로 바꾸지 않았습니다.')
        time.sleep(2)


def start_worker():
    global WORKER_STARTED
    if WORKER_STARTED or os.environ.get('SOAR_DISABLE_WORKER') == '1':
        return
    with transaction() as connection:
        for record in list_requests():
            ensure_run(record)
            if record['state'] == 'executing' and soar_rules.EXECUTE_APPROVED is not True:
                record['state'] = 'execution_error'
                record['last_error'] = '재시작 전에 조치 응답 저장을 마치지 못했습니다. 현재 제한을 확인하거나 저장 허용 복구를 승인해 주세요.'
                finish_step(record, action_step(record), 'failed', record['last_error'])
                history(record, 'execution_interrupted', OPERATOR, record['last_error'])
                save_request(connection, record)
            if record['state'] == 'notifying':
                record['state'] = 'awaiting_approval' if record['notification'] else 'awaiting_notification'
                record['last_error'] = '재시작 전에 AI 응답 저장을 마치지 못했습니다. 알림을 다시 요청해 주세요.'
                finish_step(record, 'ai_notify', 'failed', record['last_error'], keep_success=bool(record['notification']))
                history(record, 'notification_interrupted', OPERATOR, record['last_error'])
                save_request(connection, record)
            if record['state'] in {'restricted', 'restored'}:
                step_id = 'verify_restored' if record['state'] == 'restored' else 'verify_denied'
                if step_record(record, step_id)['status'] == 'running':
                    finish_step(record, step_id, 'failed', '재시작 전에 실제 근거 조회 결과를 저장하지 못했습니다. 저장 결과 확인을 다시 눌러 주세요.')
                    history(record, 'verification_interrupted', OPERATOR, '재시작으로 중단된 근거 확인을 완료로 처리하지 않았습니다.')
                    save_request(connection, record)
    WORKER_STARTED = True
    Thread(target=worker_loop, name='prepared-response-worker', daemon=True).start()
