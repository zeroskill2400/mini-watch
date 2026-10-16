from copy import deepcopy
from hashlib import sha256
import ast
import os
from pathlib import Path
from threading import RLock
from types import ModuleType
from uuid import uuid4

import requests

from ai_client import AIError, ai_status, analyze_case
from correlation_rules import correlation_status
from investigation_service import read_investigation, SERVER_ID, TARGET_PATH
from playbook_tools import find_urls
from soar_service import ACTION_URL, OPERATOR, SoarError, current_action_policy, now, require_operator, verification_evidence
from url_playbook_store import list_runs, read_run, save_run


INTERNAL_URL = 'http://general-api:5000/internal'
CTI_SOURCE = '수업용 로컬 CTI API'
LOCK = RLock()
ALLOWED_ACTIONS = {'restrict_notice', 'notify', 'create_ticket'}
SYSTEM_ACTOR = 'system'
STEP_FUNCTIONS = [('extract', 'extract_url'), ('lookup', 'lookup_classroom_cti'), ('decide', 'decide'), ('plan', 'choose_actions / make_message'), ('execute', 'execute_actions'), ('record', 'save_result')]


def load_rules():
    path = Path(os.environ.get('PLAYBOOK_RULES_PATH', str(Path(__file__).with_name('soar_rules.py'))))
    try:
        source = path.read_text(encoding='utf-8')
        parsed = ast.parse(source, filename=str(path))
        module = ModuleType('current_student_playbook')
        exec(compile(parsed, str(path), 'exec'), module.__dict__)
        history_flow = any(isinstance(node, ast.FunctionDef) and node.name == 'decide_with_rule' for node in parsed.body)
        names = ['decide_with_rule', 'make_prompt', 'decide', 'choose_actions'] if history_flow else ['extract_url', 'decide', 'choose_actions', 'make_message']
        functions = {node.name: ast.get_source_segment(source, node) for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in names}
        if set(functions) != set(names) or any(not callable(getattr(module, name, None)) for name in names):
            raise SoarError('soar_rules.py에 ' + ', '.join(names) + ' 함수 네 개가 필요합니다.')
    except SoarError:
        raise
    except SyntaxError as error:
        raise SoarError(f'soar_rules.py {error.lineno}행의 문법을 확인해 주세요. 기존 실행은 계속 읽거나 복구할 수 있습니다.') from error
    except Exception as error:
        raise SoarError('soar_rules.py를 읽거나 불러오지 못했습니다. 파일과 import를 확인해 주세요. 기존 실행은 보존합니다.') from error
    revision = sha256('\n'.join(functions.values()).encode('utf-8')).hexdigest()[:16]
    return module, {'name': '요청 이력 판단과 대응' if history_flow else '공지 URL 조회와 대응', 'flow': 'history-v1' if history_flow else 'url-v1', 'trigger': 'notice_file_change', 'revision': revision, 'source_sha256': sha256(source.encode('utf-8')).hexdigest(), 'functions': functions, 'valid': True, 'error': None}


def definition():
    try:
        return load_rules()[1]
    except SoarError as error:
        return {'name': '요청 이력 판단과 대응', 'flow': 'history-v1', 'trigger': 'notice_file_change', 'revision': None, 'functions': {}, 'valid': False, 'error': str(error)}


def required_run(identifier):
    record = read_run(identifier=identifier)
    if record is None:
        raise SoarError('플레이북 실행을 찾지 못했습니다.', 404)
    return record


def persist(record, event=None):
    record['updated_at'] = now()
    if record.get('flow') == 'history-v1':
        record['approve_allowed'] = record['state'] == 'review_pending' and record.get('decision', {}).get('status') == 'succeeded' and record.get('history_snapshot', {}).get('quality', {}).get('complete') is True
    else:
        record['approve_allowed'] = record['state'] == 'review_pending' and record.get('score') is not None and record.get('lookup', {}).get('status') == 'found'
    if event:
        record['history'].append({'at': record['updated_at'], **event})
    save_run(record)
    return record


def set_step(record, identifier, inputs, output=None, status='succeeded', error=None):
    selected = next(item for item in record['steps'] if item['id'] == identifier)
    selected.update({'input': inputs, 'output': output, 'status': status, 'error': error, 'at': now()})
    persist(record)


