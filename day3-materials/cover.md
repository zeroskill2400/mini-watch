## 오늘의 목표

게시판에서 로그인하거나 글을 쓰면 앱과 앞단 웹서버에 기록이 남는다. 같은 행동을 기록해도 앱은 JSON으로, Nginx는 긴 문자열로 남겨 각각 읽는 방법이 다르다.

오늘은 **직접 사이트 사용 → 두 원본 수집 → 정규화 → 감시 화면 확인**을 하나로 연결한다. SIEM의 기초인 로그 통합 조회를 만드는 수업이며, 계정·DB·로그 연결·화면은 준비된 상태로 시작한다.

<table header-row="true" fit-page-width="true">
<tr><td>준비된 환경</td><td>오늘 직접 구현할 부분</td></tr>
<tr><td>일반 게시판·수업 계정·Docker 설정·원본 조회 화면</td><td>앱 정규화·Nginx 정규화·합치기·오류 집계</td></tr>
</table>

<image src="./assets/day-flow.svg">설명용 구성도 — 위쪽은 게시판 요청, 아래쪽은 두 원본을 읽어 감시 화면으로 보내는 흐름이다. 감시 환경 상자는 API·화면·앞단 서버를 묶어 표시했다.</image>

브라우저는 Nginx를 거쳐 앱에 요청하고, 두 프로그램은 각자의 파일에 기록한다. 감시 앱은 공유된 두 파일을 읽어 학생이 작성한 함수로 변환한다. 마지막에는 새 주소를 직접 열고 그 기록이 통합 표에 추가되는지 확인한다.

성공 기준:
- 내가 만든 요청의 경로·상태를 두 원본에서 찾는다.
- 서로 다른 원본을 같은 열로 보고 출처·오류 조건으로 고른다.
- 추가 클릭 후 다시 불러오면 새 기록이 원본과 통합 표에 나타난다.

## 오늘 구현할 SIEM 기능

SIEM(Security Information and Event Management)은 여러 시스템의 기록을 모아 같은 기준으로 조사하는 보안 관리 체계다. 오늘은 그중 수집·정규화·통합 조회·오류 집계만 구현한다.

XDR(Extended Detection and Response)은 메일·PC 등 여러 보안 영역의 탐지를 연결해 조사·대응하고, SOAR(Security Orchestration, Automation and Response)는 사건 등록·알림·승인·조치 같은 대응 절차를 자동화한다. 이 기능들은 오늘 만들지 않으며, 세 이름이 반드시 순서대로 거치는 단계를 뜻하지도 않는다.

## 시작과 산출물

1교시에서 시작본을 clone하고 `docker compose -f compose-general.yaml up -d --build --wait` 뒤에 `docker compose -f compose-monitor.yaml up -d --build --wait`를 실행한다. 계정 준비와 서버 실행은 컨테이너 시작에 포함되며 접속 주소도 그 자리에서 안내하므로 별도 공통 준비 페이지나 시작 스크립트가 필요하지 않다. 로그는 준비 도구가 대신 만드는 것이 아니라 학생이 게시판을 실제로 사용하면서 만든다.

산출물은 `normalize_app.py`·`normalize_nginx.py`·`merge.py`·`report.py`와 이 코드가 만든 결과를 보여 주는 통합 로그 화면이다.

<page url="https://app.notion.com/p/3f8ae3d1800c81bd819de67a4d9f0a2c">1교시. 사이트를 움직여 로그 만들기 — 내 클릭이 기록되는 곳</page>
<page url="https://app.notion.com/p/3f9ae3d1800c8128a046df57a7ae6c01">2교시. 두 원본을 한곳에서 보기 — 앱과 Nginx의 기록</page>
<page url="https://app.notion.com/p/3f9ae3d1800c819d8654e05c1869bc6e">3교시. 앱 로그 정규화하기 — 공통 항목으로 옮기기</page>
<page url="https://app.notion.com/p/3f9ae3d1800c8131b377fb34feeaf53c">4교시. Nginx 로그 정규화하기 — 문자열에서 같은 값 꺼내기</page>
<page url="https://app.notion.com/p/3f9ae3d1800c8111b66ac5b4437058d5">5교시. 두 로그를 합쳐 오류 찾기 — 같은 조건으로 집계하기</page>
<page url="https://app.notion.com/p/3f9ae3d1800c81a5a211dd9c8a08f77a">6교시. 감시 화면에서 흐름 확인하기 — 새 클릭까지 반영하기</page>
