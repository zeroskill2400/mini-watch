게시판 앱과 앞단 웹서버는 같은 요청도 서로 다른 모양으로 기록한다. 오늘은 이 두 로그를 같은 항목으로 바꿔 한 화면에서 읽는 SIEM의 일부 기능을 만든다. 먼저 준비된 서비스를 실행하고, 원본 두 종류가 어디에서 생기는지 확인하자.
완성할 결과와 확인 기준부터 보자.
<image src="../assets/lesson1.svg">설명용 흐름도 — 분석할 요청 두 건을 두 프로그램이 각각 기록한다. 오늘 만들 표는 요청 수가 아니라 출처가 있는 로그 네 행을 보여 준다.</image>
- 앱 JSON과 Nginx 문자열에서 같은 경로·상태를 찾는다.
- 어느 코드가 어느 로그를 만드는지 설명한다.
- 계정·환경은 준비된 것을 쓰고, 정규화부터 직접 구현한다.
```plain text
mini-watch-m5d3/
  start-class.cmd                         준비된 시작 명령
  general/request_logging.py              앱 원본을 만드는 코드
  gateways/general.conf                   Nginx 원본을 만드는 설정
  classroom-logs/                         실행하면 원본 로그 생성
  monitor/backend/learning/
    data/case.json                        시작 명령이 준비하는 입력
    normalize_app.py                      2교시에서 완성
    normalize_nginx.py                    3교시에서 완성
    merge.py                              4교시에서 완성
    report.py                             5교시에서 완성
```
<table_of_contents/>
## 1단계. 오늘 구현할 SIEM 기능 구분하기
게시판을 운영한다고 생각해 보자. 앱에서는 상태 코드가 JSON의 status\_code 값이고, 앞단 웹서버에서는 긴 글자 줄 중간의 숫자다. 오류가 난 기록을 찾으려면 두 형식을 각각 읽어야 한다.
서로 다른 자료를 같은 항목과 값의 형식으로 맞추는 작업을 정규화라고 한다. 이번에는 두 로그 모두 method·path·status\_code로 읽게 바꾸고, 같은 조건으로 오류를 골라 한 표에서 확인한다.
<table header-row="true" fit-page-width="true">
<tr>
<td>앞에서 나온 이름</td>
<td>무엇을 하는가</td>
<td>오늘의 범위</td>
</tr>
<tr>
<td>SIEM — Security Information and Event Management</td>
<td>여러 곳의 보안 관련 로그를 모아 검색·분석한다.</td>
<td>그중 로그 정규화·통합 조회·공통 조건 집계를 직접 만든다.</td>
</tr>
<tr>
<td>XDR — Extended Detection and Response</td>
<td>기기·계정·클라우드 등 여러 보안 영역의 탐지와 조사를 연결한다.</td>
<td>두 파일을 합치는 것만으로 XDR 전체를 구현했다고 하지 않는다.</td>
</tr>
<tr>
<td>SOAR — Security Orchestration, Automation and Response</td>
<td>여러 도구를 연결해 대응 절차를 자동화한다.</td>
<td>계정 차단·장비 격리 같은 자동 조치는 만들지 않는다.</td>
</tr>
</table>
세 이름은 반드시 순서대로 거치는 세 단계가 아니다. 오늘은 SIEM의 일부 기능을 작게 만들어 보는 수업이며, 실제 제품 전체를 만드는 수업은 아니다.
<table header-row="true" fit-page-width="true">
<tr>
<td>제공된 상태로 사용하는 것</td>
<td>직접 완성할 것</td>
</tr>
<tr>
<td>Docker 실행, 계정, 게시판, 로그 수집, 감시 화면</td>
<td>앱 로그 변환 → Nginx 로그 변환 → 합치기 → 오류 집계</td>
</tr>
</table>
먼저 준비된 환경에서 두 원본이 정말 다른 모양인지 확인하자. 마지막에는 아래처럼 같은 열로 읽는다. app은 앱, nginx는 앞단 웹서버라는 출처 이름이다.
```plain text
출처    방법  경로                 상태
app     GET   /                    200
app     GET   /training-missing     404
nginx   GET   /                    200
nginx   GET   /training-missing     404
```
## 2단계. 시작본을 실행하고 준비된 화면 열기
### 시작 자료를 받자
교실에서 쓰던 Git·VS Code·Docker Desktop이 설치된 Windows에서 시작한다. Docker Desktop을 먼저 켜고 실행 준비가 끝날 때까지 기다린다. Windows 검색에서 cmd를 열어 다음 명령을 차례로 실행하자.
프로젝트 폴더의 Windows CMD
```plain text
if not exist C:\work mkdir C:\work
cd /d C:\work
git clone --branch m5d3-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-m5d3
cd mini-watch-m5d3
```
이미 같은 폴더에서 작업 중이면 다시 클론하지 말고 그 폴더를 연다. 다른 Day 자료나 보존할 옛 파일이 같은 이름으로 있다면 지우지 말고 새 폴더 이름 mini-watch-m5d3-new로 받아 이후 경로도 그 이름을 사용한다.
VS Code에서 폴더 열기
1. VS Code의 파일 → 폴더 열기에서 `C:\work\mini-watch-m5d3`를 선택한다.
2. 터미널 → 새 터미널을 누르고 + 옆 화살표 → Command Prompt를 선택한다.
프로젝트 폴더의 Windows CMD
```plain text
cd /d C:\work\mini-watch-m5d3
start-class.cmd
```
이 시작 명령은 두 서비스를 실행하고 수업 계정을 준비한 뒤 분석할 실제 요청 두 건을 보낸다. 그 요청에서 생긴 앱 로그 두 행과 Nginx 로그 두 행을 `case.json`에 저장한다. 별도의 .env 작성이나 가입 절차는 없다.
```plain text
실제 요청 2건을 보냈습니다: GET / 200, GET /training-missing 404
원본 저장: Flask JSON 2행 + Nginx combined 2행
monitor/backend/learning/data/case.json 준비 완료
```
시작 출력 끝부분에서 위 세 줄을 찾으면 분석 입력까지 준비된 것이다. 준비 상태를 확인하는 요청은 별도로 있으며, 분석 대상은 목록과 없는 경로 두 요청이다. 실행 도중에는 게시판을 새로고침하지 않는다.
### 준비된 계정으로 감시 화면에 들어가자
<table header-row="true" fit-page-width="true">
<tr>
<td>화면</td>
<td>주소</td>
<td>수업 아이디</td>
<td>수업 비밀번호</td>
</tr>
<tr>
<td>감시 서비스</td>
<td>[http://localhost:8082](http://localhost:8082)</td>
<td>`class-operator`</td>
<td>`classroom1234!`</td>
</tr>
<tr>
<td>일반 게시판</td>
<td>[http://localhost:8081/login](http://localhost:8081/login)</td>
<td>`class-student`</td>
<td>`classroom1234!`</td>
</tr>
</table>
감시 화면에 들어가기
1. 브라우저에서 [http://localhost:8082](http://localhost:8082)를 연다. 이미 로그인한 적이 있으면 현재 로그인 확인을 누른다.
2. 로그인 칸이 보이면 아이디에 class-operator, 비밀번호에 classroom1234!를 입력하고 로그인을 누른다.
3. class-operator 사용자와 로그아웃 버튼이 보이면 아래로 내려 통합 로그 영역을 찾는다.
계정은 시작 명령이 미리 만든다. 가입이나 계정 생성은 하지 않는다. 일반 게시판 계정도 준비되어 있지만, 오늘의 두 조회 요청은 로그인 없이 가능하므로 게시판 로그인은 필수가 아니다.
위 비밀번호는 내 PC의 수업용 공개 값이다. 이 설정으로 외부에 배포하지 않는다. 같은 이름의 계정이 기존 DB에 있다면 기존 비밀번호를 바꾸지 않으므로 원래 비밀번호를 사용한다.
통합 로그 불러오기를 누르면 아직 정규화와 집계 함수를 완성하라는 안내가 나온다. 오류가 아니라 학생이 채울 부분이 남은 상태다. 계정과 화면을 만드는 대신 이 빈 분석 부분을 채우는 것이 오늘 할 일이다.
<details>
<summary>시작이 멈추거나 화면이 열리지 않으면</summary>
	Docker 명령을 찾지 못하거나 서버에 연결할 수 없다는 메시지이면 Docker Desktop을 켜고 실행 준비가 끝난 뒤 start-class.cmd를 다시 실행한다. 기존 DB나 작업 파일을 지우지 않는다.
	프로젝트 폴더의 Windows CMD
	```plain text
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml ps
	```
	Up은 실행 중이라는 뜻이다. Exit 또는 Restarting이면 아래 로그의 마지막 오류를 확인한다. 8081이나 8082 포트를 다른 실습에서 쓰고 있으면 그 실습을 정상 종료한 뒤 다시 시작한다.
	프로젝트 폴더의 Windows CMD
	```plain text
docker compose -f compose-general.yaml logs --tail 20 general-api general-gateway
docker compose -f compose-monitor.yaml logs --tail 20 monitor-api monitor-web
	```
	start-class.cmd 자체가 없으면 현재 수업 시작본이 아닌 상태다. 같은 Day3의 옛 버전일 수도 있으므로 폴더를 지우거나 임의 파일로 메우지 말고 시작본 버전을 확인한다. 계정 비밀번호가 다르다는 이유로 DB 볼륨을 삭제하지 않는다.
</details>
## 3단계. 같은 요청이 남긴 두 원본 비교하기
### 앱의 JSON 기록을 읽자
수집한 파일 열기
1. VS Code 왼쪽에서 monitor → backend → learning → data → `case.json`을 연다.
2. app 아래의 두 기록에서 path와 status\_code를 찾는다. 파일은 수정하지 않는다.
app 안의 두 객체 — 읽기 쉽게 한 줄씩 펼친 모습
```json
{"method": "GET", "path": "/", "status_code": 200}
{"method": "GET", "path": "/training-missing", "status_code": 404}
```
JSON은 항목 이름과 값을 짝지어 담는 자료 형식이다. method는 요청 방법, path는 요청 경로, status\_code는 응답 상태다. GET은 읽기 요청이고, 200은 정상 응답, 404는 해당 경로를 찾지 못했다는 뜻이다.
준비 도구가 목록 /와 없는 경로 /training-missing을 한 번씩 요청했다. 따라서 404는 이번에 일부러 만든 비교 대상이며, 이 숫자 하나로 공격이라고 판단하지 않는다.
### Nginx의 글자 줄을 읽자
다른 출처와 비교하기
1. 같은 `case.json`의 nginx 아래 두 문자열을 찾는다.
2. 각 줄의 GET 뒤 경로와 큰따옴표 다음 상태 숫자를 앱 기록과 비교한다.
Nginx combined 형식 예시 — 내 주소·시각·크기는 다르다
```plain text
127.0.0.1 - - [14/Oct/2026:09:00:00 +0900] "GET / HTTP/1.1" 200 1024 "-" "python-requests/2.32.3"
127.0.0.1 - - [14/Oct/2026:09:00:00 +0900] "GET /training-missing HTTP/1.1" 404 207 "-" "python-requests/2.32.3"
```
Nginx는 앱 앞에서 요청을 받아 전달하는 웹서버다. combined는 이 서버가 접속 기록을 한 줄에 남기는 형식 이름이다. 이 원본에는 status\_code라는 항목명이 없고 정해진 위치에 상태 숫자가 있다.
`case.json`은 두 원본을 담는 바깥 포장이다. 그 안의 Nginx 기록 자체가 JSON 객체로 바뀐 것은 아니다. 파일에서 보이는 `\"`는 문자열 속 큰따옴표를 저장한 표시다.
<table header-row="true" fit-page-width="true">
<tr>
<td>비교할 것</td>
<td>Flask 앱 원본</td>
<td>Nginx 원본</td>
</tr>
<tr>
<td>요청 방법·경로</td>
<td>method와 path의 값</td>
<td>"GET / HTTP/1.1" 안에 함께 들어 있음</td>
</tr>
<tr>
<td>응답 상태</td>
<td>status\_code의 숫자 200 또는 404</td>
<td>요청 문자열 뒤에 글자로 적힌 200 또는 404</td>
</tr>
<tr>
<td>시각</td>
<td>원본에 없음</td>
<td>\[ \] 안에 시각과 UTC와의 차이가 있음</td>
</tr>
</table>
원본을 각각 읽으면 같은 질문에도 다른 코드가 필요하다. 둘 다 status\_code라는 숫자로 맞추면 이후에는 status\_code >= 400이라는 한 조건을 적용할 수 있다.
## 4단계. 어느 코드와 설정이 로그를 만드는지 찾기
### 앱에서는 응답 뒤에 기록 함수를 호출한다
Flask는 이 게시판의 Python 웹 프로그램을 만드는 도구다. VS Code에서 general/app.py를 열어 다음 등록 코드를 찾자. 아래는 읽기용 발췌이며 파일을 교체하지 않는다.
general/app.py — 기록 함수를 연결한 부분
```python
from request_logging import record_request

app.after_request(record_request)
```
after\_request는 응답 객체를 만든 뒤, 사용자에게 보내기 전에 실행할 함수를 등록한다. 그래서 요청 경로뿐 아니라 응답 상태도 기록할 수 있다. 함수를 정의만 해 둔 것이 아니라 여기서 실제 요청 처리에 연결했다.
이제 general/request\_logging.py의 record\_request를 열자. 아래 부분이 app에서 본 세 값을 만든다.
general/request\_logging.py — 값 생성과 출력 부분, 읽기용 발췌
```python
event = {
    'method': request.method,
    'path': request.path,
    'status_code': response.status_code,
}
log_line = json.dumps(event, ensure_ascii=False)
print(log_line, flush=True)
```
request는 지금 들어온 요청이고 response는 처리 후 내보낼 응답이다. json.dumps는 이 세 값을 JSON 글자로 바꾸며, print가 컨테이너 실행 로그에 한 줄을 출력한다. 수업용 파일 기록 코드도 같은 줄을 app.jsonl에 덧붙인다.
같은 함수에서 파일에 남기는 부분 — 읽기용 발췌
```python
log_path = os.environ.get('REQUEST_LOG_PATH')
if log_path:
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_line + '\n')
    except OSError:
        current_app.logger.warning('실습용 JSONL 파일에 요청 기록을 쓰지 못했습니다.')
```
준비된 실행 설정이 REQUEST\_LOG\_PATH에 /classroom-logs/app.jsonl을 넣는다. open의 a는 기존 줄 뒤에 덧붙이는 방식이고 write가 같은 JSON과 줄바꿈을 파일에 쓴다. 컨테이너의 이 폴더는 내 프로젝트의 classroom-logs와 연결되어 있다.
따라서 여기에는 없는 사용자 이름이나 시각을 나중에 알아낸 것처럼 채우면 안 된다. 앱의 원본에 없는 시각은 정규화 결과에서도 비워 둔다.
### Nginx에서는 접속 로그 설정이 기록한다
gateways/general.conf를 열고 access\_log와 proxy\_pass를 찾자. 이 설정은 이미 적용되어 있으므로 직접 다시 입력하지 않는다.
gateways/general.conf — 준비된 설정
```plain text
server {
    listen 80;
    access_log /classroom-logs/nginx.log combined;

    location / {
        proxy_pass http://general-api:5000;
        proxy_set_header Host $http_host;
    }
}
```
proxy\_pass가 요청을 일반 앱으로 전달하고, access\_log가 Nginx에서 처리한 요청을 지정 파일에 남긴다. Flask의 print가 Nginx 로그까지 만드는 것이 아니다. 서로 다른 프로그램이 같은 요청을 각자 기록한다.
### 수집기는 기록을 옮기고, 정규화 함수는 모양을 바꾼다
<table header-row="true" fit-page-width="true">
<tr>
<td>파일·도구</td>
<td>역할</td>
</tr>
<tr>
<td>`classroom-logs/app.jsonl`</td>
<td>앱이 계속 덧붙이는 원본 JSON 줄</td>
</tr>
<tr>
<td>`classroom-logs/nginx.log`</td>
<td>Nginx가 계속 덧붙이는 원본 접속 기록</td>
</tr>
<tr>
<td>`general/collect_classroom.py`</td>
<td>준비된 도구. 요청 두 건을 보내 두 출처의 이번 기록을 복사한다.</td>
</tr>
<tr>
<td>`monitor/backend/learning/data/case.json`</td>
<td>오늘 분석할 앱 2행·Nginx 2행을 함께 보관한 입력 파일</td>
</tr>
</table>
`case.json`을 다시 읽는 동작은 새 요청을 보내는 동작이 아니다. 이후에는 이 입력 파일을 그대로 사용한다. 서비스 로그나 DB의 전체 누적 건수와 이 파일의 네 행을 혼동하지 말자.
## 5단계. 바꿀 모양과 남겨 둘 원본 정하기
공통 항목을 먼저 약속해 두자. 형식이 맞으면 변환 뒤의 코드는 출처별 원본 모양을 다시 알 필요가 없다.
<table header-row="true" fit-page-width="true">
<tr>
<td>공통 항목</td>
<td>뜻과 규칙</td>
</tr>
<tr>
<td>id</td>
<td>이번 입력 파일 안의 행 이름. app-1과 nginx-1처럼 출처와 순서로 구분한다.</td>
</tr>
<tr>
<td>source</td>
<td>app 또는 nginx. 어느 프로그램에서 나온 로그인지 남긴다.</td>
</tr>
<tr>
<td>time</td>
<td>원본 시각을 공통 표현으로 바꾼다. 앱처럼 시각이 없으면 None으로 둔다.</td>
</tr>
<tr>
<td>method · path · status\_code</td>
<td>요청 방법·경로·응답 상태. 상태는 두 출처 모두 숫자로 맞춘다.</td>
</tr>
<tr>
<td>raw</td>
<td>변환 전 원본. 앱은 원본 객체, Nginx는 원본 문자열을 그대로 남긴다.</td>
</tr>
</table>
None은 Python에서 값이 없음을 나타낸다. 시각이 없는 것을 지금 시각이나 0으로 채우지 않는다. 화면에는 원본에 없음으로 보여 줄 것이다.
준비 도구가 보낸 요청은 두 건이지만, 각 요청을 앱과 Nginx가 기록하므로 로그는 네 행이다. 합친 뒤 네 번 요청했다고 말하지 않는다. 같은 경로와 상태라는 이유만으로 한 행을 지우지도 않는다.
- `case.json`에서 app2행·nginx2행을 찾는다.
- 앱 로그의 생성 함수와 Nginx의 access\_log 설정을 각각 짚는다.
- 오늘 직접 만들 부분은 정규화·합치기·집계이고, 자동 차단은 아니라는 것을 구분한다.
## 확인문제
**확인문제 1.** 오늘 SIEM·XDR·SOAR 중 어떤 기능을 직접 만드는가?
<details>
<summary>정답과 해설</summary>
	SIEM의 일부인 서로 다른 로그 정규화·통합 조회·공통 조건 집계를 만든다. 전체 제품이나 자동 차단은 구현하지 않는다.
</details>
**확인문제 2.** 계정 생성과 로그 수집기를 처음부터 구현해야 하는가?
<details>
<summary>정답과 해설</summary>
	아니다. 시작본과 start-class.cmd가 계정·서비스·수집 입력을 준비한다. 학생은 변환과 분석에 집중한다.
</details>
**확인문제 3.** Flask와 Nginx의 상태 값은 원본에서 어떻게 다르게 생겼는가?
<details>
<summary>정답과 해설</summary>
	앱은 status\_code라는 이름의 숫자이고, Nginx는 요청 문자열 뒤의 정해진 위치에 적힌 글자다.
</details>
**확인문제 4.** 앱의 record\_request 함수는 어느 코드에서 실제 요청과 연결되는가?
<details>
<summary>정답과 해설</summary>
	general/app.py의 app.after\_request(record\_request)가 연결한다. 응답 객체가 만들어진 뒤 상태를 읽어 기록한다.
</details>
**확인문제 5.** Flask의 print가 Nginx 접속 로그도 만드는가?
<details>
<summary>정답과 해설</summary>
	아니다. 앱의 print는 앱 실행 로그를 출력하고, Nginx는 access\_log 설정에 따라 자기 접속 로그를 쓴다.
</details>
**확인문제 6.** `case.json` 안의 Nginx 값은 이미 공통 딕셔너리로 변환되었는가?
<details>
<summary>정답과 해설</summary>
	아니다. JSON 파일 안에 담겼어도 원본은 긴 문자열이다. 그 안에서 필요한 값을 꺼내는 변환이 남아 있다.
</details>
**확인문제 7.** 앱 원본에 없는 시각은 무엇으로 채울 것인가?
<details>
<summary>정답과 해설</summary>
	None으로 비워 둔다. 현재 시각이나 감시 DB의 수신시각을 앱 원본 시각처럼 쓰지 않는다.
</details>
**확인문제 8.** 준비 도구는 요청 두 건을 보냈는데 왜 로그가 네 행인가?
<details>
<summary>정답과 해설</summary>
	두 요청 각각을 Flask와 Nginx가 한 번씩 기록했기 때문이다. 두 출처의 관측 수를 요청 수와 구분한다.
</details>
**확인문제 9.** 404가 보이면 공격이 확인된 것인가?
<details>
<summary>정답과 해설</summary>
	아니다. 이번에는 없는 경로를 일부러 요청했다. 404는 경로를 찾지 못했다는 결과이며 공격의 충분한 근거가 아니다.
</details>
**확인문제 10.** 공통 행에 source와 raw를 왜 남기는가?
<details>
<summary>정답과 해설</summary>
	어느 프로그램의 기록인지 구분하고, 변환 결과가 맞는지 원본으로 돌아가 확인하기 위해서다.
</details>
두 원본은 모양이 다르지만 같은 요청 방법·경로·상태를 담고 있다. 다음에는 앱 기록 한 행부터 공통 모양으로 바꿔 보자.