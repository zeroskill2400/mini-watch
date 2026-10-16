def normalize_nginx(line, number):
    prefix, request_text, suffix = line.split('"', 2)
    method, path, protocol = request_text.split()
    return {
        "id": f"nginx-{number}",
        "source": "nginx",
        "method": method,
        "path": path,
        "status_code": int(suffix.split()[0]),
        "raw": line,
    }


if __name__ == "__main__":
    from learning.log_data import read_logs

    logs = read_logs()
    if not logs["nginx"]:
        print("Nginx 원본이 없습니다. 일반 게시판에서 로그인하거나 목록을 열어 보세요.")
    for number, line in enumerate(logs["nginx"], start=1):
        event = normalize_nginx(line, number)
        print(event["source"], event["method"], event["path"], event["status_code"])
