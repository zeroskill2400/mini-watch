from learning.support import failures_before


def count_views(events):
    total = 0
    for event in events:
        valid_method = event["method"] == "GET"
        # >>>>> 수정 시작 (목록 조회 조건과 횟수) >>>>>
        valid_path = event["path"] == "/"
        valid_status = event["status_code"] == 200
        valid_kind = event["kind"] == "post_list"
        if valid_method and valid_path and valid_status and valid_kind:
            total += 1
        # <<<<< 수정 끝 <<<<<
    return total


def traffic_exceeded(normal, observed, multiple=2):
    return observed["bytes"] > normal["bytes"] * multiple


def find_ioc_matches(events, indicators):
    matches = []
    for event in events:
        if event["ip"] in indicators:
            matches.append(event)
    return matches


def find_related_downloads(events, max_seconds=300):
    related = []
    for event in events:
        if event["kind"] == "download":
            failures = failures_before(event, events, max_seconds)
            if len(failures) >= 2:
                related.append({"download": event, "failures": failures})
    return related
