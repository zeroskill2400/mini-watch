같은 요청을 남겨도 Flask는 JSON으로, Nginx는 긴 글 한 줄로 기록한다. 이대로는 같은 항목을 읽는 방법이 서로 다르다. 이번 목표는 Flask 기록 한 건을 공통 항목으로 바꾸고, 원본에 없는 시각은 비워 두는 것이다.
성공 요청과 없는 경로 요청을 같은 항목으로 읽는다. 시각의 `None`은 원본에 값이 없다는 표시다.
<image src="../assets/lesson2.svg">설명용 변환도 — Flask 원본 세 값을 옮기고 출처·분석용 이름을 붙이되 없는 시각은 만들지 않는다.</image>
왼쪽은 실제 앱 원본의 모양, 오른쪽은 이번에 만들 공통 기록이다. 원본의 세 값과 새로 붙인 표식을 구분해 읽고 아래 첫 단계에서 자기 파일을 연다.
```plain text
mini-watch-m5d3
└─ monitor
   └─ backend
      └─ learning
         ├─ classroom_data.py   준비된 파일 읽기 도구
         ├─ lesson2.py          2단계에서 만들 실행 파일
         ├─ normalize_app.py    4단계에서 완성할 변환 코드
         └─ data
            └─ case.json       실제 수집한 두 종류 기록
```
<table_of_contents/>
## 1단계. 같은 사례의 Flask 원본 열기
1교시에서 준비한 프로젝트와 실행 중인 서비스를 그대로 쓴다. VS Code에서 `C:\work\mini-watch-m5d3`를 열고, 터미널의 + 옆 화살표 → Command Prompt로 CMD를 선택한다. 다른 이름의 폴더를 사용했다면 아래 경로만 자기 폴더로 바꾼다.
프로젝트 폴더의 Windows CMD
```plain text
cd /d C:\work\mini-watch-m5d3
```
같은 원본을 열어 보자
1. 탐색기에서 `monitor` → `backend` → `learning` → `data` → `case.json`을 연다.
2. `app` 안에 있는 기록 두 건을 찾는다. 첫 기록은 GET·`/`·200, 둘째는 GET·`/training-missing`·404이다. 원본을 수정하지 않는다.
`case.json`의 `app`에는 Flask가 만든 JSON 기록이, `nginx`에는 Nginx가 만든 한 줄짜리 접근 기록이 있다. 두 입력은 같은 두 요청을 각기 다른 곳에서 남긴 자료다. 이번 시간에는 `app`만 읽고 다음 시간에 `nginx`를 읽는다.
첫 Flask 기록의 모양 — 읽기용
```json
{"method": "GET", "path": "/", "status_code": 200}
```
`method`는 요청 방법, `path`는 경로, `status_code`는 응답 상태다. 이 Flask 원본에는 시각과 ID가 없다. DB 조회 결과에 붙었던 값이나 지금 시각을 여기의 원본 값처럼 끼워 넣지 않는다.
<details>
<summary>`case.json`이 없으면</summary>
	같은 프로젝트 폴더의 CMD에서 제공된 수집 도구를 한 번 실행한다. 일반 서비스의 목록 경로와 없는 경로를 요청하고, Flask 기록 두 건과 Nginx 기록 두 줄을 같은 파일에 저장한다. 예시 원문을 대신 붙여 넣지 않는다.
	프로젝트 폴더의 Windows CMD
	```plain text
docker compose -f compose-general.yaml exec -T general-api python collect_classroom.py
	```
	수집에 성공한 뒤 `learning` → `data` → `case.json`을 다시 연다. 오류가 나오면 다음 단계로 넘어가지 않고 CMD의 메시지를 확인한다. 준비 서비스가 꺼져 있다면 이 프로젝트의 `start-class.cmd`로 다시 시작한다. 기존 글·계정·DB를 지우지 않는다.
