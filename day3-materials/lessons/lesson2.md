게시판을 한 번 사용했는데 앱 말고도 기록을 남기는 곳이 있다. 요청을 먼저 받는 Nginx의 로그를 앱 원본과 나란히 읽고, 둘이 감시 화면까지 오는 길을 확인하자.
이번 시간에 확인할 흐름이다.
<image src="../assets/lesson2.svg">설명용 흐름도 — 왼쪽의 실제 입력을 가운데에서 처리해 오른쪽 결과로 확인한다.</image>
- 일반 게시판에서 만든 새 기록을 앱·Nginx 양쪽에서 찾는다.
- 생성·수집·정규화가 서로 다른 일임을 실제 파일과 코드로 설명한다.
<table_of_contents/>
## 1단계. 앞단 웹서버를 거쳐 게시판 사용하기
Nginx는 브라우저 요청을 먼저 받아 게시판 앱으로 전달하는 웹서버다. 새로운 사이트에 접속하는 것이 아니라, 지금까지 사용한 8081 주소 안에 이 경유 과정이 있다.
```plain text
브라우저 localhost:8081 → general-gateway(Nginx) → general-api(Flask)
                         nginx.log 작성           app.jsonl 작성
```
### 새 글을 쓰고 기록을 찾자
게시판 동작 만들기
1. [게시판 목록](http://localhost:8081)을 연다. 로그아웃 상태라면 /login에서 class-student와 classroom1234!로 로그인한다.
2. 새 게시글 작성을 누른다. 제목에 로그 수집 연습, 내용에 내가 작성한 글을 입력하고 게시글 저장을 누른다.
3. [감시 화면](http://localhost:8082)에서 원본 로그 불러오기를 누른다. 완성 시연 화면에서는 로그 새로고침을 누른다. 로그인이 필요하면 class-operator와 classroom1234!를 사용한다.
앱 원본에서 POST /board/new를 찾자. 정상 저장은 303 응답 후 글 페이지로 이동한다. 따라서 저장 요청과 이동한 페이지 요청이 따로 보이는 것이 정상이다.
```plain text
{"method": "POST", "path": "/board/new", "status_code": 303}
```
303은 다른 주소를 이어서 열라는 응답이다. 새 글을 만든 동작을 오류로 세지 않으며, 제목이나 글 본문 자체가 이 세 항목 로그에 저장되는 것도 아니다.
## 2단계. 같은 경로의 서로 다른 모양 비교하기
### Nginx 쪽 기록도 찾자
두 원본 대조하기
1. 감시 화면의 Nginx 원본에서 POST /board/new가 들어간 줄을 찾는다.
2. 큰따옴표 안 요청과 그 뒤의 상태 숫자를 앱 원본과 비교한다.
```plain text
127.0.0.1 - - [14/Oct/2026:10:00:00 +0900] "POST /board/new HTTP/1.1" 303 219 "-" "Mozilla/5.0"
```
Nginx 원본의 형태를 보여 주는 예시다. 내 주소·시각·크기·브라우저 표시는 다르다. combined는 이 접속 로그 형식의 이름이며, 요청과 상태가 한 줄의 정해진 자리에 적힌다.
<table header-row="true" fit-page-width="true">
<tr>
<td>읽을 값</td>
<td>앱 JSON</td>
<td>Nginx 문자열</td>
</tr>
<tr>
<td>방법</td>
<td>method의 POST</td>
<td>첫 큰따옴표 안의 POST</td>
</tr>
<tr>
<td>경로</td>
<td>path의 /board/new</td>
<td>POST 뒤의 /board/new</td>
</tr>
<tr>
<td>상태</td>
<td>status\_code의 303</td>
<td>요청 큰따옴표가 닫힌 뒤의 303</td>
</tr>
</table>
앱에는 이름으로 읽을 항목이 있지만 Nginx에는 문자열을 나눠야 한다. 두 원본이 모였다는 것만으로 같은 코드로 읽을 수 있는 것은 아니다.
### Nginx의 어느 설정이 기록할까
VS Code에서 gateways/general.conf를 열어 다음 두 줄을 찾자. 준비된 설정의 읽기용 발췌이며 바꾸지 않는다.
`gateways/general.conf` — 서로 다른 역할의 두 설정
```plain text
access_log /classroom-logs/nginx.log combined;
proxy_pass http://general-api:5000;
```
proxy\_pass는 요청 전달, access\_log는 Nginx의 파일 기록을 담당한다. Flask의 JSON 기록 함수가 Nginx 로그도 만드는 것이 아니라 각 프로그램이 자기 위치에서 남긴다.
## 3단계. 두 파일이 감시 화면으로 모이는 길 확인하기
### Docker로 Flask 원본 파일 열기
감시 화면에 나온 기록이 실제 어디에 저장되는지 직접 열어보자. 실행 중인 컨테이너 안의 Linux 명령을 쓰므로 Windows나 Mac에 Linux를 따로 설치하지 않는다.
프로젝트 터미널 열기
1. VS Code의 파일 → 폴더 열기에서 사이트를 실행한 mini-watch-m5d3 폴더를 연다. Windows 기본 실습 경로는 `C:\work\mini-watch-m5d3`이며, 다른 곳에 clone했다면 그 실제 폴더를 연다.
2. 터미널 → 새 터미널을 누른다. 현재 위치가 방금 연 프로젝트 폴더인지 확인하고 아래 명령을 실행한다. 게시판과 감시 서비스는 켜 둔다.
프로젝트 폴더 터미널 — Flask 컨테이너 안으로 들어가기
```bash
docker compose -f compose-general.yaml exec general-api sh
```
`-f compose-general.yaml`은 사용할 설정 파일을 고른다. `exec general-api sh`는 실행 중인 Flask 컨테이너에서 명령을 입력할 셸을 열며, 새 컨테이너를 만드는 명령이 아니다.
이제 컨테이너 안이다. `ls -lh`로 파일의 이름과 크기를 확인하고, `tail -n 5`로 마지막 다섯 줄을 읽어보자.
Flask 컨테이너 안 — 두 줄을 순서대로 실행
```bash
ls -lh /classroom-logs/app.jsonl
tail -n 5 /classroom-logs/app.jsonl
```
파일 정보 다음에 `method`·`path`·`status_code`가 있는 JSON 줄이 보인다. 최근 기록이 다섯 줄보다 적으면 있는 만큼만 나오며, 요청에 따라 내용은 달라진다.
이 파일은 `general/request_logging.py`의 `record_request`가 요청 처리 뒤에 추가한다. 준비된 `REQUEST_LOG_PATH` 값이 `/classroom-logs/app.jsonl`이므로 이 경로에 저장된다.
Flask 셸에서 나오기
```bash
exit
```
`exit`는 지금 연 셸만 끝낸다. Flask 서버는 계속 켜져 있고, 터미널은 내 PC의 프로젝트 폴더로 돌아온다.
### Docker로 Nginx 원본 파일 열기
이번에는 같은 요청을 앞에서 받은 Nginx의 파일을 열어보자. 방금 돌아온 내 PC 터미널에서 실행한다.
프로젝트 폴더 터미널 — Nginx 컨테이너 안으로 들어가기
```bash
docker compose -f compose-general.yaml exec general-gateway sh
```
Nginx 컨테이너 안 — 두 줄을 순서대로 실행
```bash
ls -lh /classroom-logs/nginx.log
tail -n 5 /classroom-logs/nginx.log
```
이번에는 JSON의 항목 이름 대신 주소·시각·요청·상태가 이어진 문자열이 나온다. 앞에서 본 `gateways/general.conf`의 `access_log /classroom-logs/nginx.log combined;`가 이 파일을 기록한다.
Nginx 셸에서 나와 내 PC 터미널로 돌아가기
```bash
exit
```
`docker compose -f compose-general.yaml logs`는 일반 서비스 컨테이너의 표준 출력 기록을 보는 명령이다. 지금 한 것은 그 화면이 아니라 `/classroom-logs` 안의 원본 파일을 직접 읽는 일이다.
### 공유 폴더와 읽기 함수를 보자
방금 컨테이너에서 읽은 두 파일은 내 프로젝트의 `classroom-logs` 폴더에서도 보인다. 준비된 Compose 설정이 이 폴더를 각 컨테이너의 `/classroom-logs`에 연결하므로, 따로 복사한 파일이 아니라 같은 원본을 보는 것이다.
```plain text
classroom-logs/
├─ app.jsonl  ← Flask가 추가
└─ nginx.log  ← Nginx가 추가
       ↓ 감시 앱은 읽기만
learning/log_data.py → 원본 로그 화면
```
이 수업의 수집은 여러 서버에 에이전트를 설치하는 대신 공유 폴더의 두 파일을 감시 앱 한곳에서 읽는 방식이다. 원본을 보여 주는 기능은 이미 준비되어 있다.
`monitor/backend/learning/log_data.py`의 아래 함수를 읽어보자. read\_complete\_lines는 준비된 파일 읽기 함수이고 json.loads는 JSON 문자열을 Python 값으로 바꾸는 함수다.
`log_data.py` — 원본을 읽는 부분, 읽기용 발췌
```python
def read_logs():
    return {
        "app": [json.loads(line) for line in read_complete_lines("app.jsonl")],
        "nginx": read_complete_lines("nginx.log"),
    }
```
app 쪽은 JSON을 객체로 읽고 nginx 쪽은 글자 줄을 그대로 둔다. 아직 같은 열로 바꾼 것이 아니므로 수집과 정규화는 구분된다.
### 추가 요청도 두 원본에 나타나는지 보자
누적 수집 확인하기
1. 일반 게시판 탭에서 [http://localhost:8081/collect-check](http://localhost:8081/collect-check)을 연다.
2. 내 PC의 프로젝트 터미널로 돌아와 아래 두 명령을 실행한다.
프로젝트 폴더 터미널 — 두 파일을 다시 읽기
```bash
docker compose -f compose-general.yaml exec general-api tail -n 5 /classroom-logs/app.jsonl
docker compose -f compose-general.yaml exec general-gateway tail -n 5 /classroom-logs/nginx.log
```
이번에는 `sh` 대신 `tail`을 바로 실행하므로 파일을 읽은 뒤 자동으로 내 PC 터미널로 돌아온다. 두 출력에서 `/collect-check`와 `404`를 찾자. 다른 요청이 뒤에 많이 쌓였다면 `-n 5`를 `-n 20`으로 바꿔 더 읽는다.
감시 화면에서 원본 로그 불러오기를 다시 누른다. 완성 시연 화면에서는 로그 새로고침을 누르고 경로 검색에 `/collect-check`를 입력한다. 양쪽 원본의 경로와 상태가 방금 파일에서 읽은 값과 같은지 확인하자.
버튼은 저장된 예제 파일이 아니라 현재 두 로그 파일을 다시 읽는다. 기록 시점이 조금 다를 수 있으므로 한쪽이 아직 없으면 잠시 뒤 다시 누른다. 전체 줄 수가 정확히 같아야 하는 실습은 아니다.
## 확인문제
**확인문제 1.** Nginx를 보려면 별도 사이트에서 활동해야 하는가?
<details>
<summary>정답과 해설</summary>
	아니다. `localhost:8081`로 들어오는 게시판 요청을 Nginx가 먼저 받고 앱에 전달한다.
</details>
**확인문제 2.** 게시글 저장 요청의 방법과 경로는 무엇인가?
<details>
<summary>정답과 해설</summary>
	POST /board/new이다. 새 글의 데이터를 보내는 요청이다.
</details>
**확인문제 3.** 정상 저장의 303은 무엇을 뜻하는가?
<details>
<summary>정답과 해설</summary>
	다른 주소를 이어서 열라는 응답이다. 저장 후 글 페이지로 이동한다.
</details>
**확인문제 4.** Nginx에서 요청을 앱에 전달하는 설정은 무엇인가?
<details>
<summary>정답과 해설</summary>
	proxy\_pass이다. 일반 게시판 앱인 general-api:5000으로 전달한다.
</details>
**확인문제 5.** Nginx가 자기 접속 로그를 남기는 설정은 무엇인가?
<details>
<summary>정답과 해설</summary>
	access\_log이다. 지정한 파일에 combined 형식으로 남긴다.
</details>
**확인문제 6.** 앱 상태와 Nginx 상태는 원본에서 어떻게 찾는가?
<details>
<summary>정답과 해설</summary>
	앱은 status\_code라는 이름으로, Nginx는 요청 큰따옴표가 끝난 뒤의 숫자로 찾는다.
</details>
**확인문제 7.** 두 원본은 내 프로젝트의 어느 폴더에 있는가?
<details>
<summary>정답과 해설</summary>
	classroom-logs의 app.jsonl과 `nginx.log`이다. 준비된 실행 설정이 폴더를 연결한다.
</details>
**확인문제 8.** read\_logs가 실행되면 Nginx도 곧바로 공통 객체가 되는가?
<details>
<summary>정답과 해설</summary>
	아니다. Nginx는 문자열 목록 그대로 읽는다. 정규화 함수가 별도로 필요하다.
</details>
**확인문제 9.** 버튼을 다시 누르면 왜 방금 만든 경로가 보이는가?
<details>
<summary>정답과 해설</summary>
	현재 파일을 다시 읽기 때문이다. 앱과 Nginx가 새 요청의 줄을 계속 추가한다.
</details>
**확인문제 10.** 앱 로그 두 줄과 Nginx 두 줄을 서로 다른 요청 네 건이라 해도 되는가?
<details>
<summary>정답과 해설</summary>
	안 된다. 서로 다른 위치의 관측이므로 같은 요청이 양쪽에 기록될 수 있다.
</details>
두 원본은 한곳에서 볼 수 있지만 형식은 다르다. 다음에는 앱부터 공통 항목으로 바꿔 같은 조건으로 읽을 준비를 한다.
