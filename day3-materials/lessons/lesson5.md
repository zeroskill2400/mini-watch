앱과 Nginx 로그가 한 목록에 모였다. 이제 “오류 응답을 기록한 행은 몇 개인가?”를 확인하자. 원래는 JSON과 문자열이었지만, 정규화한 뒤에는 둘 다 숫자인 `status_code`로 비교할 수 있다.

이번에는 같은 조건으로 오류 관측을 세고, 전체 로그와 계산한 숫자를 함께 돌려주는 함수를 만든다. 완료 결과는 전체 관측 4, 오류 관측 2다. 원본을 다시 만들거나 웹 화면 코드를 새로 쓰지 않는다.
완성 모습: 전체 네 행을 보존하면서 오류를 기록한 두 행을 센다.
<image src="../assets/lesson5.svg">같은 상태 조건으로 오류 관측 세기 — 동작을 설명하는 그림이다.</image>
왼쪽의 네 행 중 상태가 404인 두 행만 가운데의 조건에 맞는다. 오른쪽 결과에는 오류 수뿐 아니라 전체 네 행도 남는다. 나중에 화면에서 전체 로그와 오류 로그를 모두 볼 수 있게 하려는 것이다.
```plain text
mini-watch-m5d3
└─ monitor
   └─ backend
      └─ learning
         ├─ normalize_app.py
         ├─ normalize_nginx.py
         ├─ merge.py            두 출처 합치기
         ├─ report.py           이번에 작성
         └─ data
            └─ case.json        같은 실습 원본
```
<table_of_contents/>
## 1단계. 합친 로그와 실행 위치 확인하기
VS Code에서 지금 쓰는 `mini-watch-m5d3` 폴더를 연다. Docker Desktop과 제공 서비스는 실행해 둔다. 이 페이지의 명령은 두 Compose 파일이 있는 프로젝트 폴더의 Windows CMD에서 실행한다.
실행 위치 확인
1. 탐색기에 `general`, `monitor`, `compose-general.yaml`, `compose-monitor.yaml`이 보이는지 확인한다.
2. 터미널 → 새 터미널을 열고, + 옆 화살표에서 Command Prompt를 선택한다.
프로젝트 폴더의 Windows CMD
```plain text
cd /d C:\work\mini-watch-m5d3
```
다른 위치에 받은 폴더를 사용 중이면 위 경로를 그 실제 위치로 바꾼다. 탐색기에서 `monitor` → `backend` → `learning` → `data`를 열면 `case.json`이 있다. 이 파일의 앱 두 행과 Nginx 두 행을 계속 사용하며, 정상적으로 준비돼 있으면 다시 수집하지 않는다.
<details>
<summary>서비스가 꺼져 있거나 `case.json`이 없으면</summary>
	프로젝트 폴더의 같은 CMD에서 제공된 시작 명령을 실행한다. 준비된 수집기가 목록과 없는 경로를 한 번씩 요청해 실습 원본을 만든다. 실행 중에는 게시판을 조작하지 않는다.
	프로젝트 폴더의 Windows CMD
	```plain text
start-class.cmd
	```
	완료 뒤 `learning` → `data`에 `case.json`이 생겼는지 확인하고 이 페이지의 실행으로 돌아온다. 이 명령은 원본 묶음을 새로 준비하므로 이미 파일이 있을 때 반복할 필요는 없다. 실패하면 오류 문구를 강사와 확인하고 DB나 기존 작업 파일을 지우지 않는다.