</details>
## 2단계. 공통 항목으로 한 건 바꾸기
지금 Flask 기록은 이름으로 값을 읽을 수 있지만 Nginx 기록은 긴 문자열이다. 나중에 같은 화면과 분석 코드로 읽으려면 두 입력을 같은 항목 이름으로 맞춰야 한다. 정규화는 서로 다른 표현을 공통 형식으로 맞추되 원본의 뜻을 유지하는 일이다.
<table header-row="true" fit-page-width="true">
<tr>
<td>공통 항목</td>
<td>이 Flask 기록에서 넣을 값</td>
<td>값이 온 곳</td>
</tr>
<tr>
<td>`id`</td>
<td>`app-1`</td>
<td>이번 파일의 첫 앱 기록에 붙이는 분석용 이름</td>
</tr>
<tr>
<td>`source`</td>
<td>`app`</td>
<td>어느 입력에서 왔는지 붙이는 출처 표식</td>
</tr>
<tr>
<td>`time`</td>
<td>`None`</td>
<td>원본에 시각이 없다는 표시</td>
</tr>
<tr>
<td>`method`·`path`·`status_code`</td>
<td>`GET`·`/`·200</td>
<td>원본에서 읽은 값</td>
</tr>
<tr>
<td>`raw`</td>
<td>원본 한 건</td>
<td>변환 전 내용을 그대로 보관</td>
</tr>
</table>
`None`은 값이 없다는 Python 표현이다. 0초라는 측정값도 아니고 현재 시각도 아니다. `app-1`은 원본에 있던 DB 번호가 아니라 이번 수집 파일의 첫 앱 기록을 찾는 이름이며, 다음에 다시 수집한 파일의 `app-1`과 같은 사건이라고 볼 수 없다.
딕셔너리는 이름과 값을 짝지어 담는 자료다. `{ "path": "/" }`에서 `path`라는 이름으로 `/`를 읽듯, 아래 코드도 원본에서 값을 꺼내 새 딕셔너리에 넣는다.
함수는 입력을 받아 정해진 처리를 하고 결과를 돌려주는 코드 묶음이다. 파일 읽기는 준비된 `read_case` 함수를 사용한다. 지금은 변환을 작은 프로그램으로 실행하고, 마지막 단계에서 그 변환에도 함수 이름을 붙인다.
작은 변환 프로그램을 저장하자
1. `monitor` → `backend` → `learning`에 `lesson2.py`를 만들거나 기존 파일을 연다.
2. 아래 전체 코드를 넣고 Ctrl+S로 저장한다. `data` 폴더 안이 아니라 `learning` 바로 아래에 둔다.
`lesson2.py` — 한 건을 바꾸는 전체 코드
```python
from learning.classroom_data import read_case

case = read_case()
number = 1
raw = case["app"][number - 1]

event = {
    "id": f"app-{number}",
    "source": "app",
    "time": None,
    "method": raw["method"],
    "path": raw["path"],
    "status_code": int(raw["status_code"]),
    "raw": raw,
}

print("ID와 출처", event["id"], event["source"])
print("요청", event["method"], event["path"], event["status_code"])
print("시각", event["time"])
print("원본", event["raw"])
```
첫 줄은 준비된 파일 읽기 함수 `read_case`를 가져온다. `case = read_case()`가 `case.json`을 읽는다. `case["app"]`은 앱 기록 목록이고, 위치는 0부터 세므로 `number - 1`이 첫 위치 0을 고른다.
`event = { ... }`가 새 공통 기록을 만든다. `f"app-{number}"`는 번호를 이름 뒤에 붙이고 `source`는 앱 출처를 표시한다. 세 요청 값은 `raw`에서 읽으며 `int`는 상태를 숫자로 맞춘다. `"raw": raw`는 나중에 되짚을 원본을 남긴다.
마지막 네 `print`는 새 이름과 출처, 요청 값, 비어 있는 시각, 보관한 원본을 각각 출력한다. 파일을 저장한 뒤 아래 명령으로 실행하자.
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson2
```
```plain text
ID와 출처 app-1 app
요청 GET / 200
시각 None
원본 {'method': 'GET', 'path': '/', 'status_code': 200}
```
원본의 세 요청 값은 그대로이고 출처·분석용 이름·빈 시각 칸이 추가됐다. 원본 출력의 작은따옴표는 Python의 표시 방식이다. JSON 파일의 큰따옴표를 고쳐야 한다는 뜻이 아니다.
키 이름을 틀리면 어떻게 될까? 원본은 그대로 두고 `lesson2.py`의 상태를 읽는 줄만 아래처럼 바꿔 저장하고 실행한다. 아래는 의도된 오류를 만들기 위해 교체할 한 줄이다.
의도된 오류 — 기존 상태 읽기 한 줄과 교체
```plain text
    "status_code": int(raw["status"]),
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson2
```
```plain text
KeyError: 'status'
```
오류의 마지막 줄이다. 원본에는 `status`라는 키가 없어서 그 이름으로 값을 읽을 수 없다. 왼쪽의 공통 항목 이름이 아니라 오른쪽 원본 키를 `status_code`로 고쳐야 한다. 아래 정상 줄로 복구하고 다시 실행해 앞의 네 출력 줄이 나오는지 확인한다.
복구할 한 줄
```plain text
    "status_code": int(raw["status_code"]),
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson2
```
<details>
<summary>실행이 안 되면</summary>
	`No module named learning.lesson2`이면 저장 위치와 파일 이름을 확인하고 Ctrl+S를 누른다. `read_case`를 가져올 수 없으면 준비된 `classroom_data.py`가 같은 `learning` 폴더에 있는지 본다. 새 패키지를 설치하지 않는다. 파일이 없다는 안내가 나오면 1단계 수집 명령으로 준비한다.
</details>
## 3단계. 같은 변환에 다른 원본 넣기
다른 기록도 같은 모양으로 바뀌는지 보자. 원본 파일은 그대로 두고 `lesson2.py`에서 다음 한 줄만 바꾼 뒤 저장한다.
바꿀 한 줄
```python
number = 2
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson2
```
```plain text
ID와 출처 app-2 app
요청 GET /training-missing 404
시각 None
원본 {'method': 'GET', 'path': '/training-missing', 'status_code': 404}
```
번호 2가 두 번째 원본을 고르고 이름도 `app-2`로 바꿨다. 경로와 상태는 그 원본에서 읽었기 때문에 달라졌다. 시각은 두 원본 모두 없으므로 여전히 `None`이다. 정규화가 404를 성공으로 고치거나 기록을 지우지는 않는다.
완료 확인: 첫 결과와 둘째 결과의 항목 이름은 같고 요청 값만 다르다. `raw`에는 각각 바꾸기 전 기록이 남아 있어야 한다. 다음 단계에서는 파일 전체를 교체하므로 번호를 따로 복구할 필요는 없다.
## 4단계. 변환 함수를 만들어 두 건에 적용하기
같은 변환을 계속 복사하지 않으려면 이름을 붙여 재사용하면 된다. 함수는 입력을 받아 정해진 처리를 하고 결과를 돌려주는 코드 묶음이다. 이번 함수는 원본 한 건과 번호를 받아 공통 기록 한 건을 돌려준다.
함수의 모양 — 읽기용
```plain text
def 함수이름(입력):
    return 결과
