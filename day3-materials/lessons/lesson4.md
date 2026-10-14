앱 로그와 Nginx 로그를 같은 항목으로 바꾸었지만, 따로 출력하면 두 결과를 번갈아 봐야 한다. 이번에는 두 변환 결과를 한 목록에 담자. 출처가 다른 로그를 같은 열로 읽는 SIEM 통합 조회의 준비 단계다.

완료하면 앱 두 행과 Nginx 두 행, 모두 네 행이 출처와 함께 출력된다. 원본은 그대로 두고 목록을 만드는 `merge.py`만 작성한다.
완성 모습: 앱만 읽을 때는 2행, Nginx까지 합치면 4행이다.
<image src="../assets/lesson4.svg">두 출처의 변환 결과를 같은 목록에 넣기 — 동작을 설명하는 그림이다.</image>
왼쪽 두 묶음은 같은 `case.json` 안에 있다. 가운데의 함수가 각각 공통 모양으로 바꾸고, `append`가 오른쪽 목록 끝에 한 행씩 붙인다. 원본 형식은 달라도 변환한 뒤에는 같은 열로 읽는다.
```plain text
mini-watch-m5d3
└─ monitor
   └─ backend
      └─ learning
         ├─ classroom_data.py   제공된 원본 읽기
         ├─ normalize_app.py    앱 정규화
         ├─ normalize_nginx.py  Nginx 정규화
         ├─ merge.py            이번에 작성
         └─ data
            └─ case.json       같은 실습 원본
```
<table_of_contents/>
## 1단계. 같은 원본과 정규화 파일 준비하기
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
`learning` 폴더의 `normalize_app.py`와 `normalize_nginx.py`는 각 출처를 공통 모양으로 바꾸는 파일이다. 그 안의 함수를 불러 쓸 것이므로 같은 폴더에 있어야 한다. `read_case()`는 제공된 파일 읽기 함수이며 새 요청을 보내지 않고 `case.json`의 내용을 가져온다.
<details>
<summary>앞에서 만든 정규화 파일이 없거나 NoneType 오류가 나면</summary>
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
	저장한 뒤 이 페이지의 실행 명령을 다시 입력한다. 새 패키지 설치나 DB 초기화는 하지 않는다.
</details>
## 2단계. 앱의 두 행부터 목록에 넣기
목록은 여러 값을 순서대로 담는 Python 값이다. 빈 목록 `[]`을 만들고, 앱 원본을 하나씩 변환해 넣는 것부터 실행하자.
VS Code에서 파일 저장
1. `monitor` → `backend` → `learning`에서 `merge.py`를 연다. 없으면 새 파일로 만든다.
2. 아래 전체 코드를 붙여 넣고 Ctrl+S로 저장한다.
`merge.py` — 앱 두 행을 합치는 파일 전체
```python
from learning.classroom_data import read_case
from learning.normalize_app import normalize_app


def load_normalized_events():
    case = read_case()
    events = []
    for number, event in enumerate(case["app"], start=1):
        events.append(normalize_app(event, number))
    return events


if __name__ == "__main__":
    events = load_normalized_events()
    for event in events:
        print(event["id"], event["source"], event["method"], event["path"], event["status_code"])
    print("전체 관측:", len(events))
```
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.merge
```
```plain text
app-1 app GET / 200
app-2 app GET /training-missing 404
전체 관측: 2
```
`enumerate(..., start=1)`은 앱의 첫 행에 1, 둘째 행에 2를 붙여 순서와 원본을 함께 꺼낸다. `normalize_app(event, number)`가 공통 모양을 만들고, `events.append(...)`가 그 결과를 목록에 넣는다. 반복이 끝난 뒤 `return events`가 완성한 목록을 호출한 곳에 돌려준다.
`if __name__ == "__main__":` 아래는 지금처럼 `python -m learning.merge`로 직접 실행할 때만 동작한다. 다른 파일이 `import`로 함수를 가져오면 이 출력 부분은 실행하지 않는다.
파일 아래의 실행 부분이 함수를 호출하고 각 행을 출력한다. 함수는 목록을 만들고, `print`는 그 목록을 화면에 보여 준다는 차이를 보자. 현재는 앱만 넣었으므로 `전체 관측: 2`가 맞다.
<details>
<summary>dict에 append가 없다는 오류가 나면</summary>
	빈 목록을 만들 때 `[]` 대신 `{}`를 쓰면 다른 종류의 값이 된다. 아래 두 줄은 그 실수를 작게 떼어 본 코드다.
	실수한 코드 — 빈 딕셔너리에 목록 동작을 시도함
	```python
