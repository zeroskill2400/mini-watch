from copy import deepcopy
from hashlib import sha256
from uuid import uuid4

from ai_client import ai_status
from history_ai import checked_prompt, comparison_key, decide_with_ai, fallback, resolve_comparisons, validate_result
from request_history import build_history, content_hash
from soar_service import SoarError, now, require_operator
from url_playbook_store import read_run
import url_playbook_service as service


STEPS = [('history', 'build_history'), ('rule', 'decide_with_rule'), ('decide', 'decide'), ('plan', 'choose_actions'), ('execute', 'execute_actions'), ('record', 'save_result')]


def checked_decision(result, history):
    if not isinstance(result, dict) or result.get('decision') not in {'review', 'respond'} or not isinstance(result.get('reason'), str) or not 1 <= len(result['reason']) <= 800:
        raise SoarError('판단 함수는 decision(review/respond)과 reason(1~800자)을 반환해야 합니다.')
    if result.get('mode') == 'ai':
        fields = {key: result.get(key) for key in ['decision', 'risk_level', 'reason', 'evidence_ids', 'inferences', 'limitations']}
        try:
            validate_result(fields, history)
        except Exception:
            return fallback('insufficient', '실제 이력과 AI 판단 근거를 함께 검증하지 못했습니다.')
        decision = deepcopy(result)
    elif result.get('mode') == 'fallback':
        decision = deepcopy(result)
        decision['decision'] = 'review'
        decision['risk_level'] = 'unknown'
    elif set(result) == {'decision', 'reason'}:
        decision = {'mode': 'rule', 'status': 'succeeded', 'risk_level': None, **result, 'evidence_ids': list(history['failure_event_ids']) if result['decision'] == 'respond' else [history['trigger_event_id']], 'inferences': [], 'limitations': list(history['quality']['limitations'])}
    else:
        raise SoarError('규칙 함수는 decision과 reason만 반환해야 합니다. AI 응답은 준비된 decide_with_ai를 사용해 주세요.')
    if history['quality']['complete'] is not True:
        return fallback('insufficient', '원본 이력이 불완전해 자동 대응하지 않습니다. 누락 및 시간창 안내를 확인해 주세요.')
    return decision


def response_allowed(record):
    decision = record.get('decision') or {}
    if record.get('history_snapshot', {}).get('quality', {}).get('complete') is not True or decision.get('status') != 'succeeded':
        return False
    if record.get('approval'):
        return True
    if decision.get('decision') != 'respond':
        return False
    return decision.get('mode') == 'rule' or (decision.get('mode') == 'ai' and decision.get('risk_level') == 'high' and bool(decision.get('evidence_ids')))