def internal_get(path, params=None):
    try:
        response = requests.get(INTERNAL_URL + path, params=params, headers={'X-Event-Token': os.environ.get('EVENT_TOKEN', '')}, timeout=(3, 8), allow_redirects=False)
        data = response.json()
        if response.status_code != 200:
            raise SoarError(data.get('error', '수업용 내부 조회에 실패했습니다.') if isinstance(data, dict) else '수업용 내부 조회에 실패했습니다.', 502)
        if not isinstance(data, dict):
            raise SoarError('수업용 내부 조회의 응답 형식을 확인하지 못했습니다.', 502)
        return data
    except (requests.RequestException, ValueError) as error:
        raise SoarError('수업용 내부 API에 연결하지 못했습니다. 안전한 대상으로 판정하지 않습니다.', 502) from error


def candidate(case, strict):
    raw = case['write']['raw']
    eligible = strict and case.get('hash_matches') is True and raw.get('notice_snapshot_sha256') == raw.get('sha256')
    reason = '앱 저장과 센서의 같은 해시로 공지 내용을 확인할 수 있습니다. 로그인 실패 횟수는 요구하지 않습니다.' if eligible else '내용 스냅샷이 있는 새 공지 저장과 센서의 같은 해시를 확인해 주세요. 이전 자료는 보존합니다.'
    return {'case_id': case['id'], 'case': case, 'eligible': eligible, 'reason': reason}


def read_overview(selected_definition=None):
    from history_ai import resolve_comparisons
    from url_playbook_automation import automation_status

    investigation = read_investigation()
    records = list_runs()
    for record in records:
        resolve_comparisons(record)
    return {
        'definition': selected_definition if selected_definition is not None else definition(), 'cti': {'source': CTI_SOURCE, 'synthetic': True, 'external_url_access': False},
        'candidates': [candidate(case, investigation['correlation'].get('require_same_hash') is True) for case in investigation['cases']],
        'runs': records, 'policy': investigation['policy'], 'ai': ai_status(), 'observation': investigation['observation'],
        'automation': automation_status(),
    }


def checked_actions(values, branch):
    if not isinstance(values, list) or any(not isinstance(value, str) or value not in ALLOWED_ACTIONS for value in values) or len(values) != len(set(values)):
        raise SoarError('조치 목록에는 restrict_notice, notify, create_ticket만 중복 없이 사용할 수 있습니다.')
    if branch == 'review' and 'restrict_notice' in values:
        raise SoarError('검토 분기에서 자동 제한은 허용하지 않습니다. 제한은 respond 목록에서만 연결해 주세요.')
    return list(values)


def checked_message(student_rules, url, score, branch):
    message = student_rules.make_message(url or '추출되지 않음', score if score is not None else '미확인', branch)
    if not isinstance(message, str) or not 1 <= len(message) <= 1000:
        raise SoarError('make_message는 1~1000자 문장을 반환해야 합니다.')
    return message


def create_run(case_id, execution_key, operator):
    require_operator(operator)
    return create_selected_run(case_id, execution_key, operator)


def create_automatic_run(selected, activated_at):
    write_id = selected['case']['write']['event_id']
    trigger = {
        'type': 'notice_file_change', 'actor': SYSTEM_ACTOR,
        'write_event_id': write_id, 'sensor_event_id': selected['case']['sensor']['event_id'],
        'activated_at': activated_at,
    }
    return create_selected_run(selected['case_id'], 'auto:' + write_id, SYSTEM_ACTOR, selected, trigger)


def create_selected_run(case_id, execution_key, operator, selected=None, trigger=None):
    with LOCK:
        previous = read_run(execution_key=execution_key)
        if previous:
            if previous['case_id'] != case_id:
                raise SoarError('같은 실행 키를 다른 사건에 사용할 수 없습니다.')
            return previous
    student_rules, selected_definition = load_rules()
    if selected_definition['flow'] == 'history-v1':
        from history_playbook_service import create_history_run

        return create_history_run(case_id, execution_key, operator, student_rules, selected_definition, selected, trigger)
    return create_url_run(case_id, execution_key, operator, selected, trigger)


