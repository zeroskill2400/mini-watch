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
3. [감시 화면](http://localhost:8082)에서 원본 로그 불러오기를 누른다. 로그인이 필요하면 class-operator와 classroom1234!를 사용한다.
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
### 공유 폴더와 읽기 함수를 보자
VS Code에서 classroom-logs 폴더를 열면 app.jsonl과 `nginx.log`가 있다. 준비된 Compose 설정이 이 폴더를 앱·Nginx·감시 앱에 연결해 두었다.
```plain text
classroom-logs/
├─ app.jsonl  ← Flask가 추가
└─ nginx.log  ← Nginx가 추가
       ↓ 감시 앱은 읽기만
learning/log_data.py → 원본 로그 화면
```
이 수업의 수집은 여러 서버에 에이전트를 설치하는 대신 공유 폴더의 두 파일을 감시 앱 한곳에서 읽는 방식이다. 원본을 보여 주는 기능은 이미 준비되어 있다.
monitor/backend/learning/log\_data.py의 아래 함수를 읽어보자. read\_complete\_lines는 준비된 파일 읽기 함수이고 json.loads는 JSON 문자열을 Python 값으로 바꾸는 함수다.
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
2. 감시 화면의 원본 로그 불러오기를 다시 누르고 앱·Nginx 양쪽에서 /collect-check와 404를 찾는다.
버튼은 저장된 예제 파일이 아니라 현재 두 로그 파일을 다시 읽는다. 기록 시점이 조금 다를 수 있으므로 한쪽이 아직 없으면 잠시 뒤 다시 누른다. 전체 줄 수가 정확히 같아야 하는 실습은 아니다.
## 확인문제
**확인문제 1.** Nginx를 보려면 별도 사이트에서 활동해야 하는가?
<details>
<summary>정답과 해설</summary>
	아니다. localhost:8081로 들어오는 게시판 요청을 Nginx가 먼저 받고 앱에 전달한다.
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