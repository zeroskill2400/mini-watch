근거는 판단에 사용한 원본 자료와 조건이다. 오늘의 결과는 어떤 기록과 조건 때문에 후보로 표시됐는지 읽을 수 있는 감시 화면이다.

앞에서 만든 조회 규칙과 준비된 패킷·감사 함수를 연결하고 실제 general의 기록으로 기준 변화를 확인해 보자.
실제 HTTP와교육용근거를구분한감시결과를완성한다.
<image src="../assets/lesson6.svg">설명용 그림. 실제 HTTP와교육용근거를구분한감시결과를완성한다.</image>
그림의 입력 자료에서 비교 기준을 거쳐 확인할 결과로 읽어 보자.
- 앞에서 적용한 함수와 준비 API·화면을 연결한다.
- HTTP 기준10·20과 새 관찰의 결과 차이를 확인한다.
- 후보의 근거와 추가 확인할 사실을 설명한다.
<table_of_contents/>
## 1단계. 연결할 함수와 기본 기준 확인하기
같은 mini-watch-m5d3 저장소에서 작업한다. count\_views는 네 조건에 맞는 조회만 세도록 완성했고, 패킷은 2배·실패는 2회 기준으로 돌려놓은 상태가 출발점이다.
출발 상태 확인하기
1. 아래 명령을 차례대로 실행한다.
2. 아래 기대 결과와 비교한다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson3
```
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson4
```
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson5
```
<table header-row="true" fit-page-width="true">
<tr>
<td>실습</td>
<td>확인할 결과</td>
</tr>
<tr>
<td>lesson3</td>
<td>정상4 False / 비교12 True</td>
</tr>
<tr>
<td>lesson4 마지막</td>
<td>관찰1220bytes / 기준초과True</td>
</tr>
<tr>
<td>lesson5</td>
<td>IOC 근거 5개 / employee-17의a1·a2→a4</td>
</tr>
</table>
<details>
<summary>조회 규칙을 완성하지 못했다면</summary>
	`checks.py`의 count\_views 함수만 아래 내용으로 바꾸고 저장한다. 다른 준비 함수는 그대로 둔다.
	`checks.py` — count\_views 함수
	```python
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

	```
</details>
## 2단계. 결과를 준비된 보고서에 연결하기
`report.py`는 규칙 결과를 감시 API로 돌려주는 파일이다. assemble\_report는 패킷·감사 계산과 출처·근거 표시를 묶은 준비 함수이므로 날짜·DB·화면 코드를 새로 작성하지 않는다.
VS Code에서 monitor/backend/learning/report.py를 열어 전체 내용을 아래 코드로 바꾸고 Ctrl+S로 저장한다.
`monitor/backend/learning/report.py` — 전체 코드
```python
from learning.checks import count_views
from learning.report_support import assemble_report


def build_report(events, threshold=10):
    count = count_views(events)
    return assemble_report(events, count, threshold)

