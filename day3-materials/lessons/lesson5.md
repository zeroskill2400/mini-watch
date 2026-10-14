IOC(Indicator of Compromise)는 침해 의심을 확인할 때 대조하는 지표이다. 상관분석은 확인된 사용자·시간·순서 같은 조건으로 여러 기록의 관계를 확인하는 일이다.

이번에는 교육용 IP 목록과 감사 기록을 비교하고 실패 뒤 다운로드가 이어진 후보를 찾아보자.
지표값 일치와 사용자·시간 연결의 근거를 구분한다.
<image src="../assets/lesson5.svg">설명용 그림. 지표값 일치와 사용자·시간 연결의 근거를 구분한다.</image>
그림의 입력 자료에서 비교 기준을 거쳐 확인할 결과로 읽어 보자.
- 일치한 원본 ID와 후보가 된 조건을 읽는다.
- 다른 사용자·역순·시간 범위 밖·미확인을 제외한다.
- 실패 2회와 3회 기준에서 결과 차이를 설명한다.
<table_of_contents/>
## 1단계. IOC 값이 일치하는 기록 찾기
`indicators.json`의203.0.113.66은 교육용으로 정한 IP다. 실제 악성 주소를 확인한 목록이 아니며 실습 결과에도 교육용이라고 표시한다.
입력 파일은 monitor/backend/learning/data에 있다. `indicators.json`은 대조할 IP 목록, `audit-raw.json`은 감사 원본 예제, `actor-map.json`은 확인된 사용자 대응표다.
준비된 감사 자료는 계정의 행동을 설명한다. ip 값이 목록에 있는지 확인하고 맞는 기록을 matches에 모으는 함수를 읽어 보자.
`checks.py` — 준비된 IOC 대조 함수
```python
def find_ioc_matches(events, indicators):
    matches = []
    for event in events:
        if event["ip"] in indicators:
            matches.append(event)
    return matches

```
in은 해당 값이 목록 안에 있는지 확인한다. matches.append(event)는 일치한 기록 자체를 남겨 원본 ID를 다시 읽을 수 있게 한다.
일치값과 의미 확인하기
1. `indicators.json`에서 예제 IP 한 개를 확인한다.
2. 감사 자료에서 IP가 일치한 기록이 곧 침해 확정인지 판단한다.
<details>
<summary>해설</summary>
	값 일치는 추가로 검토할 신호다. 정상접속·공유IP·오래된지표 등 다른 설명이 있을 수 있으므로 IOC 일치만으로 침해를 확정하지 않는다.
</details>
## 2단계. 같은 사용자와 순서를 확인하기
준비된 대응표는 user-17과 mira@example.test를 employee-17로 연결한다. 이 확인된 공통 사용자 안에서 로그인 실패가 다운로드보다 앞에 있고 시간차가 5분 이내인지 검사한다.
UTC(협정세계시)는 이 예제의 시각 기준이다. 같은 UTC 시각끼리 차이를 비교하며 한국 현지 시각으로 바꿔 계산할 필요는 없다.
<table header-row="true" fit-page-width="true">
<tr>
<td>원본 ID</td>
<td>시각(UTC)</td>
<td>공통 사용자</td>
<td>행동</td>
</tr>
<tr>
<td>a1</td>
<td>00:00:00</td>
<td>employee-17</td>
<td>로그인 실패</td>
</tr>
<tr>
<td>a2</td>
<td>00:00:30</td>
<td>employee-17</td>
<td>로그인 실패</td>
</tr>
<tr>
<td>a4</td>
<td>00:02:00</td>
<td>employee-17</td>
<td>다운로드</td>
</tr>
</table>
a1에서a4는 120초, a2에서a4는 90초이다. 둘 모두 먼저 일어났고 5분 이내이므로 실패 2회 뒤 다운로드라는 조건에 맞는다.
`checks.py` — 준비된 순서 규칙
```python
from learning.support import failures_before

def find_related_downloads(events, max_seconds=300):
    related = []
    for event in events:
        if event["kind"] == "download":
            failures = failures_before(event, events, max_seconds)
            if len(failures) >= 2:
                related.append({"download": event, "failures": failures})
    return related

```
failures\_before는 확인된 같은 사용자의 먼저 일어난 실패 중 300초 이내인 기록을 골라 주는 준비 함수다. 시간 파서를 새로 만들지 않고 여기서는 len(failures) >= 2 조건을 읽는다.
연결 조건 예상하기
1. 실패a1·a2와 다운로드a4의 사용자·순서·시간차를 확인한다.
2. 실패가 한 번뿐이면 이 규칙에 맞는지 판단한다.
<details>
<summary>해설</summary>
	실패 2회 이상이라는 조건이 있으므로 한 번으로는 맞지 않는다. 같은 IP라는 사실도 이 조건의 사용자 확인 근거를 대신하지 않는다.