def create_history_run(case_id, execution_key, operator, student_rules, selected_definition, selected=None, trigger=None):
    if selected is None:
        overview = service.read_overview(selected_definition)
        selected = next((item for item in overview['candidates'] if item['case_id'] == case_id), None)
    if selected is None or not selected['eligible']:
        raise SoarError(selected['reason'] if selected else '실제 공지 변경 사건을 확인하지 못했습니다.')
    with service.LOCK:
        previous = read_run(execution_key=execution_key)
        if previous:
            if previous['case_id'] != case_id:
                raise SoarError('같은 실행 키를 다른 사건에 사용할 수 없습니다.')
            return previous
        record = {
            'id': 'run-' + uuid4().hex, 'flow': 'history-v1', 'execution_key': execution_key, 'case_id': case_id,
            'case_snapshot': deepcopy(selected['case']), 'definition': deepcopy(selected_definition),
            'state': 'running', 'created_at': now(), 'updated_at': now(), 'created_by': operator,
            'trigger': trigger or {'type': 'manual_compatibility', 'actor': operator},
            'history_snapshot': None, 'rule_result': None, 'decision': None, 'comparisons': [], 'prompt': None,
            'url': None, 'score': None, 'lookup': {}, 'branch': None, 'effective_branch': None,
            'plan': [], 'respond_plan': [], 'message': '', 'respond_message': '',
            'steps': [{'id': identifier, 'function_name': function, 'input': None, 'output': None, 'status': 'pending', 'error': None} for identifier, function in STEPS],
            'actions': [], 'notification': None, 'ticket': None, 'summary': None,
            'restriction': None, 'verification': None, 'recovery': None, 'recovery_verification': None,
            'approval': None, 'recovery_approval': None, 'ai_summary': None, 'ai_history': [], 'ai_error': None, 'ai_running': False,
            'last_error': None, 'history': [], 'approve_allowed': False,
        }
        service.persist(record, {'type': 'started', 'operator': operator, 'message': '새 공지 저장과 센서 사건을 입력으로 실제 요청 이력 판단을 시작했습니다.'})
    stage = 'history'
    try:
        digest = selected['case']['write']['raw']['sha256']
        snapshot = service.internal_get('/notice-snapshots/' + digest)
        if snapshot.get('sha256') != digest or snapshot.get('server_id') != service.SERVER_ID or snapshot.get('target_path') != service.TARGET_PATH or not isinstance(snapshot.get('content'), str) or sha256(snapshot['content'].encode('utf-8')).hexdigest() != digest:
            raise SoarError('사건 원본과 공지 스냅샷이 일치하지 않습니다.')
        record['notice_snapshot'] = snapshot
        history = build_history(selected['case'])
        record['history_snapshot'] = history
        service.set_step(record, 'history', {'write_event_id': selected['case']['write']['event_id']}, history)
        stage = 'rule'
        record['rule_result'] = checked_decision(student_rules.decide_with_rule(deepcopy(history)), history)
        service.set_step(record, 'rule', {'history_hash': history['snapshot_hash'], 'login_failure_count': history['login_failure_count']}, record['rule_result'])
        stage = 'decide'
        record['prompt'] = checked_prompt(student_rules.make_prompt())
        service.set_step(record, 'decide', {'history_hash': history['snapshot_hash'], 'prompt': record['prompt']}, status='running')
        record['decision'] = checked_decision(student_rules.decide(deepcopy(history)), history)
        record['branch'] = record['decision']['decision']
        record['effective_branch'] = record['branch']
        service.set_step(record, 'decide', {'history_hash': history['snapshot_hash'], 'prompt': record['prompt']}, record['decision'])
        stage = 'plan'
        record['plan'] = service.checked_actions(student_rules.choose_actions(record['branch']), record['branch'])
        record['respond_plan'] = service.checked_actions(student_rules.choose_actions('respond'), 'respond')
        record['message'] = f"요청 {history['request_count']}건 · 로그인 실패 {history['login_failure_count']}건 · {record['branch']}: {record['decision']['reason']}"
        record['respond_message'] = '검토 후 대응 승인: ' + record['message']
        service.set_step(record, 'plan', {'branch': record['branch']}, {'actions': record['plan'], 'message': record['message'], 'approval_actions': record['respond_plan']})
        with service.LOCK:
            return service.execute_actions(record)
    except Exception as error:
        record['state'] = 'error'
        record['last_error'] = str(error) if isinstance(error, SoarError) else '학생 함수 또는 준비된 이력 처리에서 오류가 발생했습니다. 기존 실행과 복구는 보존합니다.'
        service.set_step(record, stage, next(item for item in record['steps'] if item['id'] == stage)['input'], status='failed', error=record['last_error'])
        return service.persist(record, {'type': 'failed', 'message': record['last_error']})


def compare_ai(identifier, operator):
    require_operator(operator)
    student_rules, selected_definition = service.load_rules()
    if selected_definition['flow'] != 'history-v1':
        raise SoarError('현재 이력 판단 함수가 필요합니다.')
    try:
        prompt = checked_prompt(student_rules.make_prompt())
    except Exception as error:
        raise SoarError('make_prompt의 1~1000자 반환 문장을 확인해 주세요.') from error
    with service.LOCK:
        record = service.required_run(identifier)
        if record.get('flow') != 'history-v1' or not record.get('history_snapshot') or record['state'] in {'running', 'recovering'}:
            raise SoarError('이력 수집과 현재 판단이 끝난 실행에서만 비교할 수 있습니다.')
        history = deepcopy(record['history_snapshot'])
        if resolve_comparisons(record):
            service.persist(record)
        key = comparison_key(history, prompt)
        matches = [item for item in record['comparisons'] if item['cache_key'] == key]
        if matches and (matches[-1]['status'] != 'unconfigured' or not ai_status()['available']):
            return record
        comparison_id = key + ':' + str(len(matches) + 1)
        comparison = {'id': comparison_id, 'cache_key': key, 'status': 'running', 'history_hash': history['snapshot_hash'], 'prompt': prompt, 'prompt_revision': content_hash(selected_definition['functions']['make_prompt']), 'prompt_source': selected_definition['functions']['make_prompt'], 'started_at': now(), 'finished_at': None, 'rule_result': deepcopy(record['rule_result']), 'ai_result': None, 'error': None}
        record['comparisons'].append(comparison)
        service.persist(record)
    result = decide_with_ai(history, prompt)
    with service.LOCK:
        record = service.required_run(identifier)
        comparison = next(item for item in record['comparisons'] if item['id'] == comparison_id)
        comparison.update({'status': 'running' if result['status'] == 'pending' else result['status'], 'finished_at': None if result['status'] == 'pending' else now(), 'ai_result': result, 'error': result.get('error')})
        return service.persist(record, {'type': 'ai_compared', 'operator': operator, 'message': '같은 고정 이력의 규칙과 AI 판단을 비교했습니다. 실행 분기·조치·정책은 바꾸지 않았습니다.'})
