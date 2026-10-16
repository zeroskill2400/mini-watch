import json
import os
import re
from datetime import datetime, timezone

import requests

from ai_client import ai_status
from correlation_rules import build_cases, correlation_status
from detection_rules import normalize_auth_event, parse_time
from detection_service import read_detection
from learning.log_data import read_complete_lines

POLICY_URL = "http://general-api:5000/internal/notice-policy"
SERVER_ID = "general-01"
TARGET_PATH = "/classroom-data/notice.txt"
MAX_DISPLAY_EVENTS = 100


class PolicyError(Exception):
    pass


def read_records(filename):
    records = []
    try:
        lines = read_complete_lines(filename)
    except (OSError, UnicodeError):
        return records
    for line in lines:
        try:
            raw = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(raw, dict):
            continue
        identifier = raw.get("event_id")
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 128:
            continue
        try:
            parse_time(raw.get("occurred_at"))
        except (ValueError, TypeError, OverflowError):
            continue
        records.append(raw)
    return records


def wrap_event(raw, source):
    return {"event_id": raw["event_id"], "event_type": raw["event_type"], "occurred_at": raw["occurred_at"], "source": source, "raw": raw}


def file_record(raw, event_type):
    if raw.get("event_type") != event_type or raw.get("server_id") != SERVER_ID or raw.get("target_path") != TARGET_PATH:
        return False
    if not isinstance(raw.get("sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", raw["sha256"]) is None:
        return False
    if event_type == "file_write":
        return all(isinstance(raw.get(field), str) and 1 <= len(raw[field]) <= 128 for field in ["authenticated_username", "auth_event_id", "request_id"])
    previous = raw.get("previous_sha256")
    return previous is None or isinstance(previous, str) and re.fullmatch(r"[0-9a-f]{64}", previous) is not None


def observation_events(records, observation, now):
    if not observation:
        return []
    started_at = parse_time(observation["started_at"])
    selected = {}
    for raw in records:
        if started_at <= parse_time(raw["occurred_at"]) <= now:
            selected.setdefault(raw["event_id"], raw)
    return sorted(selected.values(), key=lambda raw: (parse_time(raw["occurred_at"]), raw["event_id"]))


def request_policy(blocked=None, operator=None):
    token = os.environ.get("EVENT_TOKEN", "")
    if not token:
        raise PolicyError("공지 정책 연결 토큰이 준비되지 않았습니다.")
    data = None
    method = "GET"
    if blocked is not None:
        if type(blocked) is not bool or not isinstance(operator, str) or not operator.strip():
            raise PolicyError("공지 정책 입력이 올바르지 않습니다.")
        method = "POST"
        data = {"blocked": blocked, "operator": operator}
    try:
        response = requests.request(method, POLICY_URL, headers={"X-Event-Token": token}, json=data, timeout=(3, 10), allow_redirects=False)
        if response.status_code != 200:
            raise PolicyError("일반 서비스에서 공지 정책을 확인하지 못했습니다.")
        result = response.json()
        if not isinstance(result, dict) or type(result.get("blocked")) is not bool or result.get("server_id") != SERVER_ID or result.get("target_path") != TARGET_PATH:
            raise PolicyError("공지 정책 응답이 올바르지 않습니다.")
    except (requests.RequestException, ValueError, TypeError) as error:
        raise PolicyError("일반 서비스의 공지 정책에 연결하지 못했습니다.") from error
    return {"available": True, **{field: result.get(field) for field in ["blocked", "operator", "updated_at", "event_id", "server_id", "target_path"]}}


def read_investigation(limit=MAX_DISPLAY_EVENTS, started_at=None):
    detection = read_detection()
    observation = detection["observation"]
    if started_at is not None:
        observation = {"id": observation["id"] if observation else "automatic", "started_at": started_at}
    now = datetime.now(timezone.utc)
    app_records = read_records("app.jsonl")
    selected = observation_events(app_records, observation, now)
    sensor_records = observation_events(read_records("file-events.jsonl"), observation, now)
    writes = [wrap_event(raw, "app") for raw in selected if file_record(raw, "file_write")]
    file_events = [wrap_event(raw, "file-sensor") for raw in sensor_records if file_record(raw, "file_change")]
    if limit is not None:
        writes = writes[-limit:]
        file_events = file_events[-limit:]
    successes = []
    for raw in app_records:
        try:
            event = normalize_auth_event(raw)
        except (ValueError, TypeError, OverflowError):
            continue
        if event and event["event_type"] == "auth_success" and parse_time(event["occurred_at"]) <= now:
            successes.append(event)
    audit = [wrap_event(raw, "app") for raw in selected if raw.get("event_type") == "notice_policy_changed"][-MAX_DISPLAY_EVENTS:]
    try:
        policy = request_policy()
    except PolicyError as error:
        policy = {"available": False, "blocked": None, "error": str(error)}
    policy["audit"] = audit
    return {
        "observation": observation,
        "file_events": file_events,
        "writes": writes,
        "cases": build_cases(writes, file_events, successes, detection["alerts"], observation, limit=limit),
        "correlation": correlation_status(),
        "policy": policy,
        "ai": ai_status(),
    }