```
count는 이번 조회 규칙이 계산한 횟수이고 threshold는 화면에서 받은 경계값이다. 실제 HTTP 횟수를 준비된 출처별 보고서에 넣어 반환한다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml restart monitor-api
```
API가 새 함수를 읽도록 한 번 재시작한다. DB 서비스와 볼륨을 삭제하지 않으므로 기존 계정·게시글·요청 기록은 남는다.
## 3단계. 실제 목록 조회로 새 관찰 만들기
감시 화면의 분석 영역에서 시작하자.
1. 감시 화면 http://localhost:8082에 로그인한다.
2. 새 관찰 시작을 누르고 HTTP 조회 기준이 10인지 확인한다.
새 관찰 시작은 현재 DB의 마지막 ID를 읽기만 한다. 이후 ID이면서 첫 결과를 불러온 시각의 최근 60초인 기록만 실제 HTTP 집계에 포함한다.
처음 결과를 불러온 뒤에는 그 기준시각과 60초 구간을 유지한다. 근거를 읽고 기준을 바꿔 다시 불러와도 같은 구간을 비교하며, 새 관찰 시작을 누르면 새 구간을 사용한다.
Windows CMD에서 아래 준비 도구를 실행한다. 일반 API의 목록 주소를 12회 읽어 실제 수집 기록을 만든다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.make_requests
```
```plain text
일반 목록12회 조회 완료
```
이 도구는 general-api의 목록을 실제로 읽어 요청 기록을 만든다. 글을 작성하거나 삭제하지 않는다.
최근 구간의 결과 읽기
1. 조회 완료 뒤 1분 안에 감시 화면의 분석 결과 불러오기를 누른다.
2. HTTP 조회 규칙 카드의 출처·관찰값·기준·후보 여부를 읽는다.
```plain text
HTTP 조회 규칙
출처: 실제 HTTP
관찰값: 12 / 검토 후보
기준: 새 관찰 이후·첫 결과 기준60초·GET /·200·post_list / 기준10회 이상
```
같은 구간에 다른 목록 조회도 발생하면 12보다 커질 수 있다. 오래 기다리면 기록이 60초 범위에서 빠지므로 다른 목록 조회 없이 실행하고 바로 결과를 읽는다.
<details>
<summary>HTTP0건이거나 연결 전 안내가 나오면</summary>
	0건이면 새 관찰 시작 → 목록 12회 조회 → 1분 안에 결과 읽기를 다시 한다. 연결 전 안내가 나오면 `report.py` 저장과 monitor-api 재시작을 확인한다. 일반 출력에는 있는데 감시 DB에 없으면 general-api 실행 로그에서 전송 실패를 확인한다.
</details>
## 4단계. 같은 관찰 구간에서 기준 바꾸기
HTTP 경계만 바꾸어 보자.
1. HTTP 조회 기준을 20으로 바꾼다.
2. 분석 결과 불러오기를 눌러 같은 관찰 구간의 결과를 비교한다.
```plain text
HTTP 관찰값: 12 / 기준 미해당
패킷·IOC·사용자시간: 각자 기존 기준 유지
```
기준 20은 HTTP 카드에만 적용된다. 조회량 12는 그대로이고 다른 자료의 패킷 2배·실패 2회 조건은 바뀌지 않는다.
## 5단계. 출처별 근거를 펼쳐 읽기
세 종류의 출처를 구분하자.
1. 네 카드의 출처가 실제 HTTP·합성 PCAP·교육용 감사 자료인지 확인한다.
2. 각 카드의 근거 보기를 펼쳐 원본 ID나 파일 이름을 읽는다.
<table header-row="true" fit-page-width="true">
<tr>
<td>결과</td>
<td>관찰값·조건</td>
<td>원본 근거</td>
</tr>
<tr>
<td>실제 HTTP</td>
<td>첫 결과 기준60초·목록 조회12회·10회 기준 후보/20회 기준 미해당</td>
<td>http-로 시작하는 이번 기록 ID</td>
</tr>
<tr>
<td>합성 PCAP</td>
<td>각 파일5초·1220bytes·244의2배 초과</td>
<td>normal.pcap·observed.pcap</td>
</tr>
<tr>
<td>교육용 IOC</td>
<td>예제 IP 일치5건</td>
<td>a1·a2·a3·a4·a8</td>
</tr>
<tr>
<td>교육용 사용자·시간</td>
<td>같은 사용자의 실패2회 뒤5분 이내 다운로드1건</td>
<td>a1·a2·a4</td>
</tr>
</table>
HTTP의 60초, PCAP의 5초, 감사의 5분은 서로 다른 조건이다. 실제 HTTP에는 사용자·IP가 없으므로 교육용 사용자의 행동으로 이어 붙이지 않는다.
결과의 이유 설명하기
1. 각 결과가 이렇게 표시된 조건과 원본 근거를 한 가지씩 말한다.
2. 이 결과에서 추가로 확인할 사실을 정한다.
<details>
<summary>설명 예</summary>
	HTTP는10 기준에서 후보였고20에서는 같은12회가 미해당이다. 후보가 된 조회량의 맥락을 알기 위해 누가 어떤 작업을 했는지 추가로 확인한다. PCAP는 양이 큰 이유, 감사 예제는 대응표와 다운로드 맥락을 확인해야 한다. 지금은 근거를 읽고 검토하는 단계이다.
</details>
## 6단계. 원본 기록을 남겨 두고 다시 관찰하기
과거 자료를 지우지 않고 새로 관찰하자.
1. 새 관찰 시작을 다시 누른다.
2. 일반 목록을 새로 조회하지 않고 분석 결과 불러오기를 누른다.
```plain text
HTTP 관찰값: 0 / 기준 미해당
```
이전 기록은 DB에 남아 있지만 새 시작 ID보다 앞이므로 이번 집계에서 제외된다. 기록 불러오기 표에서는 이전 행을 계속 확인할 수 있다.
## 완료 확인 — 화면을 보고 이유 설명하기
- general의 행동 → 전송 전 JSON → 감시 DB → 감시 표의 수집 흐름을 설명한다.
- 정규화가 없는 사용자·IP나 같은 사건을 만들지 않는 이유를 말한다.
- 실제 HTTP12가10·20에서 달라지는 판정을 조건과 함께 설명한다.
- 패킷 바이트와 앱 요청 횟수의 단위·관찰 구간을 구분한다.
- IOC 값 일치와 동일 사용자·순서·5분 연결을 각 원본 ID로 설명한다.
- 검토 후보에서 추가로 확인할 사실을 말하고 자동 조치와 구분한다.
이 근거를 바탕으로 다음 일차에서 탐지의 품질을 평가하고 사건 정리·사람 승인으로 이어간다. 대응 조치·복구는 그 다음 단계에서 다룬다.
## 확인문제
**확인문제 1.** 최종 화면이 후보 여부와 함께 보여 주어야 할 것은 무엇인가?
<details>
<summary>정답과 해설</summary>
	출처·관찰값·기준·원본 근거·판단 한계를 보여 주어야 이유를 설명할 수 있다.
</details>
**확인문제 2.** count와threshold는 각각 무엇인가?
<details>
<summary>정답과 해설</summary>
	count는 조건에 맞는 목록 조회 횟수이고 threshold는 화면에서 받은 후보 경계값이다.
</details>
**확인문제 3.** API만 재시작하면 기존 DB 기록은 지워지는가?
<details>
<summary>정답과 해설</summary>
	아니다. DB 서비스나 볼륨을 삭제하지 않으며 API가 수정한 함수를 새로 읽는 것이다.
</details>
**확인문제 4.** 새 관찰 시작은 DB에서 무엇을 하는가?
<details>
<summary>정답과 해설</summary>
	현재 마지막 ID를 읽고 그 뒤 기록을 세도록 한다. 행을 삭제하지 않는다.
</details>
**확인문제 5.** 실제 목록 12회를 어떻게 만드는가?
<details>
<summary>정답과 해설</summary>
	준비된 make\_requests가 general-api의 목록을 실제로 GET 조회하여 수집 기록을 만든다.
</details>
**확인문제 6.** 같은 관찰에서 기준을 바꿀 때 시간이 지나면 조회 12건도 사라지는가?
<details>
<summary>정답과 해설</summary>
	첫 결과 조회시각의 60초 구간을 유지하므로 같은 12건과 원본ID를 비교한다. 새 관찰 시작을 눌렀을 때 새 ID와 기준시각으로 다시 관찰한다.
</details>
**확인문제 7.** HTTP 기준 20으로 바꾸면 다른 카드도20 기준이 되는가?
<details>
<summary>정답과 해설</summary>
	아니다. HTTP 경계만 변하고 PCAP2배·감사 실패 2회 같은 각자 조건은 유지된다.
</details>
**확인문제 8.** HTTP·PCAP·감사 후보를 같은 침해 사건이라고 묶을 수 있는가?
<details>
<summary>정답과 해설</summary>
	없다. 실제 HTTP와 합성·교육용 자료는 독립 출처이며 연결할 사용자나 사건 근거가 확인되지 않았다.
</details>
**확인문제 9.** 새 관찰 뒤 0건인데 기록 표에 이전 행이 있는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	DB 원본은 남겨 두고 새 시작 ID와 최근 구간을 기준으로 이번 집계에서만 제외했기 때문이다.
</details>
**확인문제 10.** 오늘 완성한 화면에서 자동 차단까지 끝났는가?
<details>
<summary>정답과 해설</summary>
	아니다. 근거 있는 검토 후보를 표시했다. 사건 검토·승인·실제 조치·복구는 뒤에서 다룬다.
</details>
## 되새김 문제
다음 질문에 말로 답할 수 있으면 이번 시간을 제대로 이해한 것이다.
- 기준10·20에서 같은 HTTP 조회 12회의 결과가 달라지는 이유는 무엇인가?
- 왜 HTTP·PCAP·감사 자료의 후보를 같은 사건이라고 합칠 수 없는가?
- 후보를 다음 사건 검토로 넘길 때 어떤 근거와 추가 확인이 필요한가?
다음 활동에서도 출처와 비교 기준을 확인하며 근거를 읽어 보자.