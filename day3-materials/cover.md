## 오늘의 목표

게시판 앱은 JSON으로, 앞단 Nginx 웹서버는 긴 문자열로 요청을 남긴다. 같은 오류를 찾으려 해도 원본마다 읽는 방법이 다르다.

오늘은 **서로 다른 두 로그를 공통 형식으로 정규화하고, 같은 조건으로 조회하는 작은 통합 로그 화면**을 만든다. 앞에서 소개한 SIEM의 일부 기능을 직접 구현한다. 계정·서비스·로그 수집기·화면 틀은 준비된 상태로 시작하며, 가입이나 서버 구축을 다시 배우는 시간이 아니다.

<table header-row="true" fit-page-width="true">
<tr><td>이어받은 것</td><td>오늘 직접 만들 것</td></tr>
<tr><td>일반 게시판·감시 서비스·Docker 실행 방식</td><td>앱 JSON 변환·Nginx 문자열 변환·두 결과 합치기·오류 집계</td></tr>
</table>

<image src="./assets/day-flow.svg">설명용 구성도 — 내 PC의 두 프로그램이 남긴 원본을 준비된 수집기가 모은다. 학생은 변환·집계 함수를 작성하고 준비된 감시 화면에서 확인한다.</image>

위쪽은 요청의 이동, 아래쪽은 기록을 읽는 흐름이다. 분석 대상으로 보낸 요청 두 건이 각각 앱과 Nginx에 남으므로 최종 표에는 로그 네 행이 보인다. 네 행을 요청 네 번이나 공격 네 건으로 해석하지 않는다.

성공 기준:
- 서로 다른 두 원본이 같은 항목·타입으로 보인다.
- 출처를 바꿔도 같은 오류 조건을 적용하고 원본으로 돌아가 확인한다.
- 원본에 없는 앱 시각은 비워 두며 로그 수와 요청 수를 구분한다.

## SIEM·XDR·SOAR 중 무엇을 구현할까

<table header-row="true" fit-page-width="true">
<tr><td>이름과 역할</td><td>이번 수업의 경계</td></tr>
<tr><td>SIEM — Security Information and Event Management. 여러 곳의 로그를 모아 검색·분석한다.</td><td>로그 정규화·통합 조회·공통 조건 집계를 구현한다. 전체 SIEM 제품을 만들지는 않는다.</td></tr>
<tr><td>XDR — Extended Detection and Response. 기기·계정 등 여러 보안 영역의 탐지·조사를 연결한다.</td><td>로그 두 종류를 합쳤다고 XDR 전체를 구현한 것은 아니다.</td></tr>
<tr><td>SOAR — Security Orchestration, Automation and Response. 도구를 연결해 대응 절차를 자동화한다.</td><td>자동 차단·장비 격리 같은 대응은 이번에 구현하지 않는다.</td></tr>
</table>

세 이름은 반드시 차례로 거치는 세 단계가 아니다. 이번에는 그중 정규화와 통합 조회에 집중한다.

## 시작과 산출물

1교시 안에서 시작본 클론 → `start-class.cmd` 실행 → 준비된 계정 로그인을 진행한다. 별도 공통 준비 페이지로 이동하지 않는다. 시작 명령이 실제 요청 두 건과 두 종류의 로그를 준비하므로 학생은 정규화 코드부터 작성한다.

산출물은 `normalize_app.py`, `normalize_nginx.py`, `merge.py`, `report.py`와 이 함수의 결과를 보여 주는 통합 로그 화면이다. 각 교시에 저장 위치·전체 코드·실행 명령·확인할 결과가 있다.

<page url="https://app.notion.com/p/3f8ae3d1800c81bd819de67a4d9f0a2c">1교시. 서로 다른 로그 비교하기 — 오늘 만들 SIEM 기능</page>
<page url="https://app.notion.com/p/3f9ae3d1800c8128a046df57a7ae6c01">2교시. 앱 로그 정규화하기 — 원본 값을 공통 항목으로</page>
<page url="https://app.notion.com/p/3f9ae3d1800c819d8654e05c1869bc6e">3교시. Nginx 로그 정규화하기 — 문자열을 같은 항목으로</page>
<page url="https://app.notion.com/p/3f9ae3d1800c8131b377fb34feeaf53c">4교시. 두 로그 합치기 — 출처가 보이는 한 목록</page>
<page url="https://app.notion.com/p/3f9ae3d1800c8111b66ac5b4437058d5">5교시. 같은 조건으로 오류 찾기 — 통합 로그 집계</page>
<page url="https://app.notion.com/p/3f9ae3d1800c81a5a211dd9c8a08f77a">6교시. 통합 화면 확인하기 — 출처와 원본까지 읽기</page>
