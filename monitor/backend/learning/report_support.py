from learning.support import capture_summary, audit_events, read_json
from learning.checks import traffic_exceeded, find_ioc_matches, find_related_downloads


def assemble_report(events, count, threshold=10):
    view_ids = [e["id"] for e in events if e["method"] == "GET" and e["path"] == "/" and e["status_code"] == 200 and e["kind"] == "post_list"]
    normal = capture_summary("normal.pcap")
    observed = capture_summary("observed.pcap")
    audit = audit_events()
    matches = find_ioc_matches(audit, read_json("indicators.json"))
    related = find_related_downloads(audit)
    related_ids = []
    for group in related:
        related_ids.extend(e["id"] for e in group["failures"])
        related_ids.append(group["download"]["id"])
    return {"ready": True, "results": [
        {"rule": "HTTP 조회 규칙", "source": "실제 HTTP", "observed": count,
         "basis": f"새 관찰 이후·첫 결과 기준60초·GET /·200·post_list / 기준 {threshold}회 이상",
         "triggered": count >= threshold, "evidence": view_ids,
         "reason": "일반 서비스의 목록 조회 횟수다. 사용자/IP별 판정이나 공격 확정은 아니다."},
        {"rule": "패킷 바이트 비교", "source": "합성 PCAP", "observed": observed["bytes"],
         "basis": f"각 파일 첫 패킷부터5초 / 정상 {normal['bytes']}bytes의2배 초과",
         "triggered": traffic_exceeded(normal, observed), "evidence": ["normal.pcap", "observed.pcap"],
         "reason": f"정상{normal['packets']}개·관찰{observed['packets']}개의 저장된 패킷이다. HTTP 요청 수가 아니다."},
        {"rule": "IOC 대조", "source": "교육용 감사 자료", "observed": len(matches),
         "basis": "교육용 목록203.0.113.66과 IP값 일치",
         "triggered": bool(matches), "evidence": [e["id"] for e in matches],
         "reason": "예제 지표와 일치한 기록이다. 이 주소를 실제 악성 주소로 확인한 결과가 아니다."},
        {"rule": "사용자·시간 연결", "source": "교육용 감사 자료", "observed": len(related),
         "basis": "확인된 동일사용자 / 실패2회 이상 뒤5분 이내 다운로드",
         "triggered": bool(related), "evidence": list(dict.fromkeys(related_ids)),
         "reason": "예제 감사 자료 안에서만 순서·사용자·시간을 연결한다. 다른 자료와 한 사건으로 합치지 않는다."}
    ]}
