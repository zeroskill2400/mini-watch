from learning.support import audit_events, read_json
from learning.checks import find_ioc_matches, find_related_downloads

events = audit_events()
matches = find_ioc_matches(events, read_json("indicators.json"))
print("IOC 근거", [event["id"] for event in matches])
related = find_related_downloads(events)
for group in related:
    print("연결", group["download"]["actor"], [e["id"] for e in group["failures"]], "->", group["download"]["id"])
if not related:
    print("연결 결과 없음")