```
`def`는 함수를 정의하고 `return`은 결과를 호출한 곳에 돌려준다. 이 단계에서는 앞에서 실행한 딕셔너리 만들기를 함수 안으로 옮긴다.
함수 파일 저장하기
1. 같은 `learning` 폴더의 `normalize_app.py`를 연다. 파일이 없을 때만 같은 이름으로 새로 만든다.
2. 기존 내용을 아래 전체 코드로 바꾸고 저장한다. 함수 파일은 저장만으로 결과를 출력하지 않는다.
`normalize_app.py` — 파일 전체
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
`event`에는 원본 한 건, `number`에는 이번 파일 안의 순서가 들어온다. 딕셔너리의 각 항목은 앞에서 확인한 처리와 같다. `return`이 완성한 한 건을 호출한 쪽으로 넘긴다.
두 건을 처리하는 실행 파일 저장하기
1. `lesson2.py`의 전체 내용을 아래 코드로 바꿔 Ctrl+S로 저장한다.
2. `normalize_app.py`와 `classroom_data.py`가 같은 폴더에 있는지 확인하고 명령을 실행한다.
`lesson2.py` — 이번 시간이 끝날 때 남길 전체 파일
```python
from learning.classroom_data import read_case
from learning.normalize_app import normalize_app

case = read_case()
for number, raw in enumerate(case["app"], start=1):
    event = normalize_app(raw, number)
    print(event["id"], event["source"], event["method"],
          event["path"], event["status_code"], event["time"])
