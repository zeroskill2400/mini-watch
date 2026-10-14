from learning.merge import load_normalized_events


def build_report():
    return {"ready": False, "message": "정규화와 집계 함수를 완성한 뒤 다시 불러오세요."}


if __name__ == "__main__":
    report = build_report()
    if report["ready"]:
        print("전체 관측:", report["total_count"])
        print("오류 관측:", report["error_count"])
    else:
        print(report["message"])
