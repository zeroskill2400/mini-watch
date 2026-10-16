from learning.merge import load_normalized_events


def build_report():
    events = load_normalized_events()
    errors = []
    for event in events:
        if event["status_code"] >= 400:
            errors.append(event)
    return {
        "ready": True,
        "events": events,
        "total_count": len(events),
        "error_count": len(errors),
    }


if __name__ == "__main__":
    report = build_report()
    if report["ready"]:
        print("전체 관측:", report["total_count"])
        print("오류 관측:", report["error_count"])
    else:
        print(report["message"])