</details>
같은 `learning` 폴더의 `merge.py`에는 `load_normalized_events()`가 있다. 이 함수가 두 원본을 정규화해 네 행을 돌려준다. 이번에는 그 결과를 그대로 받아 `report.py`에서 조건을 비교한다.
<details>
<summary>앞 파일이 없거나 전체 관측이 4가 아니면</summary>
	전체 관측이 2라면 앱만 합치는 중간 파일, 0이라면 비어 있는 시작 틀일 수 있다. 아래 세 파일로 두 출처를 합치는 상태를 확인한다. 원본 묶음은 다시 만들지 않는다.
	정규화 파일이 없거나 함수 안에 `return None`만 남아 있으면 아직 시작 틀이다. 탐색기의 `monitor` → `backend` → `learning`에서 아래 이름의 파일을 열고 각각 전체 내용을 저장한다. 이미 완성했다면 바꾸지 않는다.
	`normalize_app.py` — 복구용 파일 전체
	```python
def normalize_app(event, number):
    return {
        "id": f"app-{number}",
        "source": "app",
        "time": None,
        "method": event["method"],
        "path": event["path"],
        "status_code": int(event["status_code"]),
        "raw": event,
    }
	```
	`normalize_nginx.py` — 복구용 파일 전체
	```python
from datetime import datetime, timezone


def normalize_nginx(line, number):
    prefix, request_text, suffix = line.split('"', 2)
    method, path, protocol = request_text.split()
    time_text = prefix.split("[", 1)[1].split("]", 1)[0]
    parsed_time = datetime.strptime(time_text, "%d/%b/%Y:%H:%M:%S %z")
    return {
        "id": f"nginx-{number}",
        "source": "nginx",
        "time": parsed_time.astimezone(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "status_code": int(suffix.split()[0]),
        "raw": line,
    }
	```
	`merge.py` — 복구용 파일 전체
	```python
from learning.classroom_data import read_case
from learning.normalize_app import normalize_app
from learning.normalize_nginx import normalize_nginx


def load_normalized_events():
    case = read_case()
    events = []
    for number, event in enumerate(case["app"], start=1):
        events.append(normalize_app(event, number))
    for number, line in enumerate(case["nginx"], start=1):
        events.append(normalize_nginx(line, number))
    return events


if __name__ == "__main__":
    events = load_normalized_events()
    for event in events:
        print(event["id"], event["source"], event["method"], event["path"], event["status_code"])
    print("전체 관측:", len(events))
	```
	저장한 뒤 이 페이지의 실행 명령을 다시 입력한다. 새 패키지 설치나 DB 초기화는 하지 않는다.
</details>
## 2단계. 오류 응답을 기록한 행 세기
HTTP 상태는 요청을 처리한 결과를 나타낸다. 이번에는 400번대와 500번대 상태를 오류 응답으로 보고 `status_code >= 400`을 조건으로 사용한다. 404는 없는 경로를 요청했을 때 받은 응답이다.
계산하는 작은 파일부터 실행하기
1. `monitor` → `backend` → `learning`에서 `report.py`를 연다. 아래 전체 코드로 바꾸고 Ctrl+S로 저장한다.
2. 같은 프로젝트 폴더의 CMD에서 실행 명령을 입력한다.
`report.py` — 오류 행을 확인하는 파일 전체
```python
from learning.merge import load_normalized_events

events = load_normalized_events()
errors = []
for event in events:
    if event["status_code"] >= 400:
        errors.append(event)
        print(event["id"], event["source"], event["status_code"])

print("전체 관측:", len(events))
print("오류 관측:", len(errors))
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.report
```
```plain text
app-2 app 404
nginx-2 nginx 404
전체 관측: 4
오류 관측: 2
```
`errors`는 조건에 맞는 행을 모을 빈 목록이다. 반복문이 네 행을 하나씩 확인하고, `if`가 참일 때만 그 행을 추가한다. `len(errors)`는 이렇게 모은 행의 수를 센다. `events`를 지우거나 고치지 않았으므로 전체 관측은 계속 4다.
앱과 Nginx를 나누는 조건은 없다. 두 출처 모두 `status_code`가 숫자라는 같은 규칙을 따르므로 한 번의 반복문과 한 조건으로 처리할 수 있다. 이것이 정규화한 결과를 재사용하는 이유다.
<details>
<summary>숫자와 문자열을 비교할 수 없다는 오류가 나면</summary>
	조건의 숫자를 따옴표로 감싸면 문자열이 된다. 다음은 404와 문자열 "400"을 비교하는 실수다.
	실수한 코드 — 숫자와 문자열의 크기 비교
	```python
status_code = 404
print(status_code >= "400")
	```
	```plain text
TypeError: '>=' not supported between instances of 'int' and 'str'
	```
	비교 기준도 숫자여야 한다. `report.py`의 조건에서 400을 감싼 따옴표를 없애고 저장한다. 같은 실행 명령으로 다시 실행하면 오류 관측 2가 나온다.
	복구 원리 — 숫자끼리 비교하기
	```python
status_code = 404
print(status_code >= 400)
	```
	```plain text
True
	```
