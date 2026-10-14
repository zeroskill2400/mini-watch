# mini-watch — 5과목 Day3 수업 완성본

일반 게시판에서 직접 로그인·조회·없는 주소 요청을 해 보고, Flask JSON과 Nginx 텍스트에 남은 기록을 공통 형식으로 바꿉니다. **SIEM의 로그 정규화·통합 조회 일부**를 만드는 수업입니다. 자동 차단이나 XDR 전체를 구현하지 않습니다.

## 시작

Docker Desktop을 실행한 뒤 이 프로젝트 폴더의 터미널에서 실행합니다.

```text
docker compose -f compose-general.yaml up -d --build --wait
docker compose -f compose-monitor.yaml up -d --build --wait
```

일반 서비스를 먼저 실행한 뒤 감시 서비스를 실행합니다. `m5d3-general`은 게시판용 3개, `m5d3-monitor`는 감시용 4개 컨테이너를 실행합니다. general이 공통 `m5d3-general_events-net` 네트워크를 자동으로 만들고 monitor가 같은 네트워크에 연결합니다. 네트워크를 별도 명령으로 만들 필요가 없습니다. DB와 화면의 내부 네트워크는 각 프로젝트에 분리됩니다.

DB가 준비되면 각 API 컨테이너의 `init.py`가 기존 `seed_classroom.main`으로 수업 계정을 준비하고 웹서버를 실행합니다. 같은 계정이 있으면 기존 비밀번호를 유지합니다. DB 스키마 SQL은 새 볼륨의 첫 실행에만 자동 적용됩니다. 실습 요청이나 분석용 로그 묶음을 미리 만들지는 않습니다. 처음에는 원본이 비어 있어도 정상입니다.

| 화면 | 주소 | 아이디 | 공개 실습 비밀번호 |
|---|---|---|---|
| 일반 게시판 | http://localhost:8081/login | `class-student` | `classroom1234!` |
| 감시 화면 | http://localhost:8082 | `class-operator` | `classroom1234!` |

각 화면에서 아이디·비밀번호를 입력하고 `로그인`을 누릅니다. 일반 목록의 `class-student 님이 로그인했습니다.`, 감시 화면의 `class-operator 사용자`로 성공을 확인합니다. 첫 빌드 직후 화면이 아직 열리지 않으면 잠시 기다린 뒤 다시 엽니다.

## 직접 동작하고 기록 확인하기

1. 일반 게시판에서 로그인한 뒤 목록을 엽니다.
2. 브라우저 주소창에 `http://localhost:8081/training-missing`을 입력해 없는 경로의 404 응답을 확인합니다.
3. 감시 화면에서 원본을 다시 불러와 해당 경로와 상태가 두 출처에 남았는지 확인합니다.
4. 3~5교시에서 네 함수를 완성한 뒤 분석 결과를 다시 불러옵니다. 일반 게시판에서 동작을 추가하고 다시 불러오면 현재 로그로 결과가 바뀝니다.

자동 새로고침은 하지 않습니다. 로그인 뒤 이동·화면 파일·브라우저의 추가 요청도 기록되므로 클릭 수와 로그 행 수는 같지 않습니다. 앱과 Nginx가 각 요청을 기록하므로 관측 행 수를 요청 수나 공격 수로 읽지 않습니다.

## 수업에서 작성할 파일

`monitor/backend/learning`에서 아래 네 파일을 교시 순서대로 작성합니다.

| 교시 | 파일 | 결과 |
|---|---|---|
| 3 | `normalize_app.py` | 현재 Flask JSON 원본을 공통 항목으로 변환 |
| 4 | `normalize_nginx.py` | 현재 Nginx 텍스트 원본을 같은 항목으로 변환 |
| 5 | `merge.py` | 두 출처의 관측을 한 목록으로 연결 |
| 5 | `report.py` | 전체 관측과 상태 400 이상인 오류 관측 집계 |
| 6 | 제공된 감시 화면 | 추가 동작 전후 비교·출처/오류 필터·원본 확인 |

이 폴더의 네 함수는 완성되어 있습니다. 수업에서는 시작본의 빈 틀에 각 교시의 코드를 직접 저장해 완성합니다.

공통 항목은 `id/source/method/path/status_code/raw`입니다. 앱 원본에 없는 시각을 만들지 않으며, Nginx의 원본 시각은 `raw`에 남깁니다. `app-1`·`nginx-1`은 각 출처 파일의 행 번호이지 공통 요청 ID가 아닙니다.

## 준비된 코드의 역할

- `general/request_logging.py`: 일반 게시판 응답의 방법·경로·상태를 JSONL에 추가하고 기존 감시 DB에도 전송합니다.
- `gateways/general.conf`: 일반 게시판 앞 Nginx가 자신의 접근 로그를 남깁니다.
- `learning/log_data.py`: 공유된 두 로그 파일의 현재 내용을 읽습니다. 새 요청을 보내거나 원본을 수정하지 않습니다.
- `GET /api/analysis/raw`: 로그인한 운영자에게 현재 원본을 반환합니다. 정규화 함수가 미완성이어도 읽을 수 있습니다.
- `GET /api/analysis`: 학생이 작성한 함수로 현재 원본을 정규화·합치기·집계합니다.

원본 파일은 프로젝트의 `classroom-logs/app.jsonl`과 `classroom-logs/nginx.log`입니다. 일반 앱·Nginx만 쓰고 감시 API는 읽기 전용으로 공유합니다. 파일이 아직 없으면 빈 목록으로 표시하고, 기록 중인 마지막 미완성 줄은 다음 조회에서 읽습니다. 두 파일을 읽는 사이 새 요청이 들어오면 출처별 행 수가 잠시 다를 수 있습니다.

기존 `/api/events`는 Flask가 전송한 DB 요청 기록이며 두 출처의 통합 분석과 입력 경로가 다릅니다. 통합 분석은 DB나 고정 `case.json`이 아닌 현재 두 원본 파일을 사용합니다.

## 실행 상태와 보존

서비스 상태와 오류는 같은 프로젝트 폴더에서 확인합니다.

```text
docker compose ls
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml ps
docker compose -f compose-general.yaml logs --tail 30 general-api general-gateway
docker compose -f compose-monitor.yaml logs --tail 30 monitor-api
```

수업을 마치면 실행만 멈춥니다.

```text
docker compose -f compose-monitor.yaml stop
docker compose -f compose-general.yaml stop
```

이 설정과 공개 비밀번호는 개인 PC 수업용입니다. 공개 포트는 `127.0.0.1:8081`·`127.0.0.1:8082`입니다. 이전 실습이 같은 포트를 사용 중이면 Docker Desktop에서 그 프로젝트만 Stop합니다. Day3는 `m5d3-general`·`m5d3-monitor` 두 프로젝트와 각각 자동 생성되는 전용 DB 볼륨을 사용하며, 기존 Day의 DB나 이전 Day3 볼륨을 지우지 않습니다. 재실행은 계정·게시글·DB·로그 파일을 보존합니다. 같은 이름의 계정이 있으면 기존 비밀번호를 유지합니다. `down -v`나 초기 SQL 재실행은 하지 않습니다.

기본 `compose.yaml`은 사용하지 않습니다. `docker compose ps` 대신 `-f`로 확인할 파일을 지정하고, 두 프로젝트 전체 목록은 `docker compose ls`로 봅니다.
