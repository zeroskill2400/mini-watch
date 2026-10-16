import hmac
import os

from flask import Blueprint, current_app, g, redirect, render_template, request, session

from auth_helpers import api_access_error, current_user, valid_csrf
from notice_state import NoticeError, apply_approved_action, read_notice, read_notice_snapshot, read_policy, write_notice
from classroom_cti import lookup_url


notice_bp = Blueprint('notice', __name__)


def save_notice(content):
    user = current_user()
    result = write_notice(content, user['username'], session.get('auth_event_id'))
    if result['event'] is not None:
        g.classroom_event = result['event']
    return result


def unavailable():
    current_app.logger.error('수업 공지 저장소를 읽거나 기록하지 못했습니다.')
    return {'error': '공지 저장소를 확인해 주세요. 기존 파일과 정책은 초기화하지 않았습니다.'}, 503


@notice_bp.route('/api/notice', methods=['GET', 'POST'])
def notice_api():
    error = api_access_error()
    if error:
        return error
    try:
        if request.method == 'GET':
            return read_notice()
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {'content'}:
            return {'error': 'content만 JSON으로 보내 주세요.'}, 400
        return save_notice(data['content'])
    except NoticeError as error:
        if error.event:
            g.classroom_event = error.event
        return {'error': str(error)}, error.status
    except (OSError, ValueError, UnicodeError):
        return unavailable()


@notice_bp.route('/notice', methods=['GET', 'POST'])
def notice_page():
    if current_user() is None:
        return redirect('/login', code=303)
    message = None
    error = None
    status = 200
    try:
        try:
            if request.method == 'POST':
                if not valid_csrf(request.form.get('csrf_token')):
                    raise NoticeError('요청 확인 값이 올바르지 않습니다. 새로고침 후 다시 시도해 주세요.', 403)
                result = save_notice(request.form.get('content'))
                message = '공지 파일을 저장했습니다. 감시 화면을 새로고침해 센서 기록을 확인하세요.' if result['changed'] else '내용이 같아 파일을 변경하지 않았습니다.'
        except NoticeError as caught:
            if caught.event:
                g.classroom_event = caught.event
            error, status = str(caught), caught.status
        notice = read_notice()
    except (OSError, ValueError, UnicodeError):
        payload, status = unavailable()
        return render_template('error.html', message=payload['error']), status
    return render_template(
        'notice.html', notice=notice, message=message, error=error,
        response_status=status if request.method == 'POST' else None,
    ), status


@notice_bp.route('/internal/notice-policy', methods=['GET', 'POST'])
def notice_policy():
    supplied = request.headers.get('X-Event-Token', '')
    expected = os.environ.get('EVENT_TOKEN', '')
    if not expected or not hmac.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8')):
        return {'error': '내부 요청 인증에 실패했습니다.'}, 403
    try:
        if request.method == 'GET':
            return read_policy()
        return {'error': '승인된 대응 요청의 조치 경로를 사용해 주세요.'}, 409
    except NoticeError as error:
        return {'error': str(error)}, error.status
    except (OSError, ValueError, UnicodeError):
        return unavailable()


@notice_bp.post('/internal/notice-action')
def notice_action():
    supplied = request.headers.get('X-Event-Token', '')
    expected = os.environ.get('EVENT_TOKEN', '')
    if not expected or not hmac.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8')):
        return {'error': '내부 요청 인증에 실패했습니다.'}, 403
    data = request.get_json(silent=True)
    required = {'blocked', 'operator', 'operation_id', 'request_id'}
    if not isinstance(data, dict) or set(data) not in (required, required | {'expected_sha256'}):
        return {'error': '허용된 조치 입력만 보내 주세요.'}, 400
    try:
        policy, event = apply_approved_action(**data)
        if event:
            g.classroom_event = event
        return policy
    except NoticeError as error:
        return {'error': str(error)}, error.status
    except (OSError, ValueError, UnicodeError):
        return unavailable()


@notice_bp.get('/internal/notice-snapshots/<digest>')
@notice_bp.get('/internal/classroom-cti')
def playbook_evidence(digest=None):
    supplied = request.headers.get('X-Event-Token', '')
    expected = os.environ.get('EVENT_TOKEN', '')
    if not expected or not hmac.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8')):
        return {'error': '내부 요청 인증에 실패했습니다.'}, 403
    try:
        if digest is not None:
            return read_notice_snapshot(digest)
        if set(request.args) != {'url'}:
            return {'error': '조회할 url 하나만 보내 주세요.'}, 400
        return lookup_url(request.args['url'])
    except NoticeError as error:
        return {'error': str(error)}, error.status
    except ValueError:
        return {'error': '조회 입력 또는 저장된 공지 내용을 확인해 주세요.'}, 400
    except (OSError, UnicodeError):
        return unavailable()