</details>
## 3단계. 조건 하나를 바꾸어 결과 비교하기
같은 파일에서 서버 오류인 500번대만 보려면 어떻게 될까? 원본은 건드리지 않고 지금 작성한 `report.py`의 조건 한 줄만 아래처럼 바꾼다. 들여쓰기는 그대로 유지한다.
교체할 한 줄 — 저장 후 다시 실행
```plain text
    if event["status_code"] >= 500:
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.report
```
```plain text
전체 관측: 4
오류 관측: 0
```
이번 파일에는 상태 200과 404만 있으므로 500 이상에 맞는 행은 없다. 전체 관측 4는 그대로이고 오류 관측만 0이 된다. 이는 서버 오류 조건에 맞는 기록이 없다는 뜻이지 404가 사라졌거나 서비스가 안전하다는 판정은 아니다.
이번 실습은 404도 함께 세기로 했으므로 조건을 아래 한 줄로 되돌리고 Ctrl+S로 저장한다.
복구할 한 줄 — 저장 후 다시 실행
```plain text
    if event["status_code"] >= 400:
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.report
```
```plain text
app-2 app 404
nginx-2 nginx 404
전체 관측: 4
오류 관측: 2
```
같은 두 ID가 다시 출력되고 오류 관측이 2로 돌아오면 비교가 끝났다. 새 로그를 만들지 않았으므로 달라진 것은 원본이 아니라 조건이다.
## 4단계. 계산 결과를 함수로 돌려주기
지금 코드는 터미널에 숫자를 출력한다. 감시 화면에서도 같은 결과를 쓰려면 계산한 값과 원본 행을 다른 코드에 돌려줘야 한다. 그 역할을 `build_report()`라는 함수에 묶자.
화면에서도 사용할 완성 파일 저장
1. `report.py`를 아래 전체 코드로 바꾸고 Ctrl+S로 저장한다.
2. 같은 실행 명령으로 최종 숫자를 확인한다.
`report.py` — build\_report와 실행 부분을 포함한 완성 파일 전체
```python
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
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.report
```
```plain text
전체 관측: 4
오류 관측: 2
```
앞에서 실행한 계산을 함수 안에 옮겼다. `return` 뒤의 딕셔너리는 이름으로 값을 찾는 묶음이다. 함수를 호출한 쪽은 이 묶음에서 숫자와 로그 목록을 꺼내 사용할 수 있다.
<table header-row="true" fit-page-width="true">
<tr>
<td>돌려주는 항목</td>
<td>사용할 값</td>
</tr>
<tr>
<td>`ready`</td>
<td>`True`: 실습 보고서가 만들어졌다는 표시다. 공격 여부나 서비스 정상 판정이 아니다.</td>
</tr>
<tr>
<td>`events`</td>
<td>정규화한 전체 네 행. 출처·원문도 그대로 들어 있다.</td>
</tr>
<tr>
<td>`total_count`</td>
<td>전체 관측 수 4.</td>
</tr>
<tr>
<td>`error_count`</td>
<td>상태 400 이상인 관측 수 2.</td>
</tr>
</table>
`events`에 `errors`를 넣지 않은 점을 확인하자. 오류 수는 별도로 계산하지만 전체 네 행을 반환해야 화면에서 전체와 오류를 선택해 볼 수 있다. 화면의 조건 선택은 보여 줄 행만 바꾸며 이 원본 목록을 삭제하지 않는다.
## 5단계. 숫자의 의미와 다음 연결 확인하기
이번 오류 관측 두 행은 `app-2`와 `nginx-2`다. 준비 수집기가 없는 경로로 보낸 한 요청을 두 위치에서 기록했기 때문이다. 오류 관측 2를 실패한 요청 2건이나 공격 2회로 읽지 않는다.
- 같은 파일에서 조건을 400 → 500 → 400으로 바꾸어 2 → 0 → 2를 확인했다.
- 최종 `build_report()`는 전체 관측 4와 오류 관측 2를 돌려준다.
- 전체 네 행과 `source`, `raw`를 보존했고 `report.py`를 저장했다.
이 함수는 SIEM의 일부인 통합 로그의 조건 집계를 만든다. 계정을 차단하거나 자동으로 대응하는 기능은 아니다. 다음에는 제공된 감시 화면이 이 함수를 호출해 네 행과 숫자를 어떻게 보여 주는지 확인하자.
## 확인문제
**확인문제 1.** 정규화 뒤에는 앱과 Nginx에 같은 오류 조건을 쓸 수 있는 이유가 무엇인가?
<details>
<summary>정답과 해설</summary>
	두 결과 모두 status\_code라는 같은 이름의 항목에 숫자를 저장했기 때문이다. 원래 형식별로 문자열을 다시 해석할 필요가 없다.