events = {}
events.append({"source": "app"})
	```
	```plain text
AttributeError: 'dict' object has no attribute 'append'
	```
	`{}`는 딕셔너리라 목록에 추가하는 `append`가 없다. `merge.py`의 첫 `events` 대입이 `events = []`인지 확인하고 저장한다. 같은 실행 명령으로 돌아와 앱 두 행과 전체 관측 2가 나오는지 확인한다.
	복구 원리 — 목록이면 한 행을 추가할 수 있다
	```python
events = []
events.append({"source": "app"})
print(len(events))
	```
	```plain text
1
	```
</details>
## 3단계. Nginx 두 행도 같은 목록에 넣기
이제 Nginx 원본도 같은 목록에 넣는다. 앱의 원본 객체에는 `normalize_app`, Nginx의 원본 문자열에는 `normalize_nginx`를 사용한다. 두 결과의 항목 이름은 이미 같다.
같은 파일을 완성하기
1. `merge.py`를 아래 전체 코드로 바꾸고 Ctrl+S로 저장한다.
2. 같은 CMD에서 아래 실행 명령을 다시 입력한다.
`merge.py` — 두 출처를 합치는 완성 파일 전체
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
프로젝트 폴더의 Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.merge
```
```plain text
app-1 app GET / 200
app-2 app GET /training-missing 404
nginx-1 nginx GET / 200
nginx-2 nginx GET /training-missing 404
전체 관측: 4
```
두 번째 반복문도 기존 `events`에 계속 추가한다. 그래서 앱 두 행 다음에 Nginx 두 행이 나온다. 두 반복문 사이에서 `events = []`를 다시 쓰면 앱 결과를 잃으므로 목록은 처음 한 번만 만든다.
`app-1`과 `nginx-1`은 출처와 원본 순서로 붙인 이름이다. 번호 1이 같다고 하나의 기록은 아니다. 이 이름은 현재 원본 묶음 안에서 행을 구분하며, 다시 수집한 다른 파일까지 통하는 요청 번호는 아니다.
## 4단계. 네 행이 뜻하는 것 확인하기
이번 준비 수집기는 분석 대상으로 목록과 없는 경로를 한 번씩 요청했다. 앱과 Nginx가 각 요청을 기록해 출처별 두 행, 합쳐서 네 행이 된 것이다. 로그를 합쳤다고 요청이 네 번 발생한 것은 아니다.
<table header-row="true" fit-page-width="true">
<tr>
<td>확인할 것</td>
<td>이번 결과의 뜻</td>
</tr>
<tr>
<td>`source`</td>
<td>`app`과 `nginx`를 그대로 남겨 기록한 위치를 구분한다.</td>
</tr>
<tr>
<td>`time`</td>
<td>앱은 원본에 시각이 없어 `None`, Nginx는 자기 원본의 시각을 사용한다.</td>
</tr>
<tr>
<td>`raw`</td>
<td>앱 원본 객체와 Nginx 원본 문자열을 그대로 보관한다.</td>
</tr>
<tr>
<td>출력 순서</td>
<td>앱 다음에 Nginx를 넣은 순서이며, 실제 발생 시각순으로 정렬한 결과는 아니다.</td>
</tr>
</table>
일반적인 로그에서 경로와 상태가 같다는 이유만으로 두 행을 같은 요청이라고 확정하거나 지우지 않는다. 이 함수는 정규화한 관측 기록을 합칠 뿐, 요청을 서로 연결하거나 중복 제거하지 않는다.
- 네 행 모두 ID·출처·방법·경로·상태가 출력된다.
- 전체 관측은 4이며 앱과 Nginx 두 출처가 남아 있다.
- 완성한 `merge.py`와 같은 `case.json`을 그대로 둔다.
이제 한 목록의 상태 값을 같은 조건으로 비교할 수 있다. 다음에는 출처마다 다른 코드를 쓰지 않고, 오류 응답을 기록한 행을 함께 골라 보자.
## 확인문제
**확인문제 1.** 두 원본을 바로 이어 붙이지 않고 각각 정규화하는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	앱은 객체, Nginx는 문자열이어서 항목을 읽는 방법이 다르다. 먼저 같은 이름과 타입으로 바꾸면 합친 뒤 같은 코드로 읽을 수 있다.
</details>
**확인문제 2.** read\_case()를 다시 호출하면 웹 요청이 새로 발생하는가?
<details>
<summary>정답과 해설</summary>
	아니다. 준비된 `case.json`을 읽는 함수다. 원본을 다시 수집하는 시작 명령과 다르다.