def create_url_run(case_id, execution_key, operator, selected=None, trigger=None):
    with LOCK:
        previous = read_run(execution_key=execution_key)
        if previous:
            if previous['case_id'] != case_id:
                raise SoarError('같은 실행 키를 다른 사건에 사용할 수 없습니다.')
            return previous
        student_rules, selected_definition = load_rules()
        if selected is None:
            overview = read_overview(selected_definition)
            selected = next((item for item in overview['candidates'] if item['case_id'] == case_id), None)
        if selected is None or not selected['eligible']:
            raise SoarError(selected['reason'] if selected else '현재 실제 공지 변경 사건을 먼저 선택해 주세요.')
        record = {
            'id': 'run-' + uuid4().hex, 'execution_key': execution_key, 'case_id': case_id,
            'case_snapshot': deepcopy(selected['case']), 'definition': selected_definition,
            'state': 'running', 'created_at': now(), 'updated_at': now(), 'created_by': operator,
            'trigger': trigger or {'type': 'manual_compatibility', 'actor': operator},
            'url': None, 'score': None, 'branch': None, 'effective_branch': None, 'lookup': {},
            'plan': [], 'respond_plan': [], 'message': '', 'respond_message': '',
            'steps': [{'id': identifier, 'function_name': function, 'input': None, 'output': None, 'status': 'pending', 'error': None} for identifier, function in STEP_FUNCTIONS],
            'actions': [], 'notification': None, 'ticket': None, 'summary': None,
            'restriction': None, 'verification': None, 'recovery': None, 'recovery_verification': None,
            'approval': None, 'recovery_approval': None, 'ai_summary': None, 'ai_history': [], 'ai_error': None, 'ai_running': False,
            'last_error': None, 'history': [], 'approve_allowed': False,
        }
        persist(record, {'type': 'started', 'operator': operator, 'message': '서버가 새 앱 저장과 센서 사건을 감지해 플레이북을 자동 시작했습니다.' if trigger else '호환 경로에서 사람이 선택한 사건으로 실행을 시작했습니다.'})
        stage = 'extract'
        try:
            digest = selected['case']['write']['raw']['sha256']
            snapshot = internal_get('/notice-snapshots/' + digest)
            if snapshot.get('sha256') != digest or snapshot.get('server_id') != SERVER_ID or snapshot.get('target_path') != TARGET_PATH or not isinstance(snapshot.get('content'), str) or sha256(snapshot['content'].encode('utf-8')).hexdigest() != digest:
                raise SoarError('사건 원본과 공지 내용 스냅샷이 일치하지 않습니다.')
            record['notice_snapshot'] = snapshot
            record['url'] = student_rules.extract_url(snapshot['content'])
            if record['url'] is not None and record['url'] not in find_urls(snapshot['content']):
                raise SoarError('extract_url은 이 공지에 실제로 있는 URL 또는 None을 반환해야 합니다.')
            set_step(record, 'extract', {'text': snapshot['content']}, {'url': record['url']})
            stage = 'lookup'
            if record['url'] is None:
                record['lookup'] = {'source': CTI_SOURCE, 'synthetic': True, 'status': 'no_url', 'score': None, 'note': 'URL이 없어 조회하지 않았습니다. 안전하다는 뜻이 아닙니다.'}
            else:
                try:
                    result = internal_get('/classroom-cti', {'url': record['url']})
                    score = result.get('score')
                    if result.get('source') != CTI_SOURCE or result.get('synthetic') is not True or result.get('url') != record['url'] or result.get('status') not in {'found', 'not_listed'} or (result['status'] == 'found' and (type(score) is not int or not 0 <= score <= 100)) or (result['status'] == 'not_listed' and score is not None):
                        raise SoarError('수업용 조회 응답의 출처·대상·점수를 확인하지 못했습니다.', 502)
                    record['lookup'] = result
                except SoarError as error:
                    record['lookup'] = {'source': CTI_SOURCE, 'synthetic': True, 'status': 'lookup_failed', 'score': None, 'note': str(error)}
            record['score'] = record['lookup']['score']
            set_step(record, 'lookup', {'url': record['url']}, record['lookup'], status='failed' if record['lookup']['status'] == 'lookup_failed' else 'succeeded', error=record['lookup']['note'] if record['lookup']['status'] == 'lookup_failed' else None)
            stage = 'decide'
            record['branch'] = student_rules.decide(record['score']) if record['score'] is not None else 'review'
            if record['branch'] not in {'review', 'respond'}:
                raise SoarError('decide는 review 또는 respond를 반환해야 합니다.')
            record['effective_branch'] = record['branch']
            set_step(record, 'decide', {'score': record['score']}, {'branch': record['branch'], 'guard': None if record['score'] is not None else '점수를 확인하지 못해 자동 대응하지 않습니다.'})
            stage = 'plan'
            record['plan'] = checked_actions(student_rules.choose_actions(record['branch']), record['branch'])
            record['respond_plan'] = checked_actions(student_rules.choose_actions('respond'), 'respond')
            record['message'] = checked_message(student_rules, record['url'], record['score'], record['branch'])
            record['respond_message'] = checked_message(student_rules, record['url'], record['score'], 'respond')
            set_step(record, 'plan', {'branch': record['branch'], 'url': record['url'], 'score': record['score']}, {'actions': record['plan'], 'message': record['message'], 'approval_actions': record['respond_plan']})
            return execute_actions(record)
        except Exception as error:
            record['state'], record['last_error'] = 'error', str(error) if isinstance(error, SoarError) else '학생 함수 또는 준비된 처리에서 오류가 발생했습니다. 함수를 확인해 주세요.'
            set_step(record, stage, next(item for item in record['steps'] if item['id'] == stage)['input'], status='failed', error=record['last_error'])
            return persist(record, {'type': 'failed', 'message': record['last_error']})