</details>
**확인문제 2.** 상태 404는 `status_code >= 400` 조건에 포함되는가?
<details>
<summary>정답과 해설</summary>
	포함된다. 404는 400 이상이고, `>=`는 경계값과 같은 경우도 포함한다.
</details>
**확인문제 3.** 이번 자료에서 조건을 500 이상으로 바꾸면 왜 오류 관측이 0인가?
<details>
<summary>정답과 해설</summary>
	저장된 상태는 200과 404뿐이기 때문이다. 두 값 모두 500보다 작으므로 조건에 맞는 행이 없다.
</details>
**확인문제 4.** 500으로 비교한 뒤 왜 400으로 되돌리는가?
<details>
<summary>정답과 해설</summary>
	이번 완성 목표는 404를 포함한 오류 응답 관측을 세는 것이기 때문이다. 500 이상만 남기면 없는 경로의 404를 빼게 된다.
</details>
**확인문제 5.** 오류 관측이 2인데 events에 네 행을 모두 남기는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	오류 수를 계산하는 일과 전체 로그를 조회하는 일은 다르다. 전체를 보존해야 화면에서 조건을 바꾸어 성공과 오류를 모두 볼 수 있다.
</details>
**확인문제 6.** 이번 오류 관측 두 행을 실패한 요청 두 건으로 읽어도 되는가?
<details>
<summary>정답과 해설</summary>
	안 된다. 준비 수집기의 없는 경로 요청 한 건을 앱과 Nginx가 각각 기록했다. 이 숫자는 요청 수가 아닌 관측 기록 수다.
</details>
**확인문제 7.** ready가 True이면 공격이 없거나 서비스가 정상이라는 뜻인가?
<details>
<summary>정답과 해설</summary>
	아니다. 이 실습에서 ready는 보고서가 준비됐다는 표시다. 보안 판정이나 전체 서비스 상태를 검사한 값이 아니다.
</details>
**확인문제 8.** print만 쓰지 않고 build\_report에서 딕셔너리를 return하는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	화면을 위한 다른 코드가 전체 로그와 계산한 숫자를 사용해야 하기 때문이다. 터미널 출력 대신 이름으로 접근할 수 있는 값을 돌려준다.
</details>
**확인문제 9.** 조건을 바꾸는 실험에서 원본을 다시 수집해야 하는가?
<details>
<summary>정답과 해설</summary>
	아니다. 같은 네 행에 조건만 바꿔 적용해야 결과가 달라진 이유를 비교할 수 있다.
</details>
**확인문제 10.** 404 기록을 찾았다는 이유만으로 자동 차단을 실행해도 되는가?
<details>
<summary>정답과 해설</summary>
	아니다. 이번에는 수업에서 일부러 없는 경로를 요청해 404가 생겼다. 이 함수는 기록을 집계할 뿐 공격 판정이나 대응 승인을 수행하지 않는다.
</details>
같은 로그 목록과 계산한 숫자를 돌려주는 함수가 완성됐다. 다음에는 이 결과를 제공된 화면에서 읽어 보자.