</details>
## 3단계. 결과와 제외된 기록 대조하기
같은 저장소의 Windows CMD에서 준비된 `lesson5.py`를 실행한다. 사용자 대응표와 날짜 읽기는 준비 코드로 처리한다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson5
```
```plain text
IOC 근거 ['a1', 'a2', 'a3', 'a4', 'a8']
연결 employee-17 ['a1', 'a2'] -> a4
```
IOC 일치 5건과 사용자·시간 후보 1건은 다른 규칙의 결과다. 같은 기록이 여러 규칙에 들어가므로 두 숫자를 더해 사건 6건이라고 말하지 않는다.
<table header-row="true" fit-page-width="true">
<tr>
<td>기록</td>
<td>순서 규칙에서 제외하는 이유</td>
</tr>
<tr>
<td>a5</td>
<td>다른 사용자 employee-23</td>
</tr>
<tr>
<td>a6</td>
<td>관련 실패에서 5분을 넘은 다운로드</td>
</tr>
<tr>
<td>a7</td>
<td>실패보다 먼저 일어난 다운로드</td>
</tr>
<tr>
<td>a8</td>
<td>IP는 같아도 공통 사용자 미확인</td>
</tr>
</table>
후보와 제외 근거 말하기
1. a8이 IOC에는 있고 사용자·시간 후보에는 없는 이유를 말한다.
2. a6의 시간을a1·a2와 대조해 5분 범위를 확인한다.
<details>
<summary>해설</summary>
	a8은 값이 일치하므로 IOC 결과에 남지만 대응표에 사용자 근거가 없다. a6은00:08:00이므로 a1·a2 뒤 5분 범위를 넘는다. 서로 다른 조건을 읽어야 결과를 설명할 수 있다.
</details>
## 4단계. 실패 횟수 조건 바꾸기
VS Code에서 `checks.py`의 find\_related\_downloads 함수 안 len(failures) >= 2를 len(failures) >= 3으로 바꾸고 Ctrl+S로 저장한다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson5
```
```plain text
IOC 근거 ['a1', 'a2', 'a3', 'a4', 'a8']
연결 결과 없음
```
같은 자료에서 실패가 두 번뿐이므로 3회 조건에는 맞지 않는다. IOC 대조 조건은 수정하지 않았으므로 일치 ID는 그대로다.
확인 뒤 len(failures) >= 2로 돌리고 저장한다. 마지막 화면은 실패 2회 조건을 사용한다.
## 챙겨 가기 — 연결할 근거가 있는지 확인하기
<table header-row="true" fit-page-width="true">
<tr>
<td>개념</td>
<td>가져갈 판단</td>
</tr>
<tr>
<td>IOC</td>
<td>지표값 일치와 침해 확정을 구분한다.</td>
</tr>
<tr>
<td>상관분석</td>
<td>확인된 같은 사용자·행동 순서·시간 범위를 모두 확인한다.</td>
</tr>
<tr>
<td>근거</td>
<td>원본 ID와 제외 사례를 읽어 후보가 된 이유를 설명한다.</td>
</tr>
</table>
다음에는 준비된 API와 화면에 이 결과를 표시한다. 실제 HTTP·합성 PCAP·교육용 감사 자료의 출처는 끝까지 구분한다.
## 확인문제
**확인문제 1.** IOC가 무엇인가?
<details>
<summary>정답과 해설</summary>
	침해 의심을 검토할 때 대조하는 지표다. 이 시간의 IP 목록은 교육용 예제다.
</details>
**확인문제 2.** 203.0.113.66을 실제 악성 주소로 확인했는가?
<details>
<summary>정답과 해설</summary>
	아니다. 실습을 위해 정한 예제값이며 실제 평판 조회 결과가 아니다.
</details>
**확인문제 3.** IOC에 일치한 원본 ID는 무엇인가?
<details>
<summary>정답과 해설</summary>
	a1·a2·a3·a4·a8이다. 일치한 원본 기록을 근거로 남긴다.
</details>
**확인문제 4.** IP가 같으면 같은 사용자로 연결하는가?
<details>
<summary>정답과 해설</summary>
	아니다. 확인된 대응표가 필요하며 공유 IP 등 다른 가능성도 있다.
</details>
**확인문제 5.** 순서 규칙의 세 가지 주요 연결 조건은 무엇인가?
<details>
<summary>정답과 해설</summary>
	확인된 같은 사용자, 실패가 다운로드보다 먼저 일어남, 각 실패와 다운로드의 차이가 5분 이내임이다.
</details>
**확인문제 6.** a1과a2가a4의 실패 근거인 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	같은 employee-17이고 각각 120초·90초 전에 일어나 5분 범위에 들며 실패 2회를 채운다.
</details>
**확인문제 7.** a5·a6·a7은 왜 제외되는가?
<details>
<summary>정답과 해설</summary>
	a5는 다른 사용자, a6은 시간 범위 밖, a7은 실패보다 먼저 일어난 다운로드이기 때문이다.
</details>
**확인문제 8.** a8은 IOC에 있는데 순서 규칙에는 왜 없는가?
<details>
<summary>정답과 해설</summary>
	IP 값은 일치하지만 공통 사용자 대응 관계가 확인되지 않았다.
</details>
**확인문제 9.** 실패 조건을 2에서 3으로 바꾸면 무엇이 달라지는가?
<details>
<summary>정답과 해설</summary>
	같은 자료의 실패가 두 번뿐이므로 사용자·시간 후보가 없어진다. IOC 조건은 그대로라 ID도 그대로다.
</details>
**확인문제 10.** IOC5건과 연결 후보 1건을 사건 6건이라고 더할 수 있는가?
<details>
<summary>정답과 해설</summary>
	없다. 서로 다른 규칙 결과이고 같은 원본 기록이 겹칠 수 있다. 실제 침해 사건 수도 아니다.
</details>
## 되새김 문제
다음 질문에 말로 답할 수 있으면 이번 시간을 제대로 이해한 것이다.
- IOC에 일치했다는 사실만으로 침해를 확정하지 못하는 이유는 무엇인가?
- 같은 사용자·순서·5분 범위를 모두 확인해야 하는 이유는 무엇인가?
- a8이 두 규칙에서 다르게 처리되는 이유는 무엇인가?
다음 활동에서도 출처와 비교 기준을 확인하며 근거를 읽어 보자.