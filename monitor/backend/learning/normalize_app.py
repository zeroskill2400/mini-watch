def normalize_app(event, number):
    return {
        "id": f"app-{number}",
        "source": "app",
        "method": event["method"],
        "path": event["path"],
        "status_code": int(event["status_code"]),
        "raw": event,
    }


if __name__ == "__main__":
    from learning.log_data import read_logs

    logs = read_logs()
    if not logs["app"]:
        print("앱 원본이 없습니다. 일반 게시판에서 로그인하거나 목록을 열어 보세요.")
    for number, raw in enumerate(logs["app"], start=1):
        event = normalize_app(raw, number)
        print(event["source"], event["method"], event["path"], event["status_code"])
