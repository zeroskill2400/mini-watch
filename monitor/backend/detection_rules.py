from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from hashlib import sha256

THRESHOLD = 3
WINDOW_SECONDS = 60
RULE = {
    "id": "repeated-auth-failure",
    "threshold": THRESHOLD,
    "window_seconds": WINDOW_SECONDS,
    "source": "app",
}
LOGIN_PATHS = {"/auth/login", "/api/auth/login"}


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError("발생 시각이 문자열이 아닙니다.")
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("발생 시각에 시간대가 없습니다.")
    return moment.astimezone(timezone.utc)


def normalize_auth_event(raw):
    if not isinstance(raw, dict) or raw.get("event_type") not in {"auth_failure", "auth_success"}:
        return None
    expected_status = 401 if raw["event_type"] == "auth_failure" else 200
    if raw.get("method") != "POST" or raw.get("path") not in LOGIN_PATHS:
        return None
    if type(raw.get("status_code")) is not int or raw["status_code"] != expected_status:
        return None
    if not isinstance(raw.get("event_id"), str) or not raw["event_id"]:
        return None
    if not isinstance(raw.get("attempted_username"), str) or not raw["attempted_username"].strip():
        return None
    parse_time(raw.get("occurred_at"))
    return {
        "event_id": raw["event_id"],
        "occurred_at": raw["occurred_at"],
        "attempted_username": raw["attempted_username"],
        "event_type": raw["event_type"],
        "method": raw["method"],
        "path": raw["path"],
        "status_code": raw["status_code"],
        "source": "app",
        "raw": raw,
    }


def detect_repeated_failures(events, observation_id):
    windows = defaultdict(deque)
    alerted_names = set()
    alerts = []
    ordered_events = sorted(events, key=lambda event: (parse_time(event["occurred_at"]), event["event_id"]))
    for event in ordered_events:
        if event["event_type"] != "auth_failure":
            continue
        username = event["attempted_username"]
        occurred_at = parse_time(event["occurred_at"])
        window = windows[username]
        cutoff = occurred_at - timedelta(seconds=WINDOW_SECONDS)
        while window and parse_time(window[0]["occurred_at"]) < cutoff:
            window.popleft()
        window.append(event)
        if len(window) >= THRESHOLD and username not in alerted_names:
            identifier = sha256(f"{observation_id}:{username}".encode("utf-8")).hexdigest()[:20]
            evidence = list(window)
            alerts.append({
                "id": f"auth-{identifier}",
                "attempted_username": username,
                "created_at": event["occurred_at"],
                "failure_count": len(evidence),
                "window_seconds": WINDOW_SECONDS,
                "evidence_event_ids": [item["event_id"] for item in evidence],
                "evidence": evidence,
            })
            alerted_names.add(username)
    return alerts


def build_detection(events, observation, now, invalid_line_count=0):
    selected = []
    seen_ids = set()
    started_at = parse_time(observation["started_at"]) if observation else None
    if observation:
        for event in events:
            occurred_at = parse_time(event["occurred_at"])
            if started_at <= occurred_at <= now and event["event_id"] not in seen_ids:
                selected.append(event)
                seen_ids.add(event["event_id"])
    selected.sort(key=lambda event: (parse_time(event["occurred_at"]), event["event_id"]))
    counts = defaultdict(int)
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)
    for event in selected:
        if event["event_type"] == "auth_failure":
            username = event["attempted_username"]
            counts[username] += int(parse_time(event["occurred_at"]) >= cutoff)
    return {
        "observation": observation,
        "rule": RULE,
        "counts": [
            {"attempted_username": username, "failure_count": count}
            for username, count in sorted(counts.items())
        ],
        "events": selected,
        "alerts": detect_repeated_failures(selected, observation["id"]) if observation else [],
        "evaluated_at": now.isoformat(timespec="microseconds"),
        "invalid_line_count": invalid_line_count,
    }