```
두 `import`는 파일 읽기와 방금 작성한 변환 함수를 가져온다. `enumerate(..., start=1)`은 기록을 하나씩 꺼내면서 1부터 번호를 붙인다. 반복할 때마다 `normalize_app(raw, number)`가 한 건을 바꾸고 `print`가 그 반환값을 보여 준다.
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson2
```
```plain text
app-1 app GET / 200 None
app-2 app GET /training-missing 404 None
```
출력 두 줄은 공통 항목의 순서를 같게 해 읽은 결과다. 시각을 만들어 넣지 않았고 없는 경로 기록도 남았다. 다음 시간에는 Nginx 문자열을 같은 항목으로 바꾼다.
- 두 기록의 출처는 `app`이고 분석용 이름은 `app-1`, `app-2`다.
- 원본의 경로·상태가 유지되고 시각은 두 건 모두 `None`이다.
- `normalize_app`이 값을 바꾸는 곳과 `lesson2.py`가 호출·출력하는 곳을 구분한다.
## 챙겨 가기 — 읽은 값과 붙인 표식 구분하기
<table header-row="true" fit-page-width="true">
<tr>
<td>항목</td>
<td>기억할 점</td>
</tr>
<tr>
<td>요청 방법·경로·상태</td>
<td>실제 원본에서 읽는다.</td>
</tr>
<tr>
<td>분석용 이름·출처</td>
<td>파일 안에서 원본을 찾기 위해 붙인다.</td>
</tr>
<tr>
<td>시각</td>
<td>원본에 없으면 `None`으로 남긴다.</td>
</tr>
<tr>
<td>원본 `raw`</td>
<td>변환 결과를 되짚을 때 사용한다.</td>
</tr>
</table>
## 되새김 문제
다음 질문에 말로 답할 수 있으면 이번 시간을 제대로 이해한 것이다.
- 정규화 전후에 그대로 남은 값과 새로 붙인 표식은 무엇인가?
- Flask 기록의 시각을 현재 시각으로 채우면 왜 안 되는가?
- 다음 Nginx 기록도 같은 항목으로 바꾸면 어떤 코드를 함께 쓸 수 있을까?
## 확인문제
**확인문제 1.** 이번 시간에는 `case.json`의 어느 입력을 읽는가?
<details>
<summary>정답과 해설</summary>
	`app` 안의 실제 Flask 기록 두 건이다. `nginx` 문자열은 같은 파일에 있지만 다음 시간에 다룬다.
</details>
**확인문제 2.** 서로 다른 로그의 항목을 같은 이름으로 맞추는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	입력마다 다른 방식으로 읽은 뒤에도 같은 분석 코드와 화면에서 공통 항목을 사용할 수 있게 하려는 것이다. 원본의 뜻을 바꾸려는 것은 아니다.
</details>
**확인문제 3.** 원본에서 그대로 읽는 요청 값 세 가지는 무엇인가?
<details>
<summary>정답과 해설</summary>
	`method`, `path`, `status_code`다. 각각 요청 방법·경로·응답 상태이며 정규화 과정에서 성공이나 실패를 바꾸지 않는다.
</details>
**확인문제 4.** `app-1`은 원본 DB의 번호인가?
<details>
<summary>정답과 해설</summary>
	아니다. 이번 수집 파일의 첫 앱 기록에 붙인 분석용 이름이다. 다른 파일의 같은 이름과 동일 사건이라고 연결하지 않는다.
</details>
**확인문제 5.** `source`를 `app`으로 넣는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	공통 형식으로 바뀐 뒤에도 Flask 앱 원본에서 온 기록임을 구분하기 위해서다. Nginx 출처와 혼동하지 않는다.
</details>
**확인문제 6.** 시각에 `None`을 넣는 것은 0초를 뜻하는가?
<details>
<summary>정답과 해설</summary>
	아니다. 원본에 시각 값이 없다는 뜻이다. 0이나 현재 시각은 다른 사실을 주장하므로 대신 넣지 않는다.
</details>
**확인문제 7.** `number`를 1에서 2로 바꾸었을 때 404가 나온 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	두 번째 실제 원본이 없는 경로의 404 요청이기 때문이다. 같은 변환을 다른 입력에 적용한 것이지 상태를 임의로 바꾼 것이 아니다.
</details>
**확인문제 8.** `raw`를 결과에 남기는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	어떤 원본을 어떻게 변환했는지 다시 확인하기 위해서다. 공통 항목으로 다 표현하지 않은 원본도 보존한다.
</details>
**확인문제 9.** `normalize_app.py`를 저장했는데 출력이 없는 것은 왜인가?
<details>
<summary>정답과 해설</summary>
	함수 정의만으로 호출되지 않기 때문이다. `lesson2.py`가 파일을 읽고 함수를 호출한 뒤 `print`로 반환값을 보여 준다.
</details>
**확인문제 10.** `enumerate(case["app"], start=1)`은 무엇을 만들어 주는가?
<details>
<summary>정답과 해설</summary>
	앱 원본을 차례로 꺼내며 1, 2라는 순서를 함께 준다. 그 번호를 변환 함수에 전달해 파일 안에서 구분할 이름을 만든다.
</details>
Flask 두 기록의 공통 형식을 만들었다. 다음에는 같은 요청을 남긴 Nginx 문자열에서 값을 꺼내 이 형식에 맞춰 보자.