from flask import Blueprint, request

from auth_helpers import api_access_error, current_user
from soar_service import SoarError, create_request, decide_request, notify_request, read_soar, recover_request, require_operator, retry_request, verify_request


soar_bp = Blueprint('soar', __name__)


def operator_name():
    user = current_user()
    username = user['username'] if user else None
    require_operator(username)
    return username


@soar_bp.get('/api/soar')
def overview():
    error = api_access_error()
    if error:
        return error
    try:
        operator_name()
        return read_soar()
    except SoarError as caught:
        return {'error': str(caught)}, caught.status


@soar_bp.post('/api/soar/requests')
def create():
    error = api_access_error()
    if error:
        return error
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'case_id'} or not isinstance(data['case_id'], str) or not 1 <= len(data['case_id']) <= 100:
        return {'error': '현재 실제 사건의 case_id만 보내 주세요.'}, 400
    try:
        return {'request': create_request(data['case_id'], operator_name())}, 201
    except SoarError as caught:
        return {'error': str(caught)}, caught.status


@soar_bp.post('/api/soar/requests/<identifier>/<action>')
def transition(identifier, action):
    error = api_access_error()
    if error:
        return error
    if request.get_json(silent=True) != {}:
        return {'error': '추가 대상이나 명령 없이 요청 번호와 버튼만 사용해 주세요.'}, 400
    try:
        operator = operator_name()
        if action == 'notify':
            result = notify_request(identifier, operator)
        elif action in {'approve', 'reject', 'cancel'}:
            result = decide_request(identifier, action, operator)
        elif action == 'verify':
            result = verify_request(identifier, operator)
        elif action == 'recover':
            result = recover_request(identifier, operator)
        elif action == 'retry':
            result = retry_request(identifier, operator)
        else:
            raise SoarError('허용된 대응 버튼이 아닙니다.', 404)
        return {'request': result}
    except SoarError as caught:
        return {'error': str(caught)}, caught.status