def policy_action(record, recovery=False):
    operation_id = record['id'] + (':restore' if recovery else ':restrict')
    approval = record.get('recovery_approval' if recovery else 'approval')
    actor = approval['operator'] if approval else record['created_by']
    payload = {'blocked': not recovery, 'operator': actor, 'request_id': record['id'], 'operation_id': operation_id}
    if not recovery:
        payload['expected_sha256'] = record['notice_snapshot']['sha256']
    try:
        response = requests.post(ACTION_URL, json=payload, headers={'X-Event-Token': os.environ.get('EVENT_TOKEN', '')}, timeout=(3, 10), allow_redirects=False)
        result = response.json()
        if response.status_code != 200:
            raise SoarError(result.get('error', '공지 정책을 적용하지 못했습니다.') if isinstance(result, dict) else '공지 정책을 적용하지 못했습니다.', 502)
        if not isinstance(result, dict) or result.get('operation_id') != operation_id or result.get('request_id') != record['id'] or result.get('blocked') is not (not recovery) or result.get('server_id') != SERVER_ID or result.get('target_path') != TARGET_PATH or not result.get('event_id'):
            raise SoarError('실제 정책 응답의 대상·조치 번호·근거를 확인하지 못했습니다.', 502)
        return result
    except (requests.RequestException, ValueError) as error:
        raise SoarError('정책 응답을 확인하지 못했습니다. 완료로 처리하지 않으며 같은 실행으로 다시 확인할 수 있습니다.', 502) from error


def local_output(record, action):
    field = 'notification' if action == 'notify' else 'ticket'
    if record[field] is None:
        record[field] = {'id': field + '-' + record['id'], 'run_id': record['id'], 'created_at': now(), 'message': record['message'], 'source': '수업 감시 화면 내부', 'external_send': False, 'updates': []}
        if action == 'create_ticket':
            record[field]['status'] = 'open'
    elif record[field]['message'] != record['message']:
        record[field]['updates'].append({'at': now(), 'previous_message': record[field]['message']})
        record[field]['message'] = record['message']
    return deepcopy(record[field])


