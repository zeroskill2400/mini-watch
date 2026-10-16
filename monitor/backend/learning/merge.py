from learning.log_data import read_logs
from learning.normalize_app import normalize_app
from learning.normalize_nginx import normalize_nginx


def load_normalized_events():
    logs = read_logs()
    events = []
    for number, event in enumerate(logs["app"], start=1):
        events.append(normalize_app(event, number))
    for number, line in enumerate(logs["nginx"], start=1):
        events.append(normalize_nginx(line, number))
    return events


if __name__ == "__main__":
    events = load_normalized_events()
    for event in events:
        print(event["id"], event["source"], event["method"], event["path"], event["status_code"])
    print("전체 관측:", len(events))
