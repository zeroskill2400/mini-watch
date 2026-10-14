import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from uuid import uuid4
import requests


def position(filename):
    return filename.stat().st_size if filename.exists() else 0


def lines_since(filename, offset):
    if not filename.exists():
        return []
    with filename.open("rb") as source:
        source.seek(offset)
        return source.read().decode("utf-8").splitlines()


def main():
    gateway = os.environ.get("GENERAL_GATEWAY_URL", "http://general-gateway").rstrip("/")
    target = urlsplit(gateway)
    if (target.scheme != "http" or target.hostname not in {"general-gateway", "localhost", "127.0.0.1", "::1"}
            or target.username or target.password or target.path or target.query or target.fragment):
        raise ValueError("수집 대상은 로컬 일반 게이트웨이의 HTTP 주소여야 합니다.")
    app_file = Path(os.environ.get("REQUEST_LOG_PATH", "/classroom-logs/app.jsonl"))
    nginx_file = Path(os.environ.get("NGINX_LOG_PATH", "/classroom-logs/nginx.log"))
    case_file = Path(os.environ.get("CLASSROOM_CASE_PATH", "/classroom-data/case.json"))
    monitor_health = os.environ["MONITOR_URL"].rsplit("/api/events", 1)[0] + "/health"
    probe = "classroom_ready=" + uuid4().hex
    probe_offset = position(nginx_file)
    with requests.Session() as client:
        client.trust_env = False
        for attempt in range(60):
            try:
                monitor = client.get(monitor_health, timeout=2)
                gateway_state = client.get(gateway + "/health?" + probe, timeout=2)
                if monitor.status_code == 200 and gateway_state.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("실습 서버가 준비되지 않았습니다.")
        for attempt in range(50):
            if any(probe in line for line in lines_since(nginx_file, probe_offset)):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Nginx 실제 접근 로그를 읽지 못했습니다.")
        app_offset = position(app_file)
        nginx_offset = position(nginx_file)
        expected = [("GET", "/", 200), ("GET", "/training-missing", 404)]
        for method, path, status in expected:
            response = client.get(gateway + path, timeout=15, allow_redirects=False)
            if response.status_code != status:
                raise RuntimeError(f"{path} 응답이 예상한 {status}가 아닙니다.")
    for attempt in range(50):
        app_lines = lines_since(app_file, app_offset)
        nginx_lines = lines_since(nginx_file, nginx_offset)
        if len(app_lines) >= 2 and len(nginx_lines) >= 2:
            break
        time.sleep(0.1)
    app_events = [json.loads(line) for line in app_lines]
    app_observed = [(event["method"], event["path"], event["status_code"]) for event in app_events]
    nginx_observed = []
    for line in nginx_lines:
        prefix, request_text, suffix = line.split('"', 2)
        method, path, protocol = request_text.split()
        nginx_observed.append((method, path, int(suffix.split()[0])))
    if app_observed != expected or nginx_observed != expected:
        raise RuntimeError("두 원본이 각각 2행이어야 합니다. 다른 브라우저 요청을 멈추고 다시 실행하세요.")
    case_file.parent.mkdir(parents=True, exist_ok=True)
    pending_file = case_file.with_suffix(".json.next")
    pending_file.write_text(json.dumps({"app": app_events, "nginx": nginx_lines}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending_file.replace(case_file)
    print("실제 요청 2건을 보냈습니다: GET / 200, GET /training-missing 404")
    print("원본 저장: Flask JSON 2행 + Nginx combined 2행")
    print("monitor/backend/learning/data/case.json 준비 완료")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"실습 준비 실패: {error} 기존 case.json은 바꾸지 않았습니다.", file=sys.stderr)
        raise SystemExit(1)
