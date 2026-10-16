from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

import legacy_rules as soar_rules


STANDARD_STEPS = ['ai_notify', 'human_approval', 'restrict_notice', 'verify_denied', 'human_recovery_approval', 'restore_notice', 'verify_restored']
FINISHED = {'succeeded', 'rejected', 'skipped'}
TERMINAL_STATES = {'completed', 'completed_no_action', 'rejected', 'cancelled'}


class SoarError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def validate_steps(steps):
    if steps == []:
        return 'PLAYBOOK_STEPS가 비어 있습니다. 교안의 일곱 단계 정의를 먼저 작성해 주세요.'
    if not isinstance(steps, list) or len(steps) != len(STANDARD_STEPS) or any(not isinstance(step, str) for step in steps):
        return 'PLAYBOOK_STEPS에는 허용된 일곱 단계 ID를 순서대로 작성해 주세요.'
    expected = list(STANDARD_STEPS)
    if steps[2] == 'record_only':
        expected[2] = 'record_only'
    if steps != expected:
        return '승인과 검증 단계의 순서를 유지해 주세요. 세 번째 액션만 restrict_notice 또는 record_only로 선택할 수 있습니다.'
    return None


def definition(steps, threshold, legacy=False):
    result = {
        'id': 'notice-response', 'name': '반복 실패 뒤 공지 변경 대응',
        'version': 1, 'trigger': 'manual', 'steps': deepcopy(steps),
        'request_min_failures': threshold, 'legacy': legacy,
    }
    result['definition_hash'] = sha256(json.dumps(result, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:16]
    return result


def current_playbook():
    configured = getattr(soar_rules, 'PLAYBOOK_STEPS', [])
    error = validate_steps(configured)
    steps = configured if isinstance(configured, list) and all(isinstance(step, str) for step in configured) else []
    result = definition(steps, soar_rules.REQUEST_MIN_FAILURES)
    return {**result, 'valid': error is None, 'error': error}


def create_run(record, selected_definition):
    if not selected_definition['valid']:
        raise SoarError(selected_definition['error'])
    record['playbook_snapshot'] = {key: deepcopy(value) for key, value in selected_definition.items() if key not in {'valid', 'error'}}
    record['step_runs'] = [{'step_id': step, 'status': 'pending', 'attempts': [], 'message': '', 'legacy': False} for step in selected_definition['steps']]
    return refresh_run(record)


def ensure_run(record):
    if 'playbook_snapshot' not in record:
        record['playbook_snapshot'] = definition(STANDARD_STEPS, record.get('request_min_failures', 3), legacy=True)
        evidence_fields = ['notification', 'approval', 'restriction', 'verification', 'recovery_approval', 'recovery', 'recovery_verification']
        record['step_runs'] = [{'step_id': step, 'status': 'succeeded' if record.get(field) else 'pending', 'attempts': [], 'message': '이전 고정 흐름의 저장된 근거로 판별했습니다. 과거 단계별 시도 이력은 없습니다.', 'legacy': True} for step, field in zip(STANDARD_STEPS, evidence_fields)]
        if record.get('recovery_approval') and not record.get('verification'):
            step_record(record, 'verify_denied')['status'] = 'skipped'
        if record['state'] == 'rejected':
            step_record(record, 'human_approval')['status'] = 'rejected'
        if record['state'] in {'rejected', 'cancelled'}:
            skip_remaining(record, '이전 기록에서 거절 또는 실행 전 취소됐습니다.')
        if record['state'] in {'execution_error', 'recovery_error'}:
            step_record(record, 'restore_notice' if record['state'] == 'recovery_error' else 'restrict_notice')['status'] = 'failed'
    error = validate_steps(record['playbook_snapshot'].get('steps'))
    if error or [step['step_id'] for step in record.get('step_runs', [])] != record['playbook_snapshot']['steps']:
        raise SoarError('저장된 플레이북 단계와 실행 기록이 맞지 않습니다. 임의 조치는 실행하지 않습니다.')
    return refresh_run(record)


def step_record(record, identifier):
    selected = next((step for step in record['step_runs'] if step['step_id'] == identifier), None)
    if selected is None:
        raise SoarError('이 실행에 고정된 플레이북에 해당 단계가 없습니다.')
    return selected


def action_step(record):
    return record['playbook_snapshot']['steps'][2]


def refresh_run(record):
    upcoming = None if record['state'] in TERMINAL_STATES else next((step for step in record['step_runs'] if step['status'] not in FINISHED), None)
    record['next_step'] = upcoming['step_id'] if upcoming else None
    if upcoming and upcoming['status'] == 'pending':
        upcoming['status'] = 'waiting'
    reasons = {
        'ai_notify': '사람이 AI 요약 알림을 요청하면 플레이북 첫 단계를 실행합니다.',
        'human_approval': '실제 AI 알림을 읽은 사람의 승인 또는 거절을 기다립니다.',
        'restrict_notice': '사람이 승인한 공지 저장 제한을 준비된 실행기가 처리합니다.',
        'record_only': '사람이 승인한 기록 전용 액션을 준비된 실행기가 처리합니다.',
        'verify_denied': '일반 사이트에서 실제 저장을 시도한 뒤 저장 결과 확인을 눌러 정책403을 연결합니다.',
        'human_recovery_approval': '사람의 저장 허용 복구 승인을 기다립니다.',
        'restore_notice': '사람이 승인한 저장 허용 복구를 준비된 실행기가 처리합니다.',
        'verify_restored': '일반 사이트에서 다른 내용으로 저장한 뒤 저장 결과 확인을 눌러 실제200을 연결합니다.',
    }
    reason = reasons.get(record['next_step'], '')
    if upcoming and upcoming['status'] == 'running':
        reason = '현재 단계의 실제 처리 결과를 기다립니다.'
    elif upcoming and upcoming['status'] == 'failed':
        reason = upcoming['message'] or '현재 단계가 완료되지 않았습니다. 오류와 실제 상태를 확인해 주세요.'
    elif record['state'] == 'approved' and soar_rules.EXECUTE_APPROVED is not True:
        reason = '승인은 저장됐지만 EXECUTE_APPROVED=False입니다. 실행 연결 후 이 실행에 고정된 액션으로 진행합니다.'
    record['waiting_reason'] = reason
    return record


def require_step(record, identifier):
    refresh_run(record)
    if record['next_step'] != identifier:
        raise SoarError('플레이북의 다음 단계가 아닙니다. 현재 단계와 저장된 근거를 확인해 주세요.')


def begin_step(record, identifier, operator, message, repeat=False, resume=False):
    selected = step_record(record, identifier)
    if not (repeat and identifier == 'ai_notify' and record['state'] == 'awaiting_approval'):
        require_step(record, identifier)
    if selected['status'] == 'running':
        if not resume:
            raise SoarError('이 플레이북 단계는 이미 처리 중입니다.')
        finish_step(record, identifier, 'failed', '이전 처리의 응답 저장을 확인하지 못했습니다. 같은 실행 번호로 다시 확인합니다.')
    attempt = {'id': str(uuid4()), 'started_at': timestamp(), 'finished_at': None, 'status': 'running', 'operator': operator, 'message': message, 'evidence_ids': [], 'operation_id': None}
    selected['attempts'].append(attempt)
    selected['status'] = 'running'
    selected['message'] = message
    refresh_run(record)
    return attempt['id']


def finish_step(record, identifier, status, message, evidence_ids=None, operation_id=None, keep_success=False):
    selected = step_record(record, identifier)
    if selected['attempts'] and selected['attempts'][-1]['status'] == 'running':
        attempt = selected['attempts'][-1]
        attempt.update({'finished_at': timestamp(), 'status': status, 'message': message, 'evidence_ids': list(evidence_ids or []), 'operation_id': operation_id or attempt['operation_id']})
    selected['status'] = 'succeeded' if keep_success else status
    selected['message'] = message
    refresh_run(record)


def skip_step(record, identifier, message):
    finish_step(record, identifier, 'skipped', message)


def skip_remaining(record, message):
    for selected in record['step_runs']:
        if selected['status'] not in FINISHED:
            skip_step(record, selected['step_id'], message)
    refresh_run(record)
