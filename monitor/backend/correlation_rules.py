from hashlib import sha256

from detection_rules import parse_time

REQUIRE_SAME_HASH = True
MAX_CASES = 100


def correlation_status():
    return {
        "require_same_hash": REQUIRE_SAME_HASH,
        "label": "같은 서버·파일·해시로 연결" if REQUIRE_SAME_HASH else "비교용 불완전 기준: 같은 서버·파일만 연결",
        "identity_note": "인증된 계정은 실제 정상 로그인 ID로 연결합니다. 실패 입력 이름이 같아도 동일인 증거는 아닙니다.",
    }


def latest_write_id(writes, sensor):
    sensor_time = parse_time(sensor["occurred_at"])
    raw_sensor = sensor["raw"]
    candidates = [
        write for write in writes
        if (write["raw"]["server_id"], write["raw"]["target_path"]) == (raw_sensor["server_id"], raw_sensor["target_path"])
        and parse_time(write["occurred_at"]) <= sensor_time
    ]
    if not candidates:
        return None
    latest_time = max(parse_time(write["occurred_at"]) for write in candidates)
    latest = [write for write in candidates if parse_time(write["occurred_at"]) == latest_time]
    return latest[0]["event_id"] if len(latest) == 1 else None


def build_cases(writes, file_events, auth_events, alerts, observation, limit=MAX_CASES):
    if not observation:
        return []
    successes = {event["event_id"]: event for event in auth_events if event["event_type"] == "auth_success"}
    sensor_write_ids = {sensor["event_id"]: latest_write_id(writes, sensor) for sensor in file_events} if REQUIRE_SAME_HASH else {}
    cases = []
    for write in reversed(writes):
        raw_write = write["raw"]
        success = successes.get(raw_write["auth_event_id"])
        if not success:
            continue
        authenticated_username = success["raw"].get("authenticated_username")
        if authenticated_username != raw_write["authenticated_username"]:
            continue
        if parse_time(success["occurred_at"]) > parse_time(write["occurred_at"]):
            continue
        related_alert = next((alert for alert in alerts if alert["attempted_username"] == authenticated_username), None)
        for sensor in reversed(file_events):
            raw_sensor = sensor["raw"]
            if (raw_write["server_id"], raw_write["target_path"]) != (raw_sensor["server_id"], raw_sensor["target_path"]):
                continue
            hash_matches = raw_write["sha256"] == raw_sensor["sha256"]
            if REQUIRE_SAME_HASH and (not hash_matches or sensor_write_ids.get(sensor["event_id"]) != write["event_id"]):
                continue
            identifier = sha256(f'{observation["id"]}:{write["event_id"]}:{sensor["event_id"]}'.encode()).hexdigest()[:24]
            evidence = [success, write, sensor]
            if related_alert:
                evidence.extend(related_alert["evidence"])
            unique_evidence = list({event["event_id"]: event for event in evidence}.values())
            cases.append({
                "id": f"case-{identifier}",
                "username": authenticated_username,
                "server_id": raw_write["server_id"],
                "target_path": raw_write["target_path"],
                "write": write,
                "sensor": sensor,
                "auth_success": success,
                "related_alert": related_alert,
                "hash_matches": hash_matches,
                "evidence": unique_evidence,
            })
            if limit is not None and len(cases) == limit:
                return cases
    return cases
