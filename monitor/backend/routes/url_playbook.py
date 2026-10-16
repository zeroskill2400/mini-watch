from flask import Blueprint, request

from auth_helpers import api_access_error
from routes.soar import operator_name
from soar_service import SoarError
from history_playbook_service import compare_ai
from url_playbook_service import approve_run, create_run, read_overview, recover_run, retry_run, summarize_run, verify_run


url_playbook_bp = Blueprint('url_playbook', __name__)


@url_playbook_bp.get('/api/soar/playbook')
def overview():
    error = api_access_error()
    if error:
        return error
    try:
        operator_name()
        return read_overview()
    except SoarError as caught:
        return {'error': str(caught)}, caught.status


@url_playbook_bp.post('/api/soar/playbook/runs')
def create():
    error = api_access_error()
    if error:
        return error
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'case_id', 'execution_key'} or any(not isinstance(value, str) or not 1 <= len(value) <= 100 for value in data.values()):
        return {'error': 'case_id와 execution_key만 보내 주세요.'}, 400
    try:
        return {'run': create_run(data['case_id'], data['execution_key'], operator_name())}, 201
    except SoarError as caught:
        return {'error': str(caught)}, caught.status


@url_playbook_bp.post('/api/soar/playbook/runs/<identifier>/<action>')
def transition(identifier, action):
    error = api_access_error()
    if error:
        return error
    if request.get_json(silent=True) != {}:
        return {'error': '실행 번호와 버튼만 사용해 주세요.'}, 400
    functions = {'approve': approve_run, 'verify': verify_run, 'recover': recover_run, 'retry': retry_run, 'ai-summary': summarize_run, 'compare-ai': compare_ai}
    try:
        operator = operator_name()
        if action not in functions:
            raise SoarError('허용되지 않은 플레이북 작업입니다.', 404)
        record = functions[action](identifier, operator)
        pending = action == 'compare-ai' and record.get('comparisons') and record['comparisons'][-1]['status'] == 'running'
        return {'run': record}, 202 if pending else 200
    except SoarError as caught:
        return {'error': str(caught)}, caught.status
