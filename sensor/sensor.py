import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from uuid import uuid4


class FileSensor:
    def __init__(self, notice_path, log_path, server_id='general-01'):
        self.notice_path = Path(notice_path)
        self.log_path = Path(log_path)
        self.server_id = server_id
        self.previous_sha256 = None

    def observe(self):
        digest = hashlib.sha256(self.notice_path.read_bytes()).hexdigest()
        observed_at = datetime.now(timezone.utc).isoformat(timespec='microseconds')
        if self.previous_sha256 is None:
            self.previous_sha256 = digest
            return None
        if digest == self.previous_sha256:
            return None
        event = {
            'event_id': str(uuid4()),
            'occurred_at': observed_at,
            'event_type': 'file_change',
            'server_id': self.server_id,
            'target_path': '/classroom-data/notice.txt',
            'previous_sha256': self.previous_sha256,
            'sha256': digest,
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open('a', encoding='utf-8') as log_file:
            log_file.write(json.dumps(event, ensure_ascii=False) + '\n')
        self.previous_sha256 = digest
        return event


def main():
    heartbeat = Path('/run/file-sensor/heartbeat')
    if '--healthcheck' in sys.argv:
        healthy = heartbeat.exists() and time.time() - heartbeat.stat().st_mtime < 5
        raise SystemExit(0 if healthy else 1)
    sensor = FileSensor(
        Path(os.environ.get('CLASSROOM_DATA_DIR', '/classroom-data')) / 'notice.txt',
        Path(os.environ.get('CLASSROOM_LOG_DIR', '/classroom-logs')) / 'file-events.jsonl',
        os.environ.get('CLASSROOM_SERVER_ID', 'general-01'),
    )
    heartbeat.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            event = sensor.observe()
            if event is not None:
                print(json.dumps(event, ensure_ascii=False), flush=True)
            heartbeat.touch()
        except OSError:
            print('공지 파일을 관측하거나 센서 원본을 기록하지 못했습니다.', file=sys.stderr, flush=True)
        time.sleep(1.0)


if __name__ == '__main__':
    main()
