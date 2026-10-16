import os
from flask import Flask, abort
from routes.auth import auth_bp
from routes.events import events_bp
from routes.notes import notes_bp
from routes.analysis import analysis_bp
from routes.detection import detection_bp
from routes.investigation import investigation_bp
from routes.soar import soar_bp
from routes.url_playbook import url_playbook_bp
from url_playbook_service import recover_interrupted_runs
from url_playbook_automation import start_auto_worker
from soar_service import start_worker
from auth_helpers import configure_session, no_cache
from error_handlers import register_error_handlers

from auth_helpers import api_access_error
from observability import configure_errors

configure_errors('mini-monitor')
app = Flask(__name__)
app.json.ensure_ascii = False
configure_session(app, "day5_monitor_session")
app.register_blueprint(auth_bp)
app.register_blueprint(events_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(detection_bp)
app.register_blueprint(investigation_bp)
app.register_blueprint(soar_bp)
app.register_blueprint(url_playbook_bp)
register_error_handlers(app)
app.after_request(no_cache)
recover_interrupted_runs()
start_worker()
start_auto_worker()


@app.get('/api/sentry-test')
def sentry_test():
    if os.environ.get('ENABLE_SENTRY_TEST', 'false').lower() != 'true':
        abort(404)
    error = api_access_error()
    if error:
        return error
    return {'message': '오류를 수정했습니다.'}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