</details>
**확인문제 3.** 반복문 두 개가 서로 다른 정규화 함수를 사용하는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	각 반복문이 읽는 원본 형식이 다르기 때문이다. 앱 객체는 normalize\_app, Nginx 문자열은 normalize\_nginx가 해석한다.
</details>
**확인문제 4.** enumerate의 start=1은 어떤 값을 정하는가?
<details>
<summary>정답과 해설</summary>
	각 출처의 원본에 붙일 첫 순서 번호를 1로 정한다. 이 번호는 앱이나 Nginx의 실제 요청 식별자를 읽은 값이 아니다.
</details>
**확인문제 5.** app-1과 nginx-1의 숫자가 같으면 같은 로그로 지워도 되는가?
<details>
<summary>정답과 해설</summary>
	안 된다. 출처별 첫 행이라는 뜻일 뿐이다. 이 함수는 두 관측을 별도로 보관한다.
</details>
**확인문제 6.** 왜 이번 요청 두 건에서 전체 관측 네 행이 나오는가?
<details>
<summary>정답과 해설</summary>
	준비 수집기가 보낸 두 요청을 앱과 Nginx가 각각 기록했기 때문이다. 출처별 두 행을 합쳐 네 행이다.
</details>
**확인문제 7.** 시각을 맞추려고 앱의 time에 Nginx 시각을 복사해도 되는가?
<details>
<summary>정답과 해설</summary>
	안 된다. 앱 원본에는 시각이 없다. 정규화는 없는 값을 추정해 채우는 작업이 아니므로 None을 유지한다.
</details>
**확인문제 8.** 공통 항목을 만들었는데 raw를 왜 남기는가?
<details>
<summary>정답과 해설</summary>
	변환한 값이 어디에서 왔는지 원본과 대조하기 위해서다. 공통 표에서 생략한 출처별 정보도 원본에서 볼 수 있다.
</details>
**확인문제 9.** 두 반복문 사이에 events = \[\]를 다시 쓰면 무엇이 달라지는가?
<details>
<summary>정답과 해설</summary>
	앞에서 담은 앱 결과를 잃고 새 목록에 Nginx만 남는다. 두 출처를 한 목록에 쌓으려면 처음 만든 events를 계속 사용한다.
</details>
**확인문제 10.** return events와 print(events)는 무엇이 다른가?
<details>
<summary>정답과 해설</summary>
	return은 목록을 다른 코드가 사용하도록 돌려주고, print는 화면에 출력한다. 이후 분석에서 재사용하려면 함수의 반환값이 필요하다.
</details>
두 출처를 같은 목록으로 합쳤다. 이제 한 가지 오류 조건을 이 네 행에 똑같이 적용하자.