def execute_actions(record):
    record['state'], record['last_error'] = 'running', None
    set_step(record, 'execute', {'actions': record['plan'], 'effective_branch': record['effective_branch']}, status='running')
    for identifier in record['plan']:
        action = next((item for item in record['actions'] if item['id'] == identifier), None)
        if action is None:
            action = {'id': identifier, 'status': 'pending', 'result': None, 'error': None, 'attempts': []}
            record['actions'].append(action)
        if action['status'] == 'succeeded':
            if identifier in {'notify', 'create_ticket'}:
                action['result'] = local_output(record, identifier)
            continue
        attempt = {'started_at': now(), 'finished_at': None, 'status': 'running', 'operation_id': record['id'] + ':restrict' if identifier == 'restrict_notice' else None}
        action['attempts'].append(attempt)
        action['status'] = 'running'
        persist(record)
        try:
            if identifier == 'restrict_notice':
                if record.get('flow') == 'history-v1':
                    from history_playbook_service import response_allowed

                    valid_decision = response_allowed(record)
                else:
                    valid_decision = record['score'] is not None
                if record['effective_branch'] != 'respond' or not valid_decision or not record['case_snapshot']['hash_matches']:
                    raise SoarError('유효한 근거와 대응 분기 없이 제한하지 않습니다.')
                result = policy_action(record)
                record['restriction'] = result
            else:
                result = local_output(record, identifier)
            action.update({'status': 'succeeded', 'result': result, 'error': None})
            attempt.update({'finished_at': now(), 'status': 'succeeded'})
        except Exception as error:
            message = str(error) if isinstance(error, SoarError) else '조치 결과를 저장하지 못했습니다. 같은 실행에서 확인해 주세요.'
            action.update({'status': 'failed', 'error': message})
            attempt.update({'finished_at': now(), 'status': 'failed', 'error': message})
            record['state'], record['last_error'] = 'error', message
            set_step(record, 'execute', {'actions': record['plan']}, record['actions'], 'failed', message)
            return record_result(record)
        persist(record)
    record['state'] = 'review_pending' if record['effective_branch'] == 'review' else 'restricted' if record['restriction'] else 'completed'
    set_step(record, 'execute', {'actions': record['plan'], 'effective_branch': record['effective_branch']}, record['actions'])
    return record_result(record)


def record_result(record):
    record['summary'] = {'state': record['state'], 'branch': record['branch'], 'effective_branch': record['effective_branch'], 'actions': [{'id': item['id'], 'status': item['status']} for item in record['actions']], 'message': record['message'], 'last_error': record['last_error']}
    set_step(record, 'record', {'run_id': record['id']}, record['summary'])
    return persist(record, {'type': 'result_saved', 'message': '실제 분기와 조치 결과를 이 실행에 저장했습니다.'})


def approve_run(identifier, operator):
    require_operator(operator)
    with LOCK:
        record = required_run(identifier)
        if not record['approve_allowed']:
            raise SoarError('유효한 판단 근거가 있는 검토 대기 실행에서만 승인할 수 있습니다.')
        record['approval'] = {'operator': operator, 'at': now()}
        record['effective_branch'], record['plan'], record['message'] = 'respond', list(record['respond_plan']), record['respond_message']
        persist(record, {'type': 'approved', 'operator': operator, 'message': '사람이 이 실행에 고정된 대응 조치 목록을 승인했습니다.'})
        return execute_actions(record)


def retry_run(identifier, operator):
    require_operator(operator)
    with LOCK:
        record = required_run(identifier)
        if record['state'] == 'recovery_error':
            return finish_recovery(record)
        if record['state'] != 'error' or not any(item['status'] in {'failed', 'running'} for item in record['actions']):
            raise SoarError('조치 응답을 확인하지 못한 실행에서만 다시 확인할 수 있습니다. 함수 변경 비교는 새 실행으로 진행해 주세요.')
        return execute_actions(record)


def verify_run(identifier, operator):
    require_operator(operator)
    with LOCK:
        record = required_run(identifier)
        if record['state'] not in {'restricted', 'restored'}:
            raise SoarError('제한 또는 복구 뒤 실제 저장을 시도한 다음 확인해 주세요.')
        raw, status, action = verification_evidence(record)
        recovery = record['state'] == 'restored'
        record['recovery_verification' if recovery else 'verification'] = {'event_id': raw['event_id'], 'status_code': status, 'expected_outcome': 'save_succeeded' if recovery else 'policy_denied', 'raw': raw, 'operation_id': action['operation_id']}
        record['state'] = 'completed_recovery' if recovery else 'verified'
        if recovery and record['ticket']:
            record['ticket']['status'] = 'resolved'
        return record_result(record)


