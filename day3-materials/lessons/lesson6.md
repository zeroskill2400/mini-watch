터미널에서 확인한 통합 목록을 감시 화면으로 가져오자. 출처와 오류를 골라 본 뒤 새 주소를 열어, 내 다음 행동도 같은 코드와 화면을 거치는지 확인한다.
이번 시간에 확인할 흐름이다.
<image src="../assets/lesson6.svg">설명용 흐름도 — 왼쪽의 실제 입력을 가운데에서 처리해 오른쪽 결과로 확인한다.</image>
- 통합 표에 두 출처의 실제 경로와 상태가 보인다.
- 새로 연 경로가 재조회 후 나타나고 원본까지 대조할 수 있다.
<table_of_contents/>
## 1단계. 완성한 코드를 감시 화면에 연결하기
### 감시 앱이 코드를 다시 읽게 하자
학습 파일 네 개를 저장한 상태에서 시작한다. 터미널 명령은 실행할 때마다 파일을 읽지만, 켜져 있던 감시 앱은 처음 불러온 함수를 사용하므로 한 번 다시 시작한다.
프로젝트 폴더의 Windows CMD
```bash
cd /d C:\work\mini-watch-m5d3
docker compose restart monitor-api
```
다른 이름으로 clone했다면 위 폴더명도 실제 이름을 쓴다. 이 명령은 감시 앱만 다시 켜며 로그 파일이나 DB를 삭제하지 않는다. 이후 새 클릭을 조회할 때마다 재시작할 필요는 없다.
통합 표 열기
1. [감시 화면](http://localhost:8082)에서 현재 로그인 확인을 누른다. 필요하면 class-operator와 classroom1234!로 로그인한다.
2. 통합 로그 불러오기를 누르고 출처·방법·경로·상태 열을 확인한다.
```plain text
출처    방법   경로                 상태
app     GET    /training-missing     404
nginx   GET    /training-missing     404
```
표 중 두 행을 고른 예시다. 실제 표에는 내 로그인·글 작성·페이지 조회 기록도 있다. 화면의 전체 관측·오류 관측은 `report.py`가 돌려준 값이다.
<details>
<summary>아직 완성하라는 안내가 나오면</summary>
	VS Code에서 지금 실행한 폴더가 맞는지 확인하고 `normalize_app.py`·`normalize_nginx.py`·`merge.py`·`report.py`를 모두 저장한다. 특히 `report.py`에 ready: False인 시작 코드가 남았는지 확인한 뒤 monitor-api를 다시 시작한다.
	프로젝트 폴더의 Windows CMD
	```bash
docker compose exec -T monitor-api python -m learning.report
	```
	터미널에서도 오류가 나면 마지막 오류에 적힌 파일·항목을 확인한다. 원본이 비었다면 일반 게시판을 사용한 뒤 다시 조회한다.
</details>
## 2단계. 출처와 오류를 골라 원본까지 보기
### 같은 조건을 두 출처에 적용하자
출처·오류 필터 사용하기
1. 출처를 app으로 바꾸고 오류만 보기를 선택한다. 상태 400 이상인 앱 행만 남는지 확인한다.
2. 출처를 nginx로 바꿔 같은 오류 조건이 Nginx 행에도 적용되는지 확인한다.
3. 출처를 전체로 돌리고 /training-missing 행의 원본 보기를 펼친다.
앱 원본은 JSON 객체이고 Nginx 원본은 문자열이지만 바깥 표의 열은 같다. 원본 보기에서 경로·상태가 변환 결과와 맞는지 대조하자.
필터는 현재 불러온 결과에서 표시할 행만 고른다. 따라서 표시 관측은 달라져도 전체 관측·오류 관측은 그대로이며, 파일에 저장된 원본을 지우지 않는다.
## 3단계. 새 클릭이 끝까지 이어지는지 확인하기
### 지금 만든 경로를 화면에서 찾자
처음부터 끝까지 검증하기
1. 일반 게시판 탭에서 [http://localhost:8081/final-check](http://localhost:8081/final-check)을 연다. 이 주소는 없으므로 404가 나온다.
2. 감시 탭에서 원본 로그 불러오기를 눌러 두 원본에 /final-check가 추가됐는지 찾는다.
3. 통합 로그 불러오기를 누르고 출처 전체·오류만 보기 상태에서 /final-check의 app·nginx 행과 원본을 확인한다.
원본을 갱신하면 이전 통합 표는 비워진다. 통합 로그 불러오기를 눌러 새 원본을 다시 분석한 결과를 보자. 한쪽 기록이 늦게 보이면 잠시 뒤 다시 조회한다.
### 화면까지 연결하는 코드를 읽자
`monitor/backend/routes/analysis.py`에서 다음 부분을 찾자. API는 화면이 서버에 데이터를 요청하는 통로이며, 아래는 이미 제공된 함수의 읽기용 발췌다.
`routes/analysis.py` — 로그인 확인 후 학생 집계 함수 호출
```python
@analysis_bp.get("/api/analysis")
def analysis():
    error = api_access_error()
    if error:
        return error
    try:
        return build_report()
    except (OSError, ValueError) as error:
        return {"error": str(error)}, 400
```
통합 버튼이 /api/analysis를 요청하면 build\_report가 실행된다. 이 함수가 현재 파일 읽기부터 정규화·집계까지 호출하고, 화면은 반환된 events를 표로 보여 준다.
```plain text
버튼 → /api/analysis → build_report
     → load_normalized_events → read_logs + 두 정규화 함수
     → events / total_count / error_count → 표와 집계
```
별도 예제 데이터가 아니라 방금 내가 만든 /final-check가 이 경로를 거쳐 화면에 나온 것이다. 내가 만든 함수를 화면이 실제로 사용한다는 확인까지 하면 오늘 실습은 끝이다.
## 4단계. 오늘 구현한 범위 정리하기
오늘은 SIEM의 기초인 수집·정규화·통합 조회를 구현했다. 비슷해 보였던 세 이름을 해결하려는 문제로 다시 구분해 보자.
<table header-row="true" fit-page-width="true">
<tr>
<td>이름</td>
<td>해결하려는 문제와 예</td>
<td>오늘 구현 여부</td>
</tr>
<tr>
<td>SIEM — Security Information and Event Management</td>
<td>로그가 흩어져 조사하기 어렵다. 예: 웹·로그인·DB 기록을 모아 한 계정의 접근을 조사한다.</td>
<td>앱·Nginx 로그를 모아 같은 열로 조회하는 기초 기능만 구현</td>
</tr>
<tr>
<td>XDR — Extended Detection and Response</td>
<td>보안 도구의 탐지가 따로 보인다. 예: 메일의 악성 파일과 PC에서 실행된 같은 파일을 연계해 감염 사건을 조사·대응한다.</td>
<td>미구현. 앱·Nginx를 합쳤다고 XDR이 되지는 않음</td>
</tr>
<tr>
<td>SOAR — Security Orchestration, Automation and Response</td>
<td>대응 때마다 여러 도구에서 같은 작업을 반복한다. 예: 사건 등록 → 알림 → 승인 → 계정 잠금 → 결과 기록.</td>
<td>미구현. 알림·승인·차단 절차는 만들지 않음</td>
</tr>
</table>
위 메일·PC·계정 사례는 개념 설명용이며 이번 환경의 실제 사건이 아니다. SIEM도 탐지·연계를 할 수 있고 XDR도 자동 대응할 수 있으므로 기능은 겹치며, 세 제품을 반드시 순서대로 써야 하는 것도 아니다.
### 작업을 보존하고 마치자
프로젝트 폴더의 Windows CMD
```bash
docker compose stop
```
실습 서비스를 멈추되 코드·로그·DB는 남긴다. 이어서 실행할 때는 같은 폴더에서 docker compose up -d를 사용한다.
## 확인문제
**확인문제 1.** 코드 저장 뒤 감시 앱을 한 번 재시작하는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	실행 중인 Python 앱이 처음 불러온 함수를 사용하기 때문이다. 새 코드를 다시 읽게 한다.
</details>
**확인문제 2.** 새 클릭을 조회할 때마다 monitor-api를 재시작해야 하는가?
<details>
<summary>정답과 해설</summary>
	아니다. 코드를 바꿀 때와 새 로그를 읽을 때를 구분한다. 새 로그는 통합 버튼으로 다시 읽는다.
</details>
**확인문제 3.** 출처를 app으로 바꾸면 Nginx 원본 파일도 지워지는가?
<details>
<summary>정답과 해설</summary>
	아니다. 이미 불러온 표에서 표시할 행만 고른다.
</details>
**확인문제 4.** 표시 관측과 전체 관측이 다른 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	표시 관측에는 화면 필터가 적용되지만 전체 관측은 불러온 전체 결과의 행 수이기 때문이다.
</details>
**확인문제 5.** 원본 보기를 펼쳤을 때 앱과 Nginx는 어떤 모양인가?
<details>
<summary>정답과 해설</summary>
	앱은 JSON 객체, Nginx는 원래 한 줄 문자열이다. 같은 표에서도 원본은 보존한다.
</details>
**확인문제 6.** /final-check를 연 뒤 수집과 분석을 각각 어떻게 확인하는가?
<details>
<summary>정답과 해설</summary>
	원본 버튼으로 두 원본을 보고, 통합 버튼으로 정규화 표에서 같은 경로·상태를 확인한다.
</details>
**확인문제 7.** 통합 화면 요청을 받는 API 경로와 호출 함수는 무엇인가?
<details>
<summary>정답과 해설</summary>
	/api/analysis가 build\_report를 호출한다. 학생이 작성한 집계 함수가 화면 결과를 만든다.
</details>
**확인문제 8.** 오늘 만든 기능을 SIEM 전체라고 부를 수 있는가?
<details>
<summary>정답과 해설</summary>
	없다. 여러 로그의 수집·정규화·조회·오류 집계라는 기초 일부만 구현했다.
</details>
**확인문제 9.** 로그 두 종류를 합치면 XDR과 SOAR도 구현한 것인가?
<details>
<summary>정답과 해설</summary>
	아니다. 보안 영역의 탐지 연계나 승인·조치 절차를 구현하지 않았다.
</details>
**확인문제 10.** 실습을 멈추면서 데이터를 보존하려면 어떤 명령을 쓰는가?
<details>
<summary>정답과 해설</summary>
	docker compose stop을 쓴다. 볼륨을 삭제하지 않으며 같은 폴더에서 다시 켤 수 있다.
</details>
사이트 직접 사용 → 두 원본 확인 → 정규화 → 통합 조회가 이어졌다. 새 행동이 같은 흐름으로 반영되는 것을 확인한 것이 오늘의 최종 산출물이다.