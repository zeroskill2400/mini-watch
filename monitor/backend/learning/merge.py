from learning.classroom_data import read_case
from learning.normalize_app import normalize_app
from learning.normalize_nginx import normalize_nginx


def load_normalized_events():
    return []


if __name__ == "__main__":
    events = load_normalized_events()
    for event in events:
        print(event["id"], event["source"], event["method"], event["path"], event["status_code"])
    print("전체 관측:", len(events))
