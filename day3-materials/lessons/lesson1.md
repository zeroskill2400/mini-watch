일반 서비스에서 글을 쓰고 고치면 요청이 발생한다. 그 요청과 처리 결과를 남긴 자료가 요청 기록이다. 이번 시간에는 general에서 여러 행동을 해 보고 monitor에 모인 기록과 대조하자.
일반 서비스의 게시글 활동을 감시 표에서 확인하는 것이 목표다.
<image src="../assets/lesson1.svg">설명용 구성도. 일반 앱은 게시글 기능을 처리하고, 감시 앱에 요청 기록을 보내 별도 DB에 저장한다.</image>
왼쪽은 글을 다루는 일반 서비스다. 가운데 화살표로 방법·경로·상태를 보내면 오른쪽 감시 API가 요청 종류를 붙여 저장한다. 감시 화면은 감시 API에 조회 요청을 보내고, API가 DB에서 읽어 돌려준 기록을 표로 보여 준다.
- 조회·작성·수정·삭제 요청을 감시 표에서 구분한다.
- 일반 화면 결과와 요청의 방법·경로·상태를 함께 확인한다.
```plain text
C:\work\mini-watch-m5d3\
├─ general\                  ← 요청을 처리하고 기록을 보냄
├─ monitor\backend\          ← 기록을 받고 DB에 저장
├─ monitor\next-frontend\    ← 저장된 기록을 표로 조회
├─ compose-general.yaml
└─ compose-monitor.yaml
```
<table_of_contents/>
## 1단계. 동작 전후의 DB와 감시 기록 비교하기
이번에는 동작 전 DB → 일반 화면의 요청 → 동작 후 DB → 감시 표 순서로 확인한다. 먼저 준비한 저장소의 루트에서 Windows CMD를 연다.
도구·Git·Compose·계정 준비가 안 됐다면 [4과목 공통 실습 환경 준비](https://app.notion.com/p/3f9ae3d1800c81b0ba61cf483bd35724)를 먼저 마친다.
### 동작 전 DB의 현재 기록 확인하기
새 감시 DB의 http\_events는 빈 테이블로 시작한다. Docker 실행만으로 general의 활동 기록 한 건이 만들어지지는 않는다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-db psql -U sample -d monitor_db -c "SELECT id, method, path, status_code, event_type FROM http_events ORDER BY id DESC LIMIT 5;"
```
아래는 새 DB가 아직 일반 서비스의 요청을 받지 않았을 때의 출력 형태 예시다.
```plain text
 id | method | path | status_code | event_type
----+--------+------+-------------+------------
(0 rows)
```
환경 준비 중 일반 화면을 열거나 로그인했다면 이미 그 요청이 저장됐을 수 있다. 기존 DB를 이어 쓰는 학생도 이전 행이 보이므로 현재 최근 행의 ID를 읽어 두고 다음 동작 전후를 비교한다.
SELECT는 저장된 행을 읽는 SQL이다. 이 명령은 최근 5건을 읽으며 DB를 수정하지 않는다.
### 일반 화면에서 요청을 만들고 DB 다시 보기
이번에 만든 요청이 늘어나는지 확인하자.
1. 일반 화면 http://localhost:8081을 열어 게시글 목록을 확인한다. 이미 열려 있다면 새로고침한다.
2. 아래의 같은 DB 읽기 명령을 다시 실행한다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-db psql -U sample -d monitor_db -c "SELECT id, method, path, status_code, event_type FROM http_events ORDER BY id DESC LIMIT 5;"
```
아래는 새로 저장된 목록 조회 행의 출력 형태 예시다. 12는 예시 ID이며 실제 조회 결과의 ID와 행 수는 내 DB에 따라 다르다.
```plain text
 id | method | path | status_code | event_type
----+--------+------+-------------+------------
 12 | GET    | /    |         200 | post_list
(1 row)
```
동작 전 결과와 비교해 새 ID의 GET·경로 /·상태200·종류 post\_list 행을 찾는다. 로그인이나 다른 화면 요청도 기록되므로 전체 결과가 정확히 한 행이라는 뜻은 아니다.
LIMIT 5는 최대 5건을 읽는 조건이다. 일반 DB의 게시글과 감시 DB의 http\_events 요청 기록은 서로 다른 목적의 자료다.
### 감시 화면에서 수집된 요청 확인하기
DB에서 본 요청 형태를 감시 표에서 확인하자.
1. 감시 화면 http://localhost:8082에서 자신의 감시 계정으로 로그인한다.
2. 기록 불러오기를 누르고 post\_list·GET·경로 /·상태200인 행을 찾는다.
이 표는 monitor가 자기 DB에서 읽어 온 기록이다. DB에서는 ID로 전후를 비교했고, 현재 감시 표에서는 종류·방법·경로·상태를 확인한다.
### 전송 전 JSON과 dump 파일 보기
general은 요청 결과를 JSON으로 표준 출력에 남긴 뒤 monitor로 보낸다. 표준 출력은 실행 중인 프로그램이 콘솔로 내보내는 글이며 Docker 실행 로그에서 읽을 수 있다.
Windows CMD
```plain text
docker compose -f compose-general.yaml logs --tail 10 --no-color general-api
```
```plain text
{"method": "GET", "path": "/", "status_code": 200}
```
위는 방금 목록을 읽은 요청의 JSON 부분이다. 로그 앞에 서비스 이름이 붙거나 시작·오류 메시지가 함께 나올 수 있다.
전송 전 JSON에는 method·path·status\_code가 있다. monitor는 종류를 분류하고 DB가 ID와 수신 시각을 붙인다. 따라서 DB의 행은 전송 JSON을 그대로 저장한 원문 전체와 구분한다.
<details>
<summary>실행 로그를 dump 파일로 저장해 보기</summary>
	dump는 지금 읽을 수 있는 기록을 파일로 내보낸 사본이다. 아래는 general의 실행 로그 전체를 새 logs 폴더의 `general-raw.log`에 저장한다.
	Windows CMD
	```plain text
if not exist logs mkdir logs
docker compose -f compose-general.yaml logs --no-color --no-log-prefix general-api > logs\general-raw.log
	```
	VS Code에서 logs/general-raw.log를 열어 GET·경로 /·상태 200인 JSON 줄을 찾는다. 이 파일에는 general이 출력한 JSON과 실행 메시지가 함께 들어 있다. 같은 명령을 다시 실행하면 이 파일을 현재 읽을 수 있는 로그로 갱신한다.
	JSONL은 JSON 하나를 한 줄에 담는 파일형식이다. DB에 저장된 최신 50건만 구조화한 파일이 필요하면 아래 준비 도구를 사용한다.
	Windows CMD
	```plain text
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.export_events > logs\general-events.jsonl
	```
	logs/general-events.jsonl은 감시DB 행의 사본이며 전송 당시 원문 전체가 아니다. 일반 출력에 있어도 전송 실패로 감시DB에 없을 수 있으므로 두 자료를 대조할 수 있다.
</details>
## 2단계. 일반 화면에서 새 글 쓰기
글을 쓰기 전에 일반 화면에서 자신의 일반 계정으로 로그인한다. 이미 로그인했다면 그 상태를 사용한다. 감시 계정으로 로그인한 상태와 일반 계정의 로그인 상태는 별개다.
이번 관찰에 사용할 실습용 글을 하나 만든다. 입력한 글 내용은 일반 DB에, 그 요청의 기록은 감시 DB에 각각 남는다.
실습용 게시글 만들기
1. 일반 화면에서 새 게시글 작성을 누른다.
2. 제목은 Day3 수집 연습, 내용은 일반 서비스 행동을 확인한다.로 입력하고 게시글 저장을 누른다.
- 일반 화면에 방금 입력한 제목과 내용이 보인다.
- 주소의 /board/ 뒤 숫자를 확인한다. 이 숫자는 내가 만든 글 번호다.
작성 요청 찾기
1. 감시 화면으로 옮겨 기록 불러오기를 누른다.
2. post\_create\_request / POST / /board/new인 행을 찾는다.
<table header-row="true" fit-page-width="true">
<tr>
<td>종류</td>
<td>방법</td>
<td>경로</td>
<td>상태</td>
</tr>
<tr>
<td>`post_create_request`</td>
<td>POST</td>
<td>`/board/new`</td>
<td>303</td>
</tr>
<tr>
<td>`post_view`</td>
<td>GET</td>
<td>`/board/내 글 번호`</td>
<td>200</td>
</tr>
</table>
표의 경로에 적은 내 글 번호는 설명용 자리표시다. 실제 표에는 /board/3처럼 내가 만든 글의 번호가 들어간다. 예시의 3을 그대로 입력하지 않는다.
POST는 입력한 내용을 보내는 요청이고 GET은 화면이나 자료를 읽는 요청이다. 저장 뒤에는 다음 화면으로 이동하라는 303 응답이 오고, 브라우저가 상세 화면을 GET으로 읽어 200 응답을 받는다. 버튼 한 번으로 여러 요청 기록이 생길 수 있다.
post\_create\_request는 글 작성 요청이라는 뜻이다. 303만으로 작성 완료를 확정하지 않는다. 미로그인 요청도 로그인 화면으로 이동할 수 있으므로, 완료는 일반 화면에 실제 새 글이 보이는지 함께 확인한다.
## 3단계. 조회와 수정을 기록에서 찾기
조회 기록 확인
1. 일반 화면에서 목록으로를 누르고 내가 만든 글 제목을 다시 누른다.
2. 감시 화면에서 기록 불러오기를 누른다.
<table header-row="true" fit-page-width="true">
<tr>
<td>종류</td>
<td>무엇을 읽었는가</td>
<td>방법·경로</td>
</tr>
<tr>
<td>`post_list`</td>
<td>게시글 목록</td>
<td>GET /</td>
</tr>
<tr>
<td>`post_view`</td>
<td>게시글 상세</td>
<td>GET /board/내 글 번호</td>
</tr>
</table>
이름만 보지 말고 방법과 경로를 함께 읽는다. 일반 화면에서 한 동작이 어떤 요청으로 처리되었는지 연결해 보자.
수정 요청 확인
1. 일반 상세 화면에서 수정하기를 누른다.
2. 제목을 Day3 수집 연습 수정으로 바꾸고 수정 저장을 누른다.
3. 감시 화면에서 기록 불러오기를 누르고 post\_update\_request 행을 찾는다.
- 일반 화면에는 바꾼 제목이 보인다.
- 감시 표에는 POST /board/내 글 번호/edit / 303 요청이 남는다.
수정 화면을 여는 GET과 수정 내용을 보내는 POST는 서로 다른 요청이다. /edit 경로만 같다고 모두 글 수정 완료로 읽지 않는다.
## 4단계. 삭제와 실패한 조회도 확인하기
삭제 실습에는 이번에 만든 Day3 수집 연습 수정 글만 사용한다.
삭제 요청 확인
1. 그 글의 상세 화면에서 삭제하기를 누른다.
2. 삭제할 제목을 확인하고 삭제 확인을 누른다.
3. 목록에서 그 글이 사라졌는지 확인한 뒤 감시 화면의 기록 불러오기를 누른다.
- post\_delete\_request / POST / /board/내 글 번호/delete / 303 행이 보인다.
- 글을 삭제한 뒤에도 감시 표의 작성·수정·삭제 요청 기록은 남아 있다.
게시글은 일반 DB의 업무 자료이고 요청 기록은 감시 DB의 관찰 자료다. 글을 삭제했다고 이미 수집한 기록까지 삭제하지는 않는다.
없는 글 조회하기
1. 일반 화면 주소 뒤에 /board/방금 삭제한 글 번호를 입력한다.
2. 게시글을 찾을 수 없습니다.라는 화면을 확인한다.
3. 감시 화면에서 기록 불러오기를 누르고 request\_error인 GET 행의 상태 404를 확인한다.
404는 그 글을 찾을 수 없다는 응답이다. 삭제한 글을 조회하면 생길 수 있는 결과이며 이 기록만으로 공격이라고 판단하지 않는다.
## 5단계. 기록이 전달되는 흐름 살펴보기
지금 확인한 표는 monitor가 general 화면을 대신 처리해서 만든 것이 아니다. 일반 앱은 자기 요청을 처리하고, 그 결과를 감시 앱에 별도로 보낸다.
<table header-row="true" fit-page-width="true">
<tr>
<td>위치</td>
<td>하는 일</td>
</tr>
<tr>
<td>`general/request_logging.py`</td>
<td>요청 처리 뒤 method·path·status\_code를 전송한다.</td>
</tr>
<tr>
<td>`monitor/backend/routes/events.py`</td>
<td>POST /api/events에서 기록을 받는다.</td>
</tr>
<tr>
<td>`monitor/backend/event_rules.py`</td>
<td>받은 요청을 게시글 조회·작성 요청 등으로 구분한다.</td>
</tr>
<tr>
<td>`monitor/backend/repositories/events.py`</td>
<td>감시 DB에 저장하고 조회한다.</td>
</tr>
<tr>
<td>감시 화면</td>
<td>기록 불러오기를 누르면 저장된 기록을 읽어 표로 보여 준다.</td>
</tr>
</table>
```plain text
{"method": "POST", "path": "/board/new", "status_code": 303}
```
위 자료는 일반 앱이 보내는 기록 예시다. 글의 제목·본문·비밀번호는 담지 않는다. monitor는 이 방법과 경로에 post\_create\_request라는 이름을 붙인다.
기록을 받을 때는 POST /api/events, 화면에서 기록을 읽을 때는 GET /api/events를 사용한다. 경로가 같아도 요청 방법에 따라 역할이 다르다.
현재 전송은 연결 실패 때 일부 기록이 누락될 수 있다. 일반 화면이 성공했다는 사실과 monitor에 저장되었다는 사실을 따로 확인한다. 이번에는 실제 화면과 감시 표를 대조하며 수집 흐름을 익힌다.
Sentry는 앞 수업에서 앱 오류와 발생 위치를 확인하는 데 사용했다. 기존 오류 수집 코드는 유지한다. 이번 행동 기록은 general에서 monitor로 직접 보내며 Sentry 연결을 새로 설정하지 않는다.
## 6단계. 수집 결과를 한눈에 정리하기
<table header-row="true" fit-page-width="true">
<tr>
<td>일반 서비스에서 한 일</td>
<td>감시 표에서 확인할 종류</td>
</tr>
<tr>
<td>게시글 작성 요청</td>
<td>`post_create_request`</td>
</tr>
<tr>
<td>목록·상세 조회</td>
<td>`post_list` · `post_view`</td>
</tr>
<tr>
<td>게시글 수정 요청</td>
<td>`post_update_request`</td>
</tr>
<tr>
<td>게시글 삭제 요청</td>
<td>`post_delete_request`</td>
</tr>
<tr>
<td>삭제한 글 조회</td>
<td>`request_error` · 상태404</td>
</tr>
</table>
- 이번에 만든 글의 작성·수정·삭제 요청을 구분할 수 있다.
- 한 행동 뒤에 여러 요청이 생기는 이유를 설명할 수 있다.
- 일반 서비스의 처리 결과와 monitor 수집 여부를 각각 확인할 수 있다.
표는 최신 50건을 보여 주므로 오래된 행이 안 보인다고 DB에서 삭제되었다고 판단하지 않는다. 이 교시는 수집·조회까지 확인하며 이상 징후 판단은 다음 단계에서 붙인다.
## 확인문제
**확인문제 1.** general과 monitor는 각각 어떤 일을 하는가?
<details>
<summary>정답과 해설</summary>
	general은 게시글 기능을 처리하고 요청 결과를 보낸다. monitor는 그 기록을 받아 자기 DB에 저장하고 표로 조회한다.
</details>
**확인문제 2.** 일반 DB와 감시 DB, general의 실행 로그에는 각각 무엇이 남는가?
<details>
<summary>정답과 해설</summary>
	일반 DB에는 게시글, 감시DB의 http\_events에는 요청 기록이 저장된다. general 실행 로그에는 전송 전 JSON이 출력된다. 감시DB는 ID·수신 시각·종류를 더하므로 원문 전체와 같은 자료는 아니다.
</details>
**확인문제 3.** 게시글 저장 버튼 한 번 뒤에 POST와 GET 기록이 함께 생기는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	POST로 글 내용을 보내고 303으로 이동할 주소를 받은 뒤 브라우저가 상세 화면을 GET으로 읽기 때문이다.
</details>
**확인문제 4.** 303 응답만 보면 글 작성이 완료되었다고 확정할 수 있는가?
<details>
<summary>정답과 해설</summary>
	아니다. 303은 다른 화면으로 이동하라는 응답이다. 미로그인 요청도 이동할 수 있으므로 일반 화면에서 실제 새 글을 확인한다.
</details>
**확인문제 5.** 수정 화면을 연 것과 수정 내용을 저장한 것은 무엇으로 구분하는가?
<details>
<summary>정답과 해설</summary>
	같은 /edit 경로라도 GET은 화면 조회, POST는 수정 요청이다. 방법과 경로를 함께 확인한다.
</details>
**확인문제 6.** 일반 서비스에서 글을 삭제하면 이미 수집한 감시 기록도 지워지는가?
<details>
<summary>정답과 해설</summary>
	아니다. 글과 요청 기록은 서로 다른 DB에 저장되어 있고 글 삭제는 감시 기록 삭제 요청이 아니다.
</details>
**확인문제 7.** 삭제한 글을 다시 조회한 404를 곧바로 공격이라고 판단할 수 있는가?
<details>
<summary>정답과 해설</summary>
	아니다. 실제로 글이 없어 정상적인 사용자 조회에서도 404가 생길 수 있다. 처리 결과와 상황을 함께 봐야 한다.
</details>
**확인문제 8.** POST /api/events와 GET /api/events는 각각 무엇을 하는가?
<details>
<summary>정답과 해설</summary>
	POST는 general이 보낸 기록을 monitor가 받는 요청, GET은 감시 화면에서 저장된 기록을 읽는 요청이다.
</details>
**확인문제 9.** 일반 화면이 정상으로 열리면 monitor에도 기록이 반드시 저장되었는가?
<details>
<summary>정답과 해설</summary>
	그렇지 않다. 현재 전송 방식은 연결 실패 때 누락될 수 있으므로 감시 표도 확인한다.
</details>
**확인문제 10.** 이번 행동 기록 수집에 Sentry를 새로 연결해야 하는가?
<details>
<summary>정답과 해설</summary>
	아니다. general이 monitor로 직접 보내는 수집 흐름을 사용한다. 기존 Sentry는 앱 오류 확인 용도로 유지한다.
</details>
## 되새김 문제
다음 질문에 말로 답할 수 있으면 이번 시간을 제대로 이해한 것이다.
- 일반 서비스의 자료와 감시 서비스의 기록은 어떻게 다른가?
- 게시글 행동 하나에서 여러 요청이 발생할 수 있는 이유는 무엇인가?
- 요청의 종류와 동작 완료 여부를 왜 따로 확인해야 하는가?
다음에는 서로 다른 기록의 출처와 뜻을 구분한 뒤 비교 조건을 붙여 보자.