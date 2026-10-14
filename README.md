# mini-watch — 5과목 Day3(m5d3)

일반 서비스의 게시글 행동을 요청 기록에서 확인하고, 출처·시각·조건을 구분해 근거가 보이는 감시 화면을 만든다.

처음 도구·Git·Compose·DB 준비는 [4과목 공통 실습 환경 준비](https://app.notion.com/p/3f9ae3d1800c81b0ba61cf483bd35724)에 있다. 새 DB의 초기 SQL은 Compose가 자동 실행하고 기존 DB에는 다시 적용하지 않는다. 실제 계정·DB 데이터·환경 비밀값은 Git clone으로 복사되지 않는다.

- 시작 브랜치: `m5d3-start`, Windows 작업 폴더: `C:\work\mini-watch-m5d3`
- 완성 비교 브랜치: `m5d3-solution`
- 교안: [Day3 여섯 교시](https://app.notion.com/p/3b9ae3d1800c8197a6dacfb41524e347), 저장소 안 `day3-materials/lessons`
- 일반 화면: http://localhost:8081 / 감시 화면: http://localhost:8082

`monitor/backend/learning`은 감시 API에 읽기 전용으로 연결되어 VS Code에서 저장한 파일을 다음 Python 실행부터 읽는다. Scapy2.8.0은 이미지에 들어 있다. 준비된 PCAP만 읽으므로 별도 캡처 드라이버 설치는 필요하지 않다.

1교시에서 일반 목록 조회→감시DB `http_events`→감시 화면의 같은 기록을 확인한다. general의 실행 로그에는 전송 전 JSON이 있으며 `day3-materials/lessons/lesson1.md`에 실행 로그 dump와 DB JSONL 사본을 내보내는 방법이 있다.

실제 HTTP는 새 관찰 시작 이후 ID 중 첫 결과 조회시각의 최근60초를 센다. 같은 관찰의 기준을 바꿀 때 이 구간을 유지하고 새 관찰에서 다시 정한다. 교육용 PCAP와 감사 JSON은 실제 HTTP와 별개 자료이며 한 사건의 사용자·시간으로 합치지 않는다. 검토 후보는 추가 확인의 입력이다.

이 브랜치는 조회 규칙과 보고서 연결이 완성된 비교본이다. 실제 HTTP 관찰은 실행한 환경에서 새로 시작한다.
