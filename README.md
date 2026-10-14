# mini-watch — 5과목 Day3 수업 시작본

같은 실제 HTTP 요청을 Flask JSON과 Nginx 텍스트로 확인한 뒤 공통 형식으로 바꾸고 한 표에서 조회합니다. **SIEM의 수집·정규화·통합 조회 일부**를 만드는 수업입니다. 자동 대응(SOAR)이나 여러 보안 제품을 연결한 XDR을 구현하지 않습니다.

## 시작

Docker Desktop을 실행한 뒤 이 프로젝트 폴더의 CMD에서 실행합니다.

```cmd
start-class.cmd
```

macOS·Linux에서는 `sh start-class.sh`를 실행합니다. 준비 스크립트가 네트워크·두 Compose·수업 계정·서버 준비 확인·실제 로그 수집까지 진행합니다. 수집이 끝날 때까지 일반 게시판을 클릭하지 않습니다.

```text
실제 요청 2건을 보냈습니다: GET / 200, GET /training-missing 404
원본 저장: Flask JSON 2행 + Nginx combined 2행
monitor/backend/learning/data/case.json 준비 완료
```

| 화면 | 주소 | 아이디 | 공개 실습 비밀번호 |
|---|---|---|---|
| 일반 게시판 | http://localhost:8081/login | `class-student` | `classroom1234!` |
| 감시 화면 | http://localhost:8082 | `class-operator` | `classroom1234!` |

각 화면에서 아이디·비밀번호를 입력하고 `로그인`을 누릅니다. 일반 목록의 `class-student 님이 로그인했습니다.`, 감시 화면의 `class-operator 사용자`로 성공을 확인합니다.

## 수업에서 작성할 파일

`monitor/backend/learning`에서 아래 네 파일을 교시 순서대로 작성합니다.

| 교시 | 파일 | 결과 |
|---|---|---|
| 2 | `normalize_app.py` | Flask JSON 2행을 공통 형식으로 변환 |
| 3 | `normalize_nginx.py` | Nginx 텍스트 2행을 같은 형식으로 변환 |
| 4 | `merge.py` | 두 출처의 관측 4행을 한 목록으로 연결 |
| 5 | `report.py` | 전체 관측 4행·오류 관측 2행 집계 |
| 6 | 제공된 분석 화면 | 출처·오류 필터·원본 펼쳐 보기 확인 |

시작본의 네 함수는 빈 틀입니다. 앱·로그 수집기·로그인·분석 API·React 화면은 준비되어 있습니다. 각 교시의 전체 코드를 저장하며 빈 틀을 채웁니다.

공통 필드는 `id/source/time/method/path/status_code/raw`입니다. 앱 원본에 시각이 없으므로 `time=None`으로 두고 추정하지 않습니다. Nginx 시각은 시간대가 있는 원본을 UTC ISO로 변환합니다. `raw`에는 원본을 그대로 남깁니다.

요청 2건을 두 시스템이 각각 남겼으므로 관측은 4행입니다. 오류 관측 2행도 같은 404 요청을 각 출처가 기록한 결과이며, 공격 2건이나 서로 다른 사용자 2명을 뜻하지 않습니다. `app-1`·`nginx-1`은 스냅샷 안의 출처별 행 번호이지 공통 요청 ID가 아닙니다.

## 제공된 준비 코드

- `general/request_logging.py`: 응답 정보 JSON을 출력·전송하고, Compose의 `REQUEST_LOG_PATH`가 있을 때만 같은 JSONL을 추가 기록합니다.
- `gateways/general.conf`: Nginx의 실제 combined 접근 로그를 기록합니다.
- `general/collect_classroom.py`: 일반 게이트웨이에 실제 요청 2건을 보내고 두 원본을 검증해 `case.json`에 저장합니다.
- `classroom_data.py`: 학생 코드가 같은 `case.json`을 읽는 공통 함수입니다.
- `routes/analysis.py`·`AnalysisClient.js`: 로그인한 사용자의 보고서를 화면으로 연결합니다.

프로젝트의 `classroom-logs`는 일반 앱·Nginx가 공유하고, `monitor/backend/learning/data`는 수집기·분석 앱·PC에서 함께 사용합니다. 원본이 없거나 다른 요청이 섞이면 준비가 실패하며 예제값으로 대신하지 않고 기존 `case.json`을 보존합니다.

이 설정과 공개 비밀번호는 개인 PC 수업용입니다. 공개 포트는 `127.0.0.1:8081`·`127.0.0.1:8082`만 사용합니다. 재실행해도 기존 계정·비밀번호·게시글·DB 기록·볼륨을 삭제하지 않습니다. `down -v`나 초기 SQL 재실행은 필요 없습니다.

## 시작본 범위

`m5d3-start`는 준비 코드와 빈 함수 틀을 제공하는 시작본입니다. 2~5교시의 전체 코드를 순서대로 작성하고 6교시에서 통합 화면을 확인합니다. 이 브랜치는 학생이 작성할 네 함수의 완성 답안을 제공하지 않습니다.
