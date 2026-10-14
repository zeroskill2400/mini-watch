from learning.support import read_json, normalize_audit
raw = read_json("audit-raw.json")[0]
event = normalize_audit(raw)
print(raw["person"], "->", event["actor"])
print("원본ID", raw["id"], "공통ID", event["id"])
print(event["source"], event["kind"], event["occurred_at"])
http = read_json("http-example.json")
sentry = read_json("sentry-example.json")
print(http["request_id"], sentry["request_id"])
print(http["status_code"], sentry["exception"])
