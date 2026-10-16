from datetime import datetime, timezone
import json
import os
from pathlib import Path

from notice_state import atomic_write


def prepare_request_history():
    log_path = Path(os.environ.get('REQUEST_LOG_PATH', '/classroom-logs/app.jsonl'))
    marker_path = log_path.with_name('request-history-start.json')
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    if marker_path.exists():
        return json.loads(marker_path.read_text(encoding='utf-8'))
    offset = log_path.stat().st_size if log_path.exists() else 0
    if offset:
        with log_path.open('rb') as source:
            old_count = sum(1 for line in source if line.endswith(b'\n'))
    else:
        old_count = 0
    marker = {
        'schema_version': 2, 'started_at': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
        'start_offset': offset, 'older_records_excluded': old_count,
    }
    atomic_write(marker_path, json.dumps(marker).encode('utf-8'))
    return marker
