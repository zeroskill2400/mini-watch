일반 서비스에서 글을 쓰고 고치면 요청이 발생한다. 그 요청과 처리 결과를 남긴 자료가 요청 기록이다. 이번 시간에는 general에서 여러 행동을 해 보고 monitor에 모인 기록과 대조하자.
일반 서비스의 게시글 활동을 감시 표에서 확인하는 것이 목표다.
<image src="../assets/lesson1.svg">설명용 구성도. 일반 앱은 게시글 기능을 처리하고, 감시 앱에 요청 기록을 보내 별도 DB에 저장한다.</image>
왼쪽은 글을 다루는 일반 서비스다. 가운데 화살표로 방법·경로·상태를 보내면 오른쪽 감시 API가 요청 종류를 붙여 저장한다. 감시 화면은 감시 API에 조회 요청을 보내고, API가 DB에서 읽어 돌려준 기록을 표로 보여 준다.
- 조회·작성·수정·삭제 요청을 감시 표에서 구분한다.
- 일반 화면 결과와 요청의 방법·경로·상태를 함께 확인한다.
```plain text
C:\work\mini-watch-day08\
├─ general\                  ← 요청을 처리하고 기록을 보냄
├─ monitor\backend\          ← 기록을 받고 DB에 저장
├─ monitor\next-frontend\    ← 저장된 기록을 표로 조회
├─ compose-general.yaml
└─ compose-monitor.yaml
```
<table_of_contents/>
## 1단계. 시작 자료와 두 화면 준비하기
앞 수업에서 사용한 Git·Docker Desktop을 그대로 쓴다. 이번 시작본에는 Day2 일반 서비스와 감시 서비스의 완성 코드가 들어 있다. 감시 표에서 게시글 관련 요청을 구분하는 이름도 준비되어 있다.
Windows CMD를 사용한다. 아래 명령은 새 폴더에 코드를 받고 VS Code로 연다.
Windows CMD
```plain text
cd /d C:\work
git clone --branch day08-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-day08
cd mini-watch-day08
code .
```
Git은 코드·SQL·설정 예시를 가져온다. 실제 DB 데이터와 계정은 복사하지 않는다. 같은 이름의 폴더가 이미 있다면 아래의 준비 중 막히면을 펼쳐 새 폴더로 받는다.
이번 교시는 로컬 Docker에서 일반 화면 `http://localhost:8081`, 감시 화면 `http://localhost:8082`를 연다. Docker Desktop이 실행 중인지 확인하고 VS Code에서 새로 받은 저장소의 루트 폴더를 터미널로 연다.
Windows CMD
```plain text
docker network inspect m5d1-events
```
공유 망 정보가 나오면 그대로 사용한다. No such network가 나오면 다음 명령으로 한 번 만든다.
Windows CMD
```plain text
docker network create m5d1-events
```
Windows CMD
```plain text
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build
```
앞 실습과 같은 Compose 프로젝트 이름과 로컬 DB 볼륨을 사용한다. 기존 계정·게시글·기록은 유지된다. 새 환경에서는 DB와 실행 확인용 게시글이 준비된다. 계정이 없다면 아래 명령으로 만든다. 빌드가 끝난 뒤 두 주소를 열어 일반 서비스와 감시 서비스 제목을 확인한다.
계정이 이미 있으면 기존 아이디·비밀번호를 사용한다. 새 환경이라면 아래 명령을 하나씩 실행해 일반은 student, 감시는 operator와 본인이 정한 12자 이상 비밀번호를 직접 입력한다. 입력한 비밀번호 글자는 화면에 표시되지 않는다.
Windows CMD
```plain text
docker compose -f compose-general.yaml exec general-api python create_user.py
```
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```
일반 화면의 로그인으로 들어가 자신의 일반 계정으로 로그인한다. 감시 화면에서는 현재 로그인 확인을 누르고 자신의 감시 계정으로 로그인한다. 방금 계정을 만들었다면 일반은 student, 감시는 operator를 사용한다. 로그인은 글을 쓰고 기록을 볼 준비이며 이번 관찰 대상은 게시글 활동이다.
두 화면 확인
1. 일반 화면에서 게시글 목록이 보이는지 확인한다.
2. 감시 화면에서 기록 불러오기를 누르고 종류·방법·경로·상태 열을 확인한다.
<details>
<summary>준비 중 막히면</summary>
	기본 폴더가 이미 있다면 아래처럼 clone의 마지막 이름과 다음 cd를 함께 바꾼다. 이후에는 새로 받은 mini-watch-day08-2 폴더에서 작업한다.
	Windows CMD
	```plain text
cd /d C:\work
git clone --branch day08-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-day08-2
cd mini-watch-day08-2
code .
	```
	code .을 찾지 못하면 VS Code의 파일 → 폴더 열기로 새로 받은 폴더를 연다. 접속이 안 되면 아래 명령에서 서비스 상태와 감시 API 로그를 확인한다.
	Windows CMD
	```plain text
docker compose -f compose-monitor.yaml ps
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml logs --tail 20 monitor-api
docker compose -f compose-general.yaml logs --tail 20 general-api
	```
	일반 화면만 열리고 기록이 없으면 일반 앱의 MONITOR\_URL이 감시 수집 API를 가리키는지 확인하고, 두 앱의 EVENT\_TOKEN이 같은지도 확인한다. 기록 전송 실패 경고는 general-api 로그에서 찾는다. 지금 제공한 로컬 Compose에는 연결값이 준비되어 있다. 기존 계정이 있다는 안내가 나오면 비밀번호를 덮어쓰지 않고 기존 비밀번호를 사용한다.
</details>
## 2단계. 일반 화면에서 새 글 쓰기
게시글이 없는 새 DB에서도 시작할 수 있도록 이번 실습용 글을 하나 만든다. 입력한 글 내용은 일반 DB에, 그 요청의 기록은 감시 DB에 각각 남는다.
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
**확인문제 2.** 이 실습에서 일반 DB와 감시 DB에 각각 무엇이 저장되는가?
<details>
<summary>정답과 해설</summary>
	일반 DB에는 게시글, 감시 DB에는 요청 기록이 저장된다. 서로 다른 목적의 자료다.
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
다음에는 이렇게 모은 여러 행동 기록에서 평소와 다른 패턴을 찾아보자.