def finish_recovery(record):
    try:
        record['recovery'] = policy_action(record, recovery=True)
        record['state'], record['last_error'] = 'restored', None
    except SoarError as error:
        record['state'], record['last_error'] = 'recovery_error', str(error)
    return record_result(record)


def recover_run(identifier, operator):
    require_operator(operator)
    with LOCK:
        record = required_run(identifier)
        policy = current_action_policy()
        if record['state'] not in {'restricted', 'verified', 'error'} or not policy['blocked'] or policy.get('owner_request_id') != identifier:
            raise SoarError('이 실행이 소유한 현재 공지 제한만 복구할 수 있습니다.')
        receipt = policy.get('receipts', {}).get(identifier + ':restrict')
        if not receipt:
            raise SoarError('실제 제한 영수증을 확인하지 못했습니다.')
        record['restriction'] = receipt
        record['recovery_approval'] = {'operator': operator, 'at': now()}
        record['state'] = 'recovering'
        persist(record, {'type': 'recovery_approved', 'operator': operator, 'message': '사람이 이 실행의 저장 허용 복구를 승인했습니다. 공지 원문 복원은 아닙니다.'})
        return finish_recovery(record)


def summarize_run(identifier, operator):
    require_operator(operator)
    with LOCK:
        record = required_run(identifier)
        if record.get('ai_running'):
            raise SoarError('이 실행의 실제 AI 요약 요청이 이미 진행 중입니다.')
        case = deepcopy(record['case_snapshot'])
        context = {'url': record['url'], 'lookup': record['lookup'], 'branch': record['branch'], 'actions': record['summary']}
        record['ai_running'] = True
        persist(record)
    try:
        result = analyze_case(case, correlation_status(), '수업용 조회 점수와 실제 관찰 근거를 구분하여 이 실행 결과를 짧게 요약해 주세요. 조치를 결정하거나 실행하지 마세요.', context=context)
    except AIError as error:
        with LOCK:
            record = required_run(identifier)
            record['ai_running'] = False
            record['ai_error'] = {'code': error.code, 'message': str(error), 'at': now()}
            persist(record, {'type': 'ai_failed', 'message': str(error)})
        raise SoarError(str(error), error.status) from error
    with LOCK:
        record = required_run(identifier)
        record['ai_running'] = False
        record['ai_summary'] = {'at': now(), **result}
        record['ai_history'].append(record['ai_summary'])
        record['ai_error'] = None
        return persist(record, {'type': 'ai_summarized', 'message': '선택한 실제 AI 요약 응답을 저장했습니다. 플레이북 분기와 조치는 바꾸지 않았습니다.'})


def recover_interrupted_runs():
    from history_ai import recover_interrupted_calls, resolve_comparisons

    recover_interrupted_calls()
    with LOCK:
        for record in list_runs():
            changed = resolve_comparisons(record)
            if record['state'] in {'running', 'recovering'}:
                record['state'] = 'recovery_error' if record['state'] == 'recovering' else 'error'
                record['last_error'] = '재시작 전에 결과 저장을 마치지 못했습니다. 완료가 아닙니다. 조치가 적용됐다면 같은 실행에서 확인하거나 복구해 주세요.'
                for action in record['actions']:
                    if action['status'] == 'running':
                        action['status'], action['error'] = 'failed', record['last_error']
                        action['attempts'][-1].update({'status': 'failed', 'finished_at': now(), 'error': record['last_error']})
                changed = True
            if record.get('ai_running'):
                record['ai_running'] = False
                record['ai_error'] = {'code': 'ai_interrupted', 'message': '재시작 전에 AI 응답 저장을 마치지 못했습니다. 기존 응답은 보존합니다.', 'at': now()}
                changed = True
            for comparison in record.get('comparisons', []):
                if comparison['status'] == 'running':
                    from history_ai import fallback

                    decision = fallback('failed', '재시작 전에 비교 응답을 저장하지 못했습니다. 자동으로 다시 호출하지 않습니다.', 'ai_interrupted')
                    comparison.update({'status': 'failed', 'finished_at': now(), 'ai_result': decision, 'error': decision['error']})
                    changed = True
            if changed:
                record_result(record)
