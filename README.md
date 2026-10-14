# Day4 1교시 — 로그에서 반복 로그인 실패 경고로

Day3에서 본 앱·Nginx 원본과 통합 로그를 그대로 제공하고, 앱의 실제 인증 결과로 반복 실패를 찾는다. 일반 사이트에서 같은 아이디로 60초 안에 세 번 틀린 비밀번호를 입력하면 감시 화면에 경고 하나와 근거 세 건이 표시된다. 한 번의 실패에는 경고가 없다. 이는 수업용 탐지 조건이지 공격 확정이나 자동차단이 아니다.

## 시작

Day3에서 사용한 Git과 Docker를 그대로 사용한다. Docker Desktop 또는 Linux Docker Engine과 Docker Compose가 실행 중이어야 한다. 같은 저장소의 `m5d4-start` 브랜치를 새 `mini-watch-day4` 폴더로 받는다. Day3 폴더에 덮어쓰거나 파일을 옮길 필요가 없다. 이 시작본에는 계정·DB·원본 수집·규칙·화면이 준비되어 있으며, 예제 실패 로그는 미리 넣지 않았다.

Windows PowerShell 또는 CMD:

```powershell
cd C:\work
git clone --branch m5d4-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-day4
cd mini-watch-day4
.\start-class.cmd
```

Linux 또는 macOS:

```bash
mkdir -p ~/work
cd ~/work
git clone --branch m5d4-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-day4
cd mini-watch-day4
sh start-class.sh
```

이미 받은 폴더가 있다면 다시 clone하지 않고 그 폴더에서 시작 명령만 실행한다. Windows의 `C:\work`가 없다면 탐색기에서 먼저 만든다. 소스를 볼 때는 VS Code에서 파일 → 폴더 열기로 `mini-watch-day4`를 연다.

첫 실행에서는 이미지를 내려받고 빌드하므로 인터넷 연결과 여유 시간이 필요하다. 시작 명령은 두 Compose를 실행하고 서비스가 정상 응답할 때까지 기다린다. 실패했으면 출력된 오류를 먼저 확인한다.

| 사이트 | 주소 | 아이디 | 비밀번호 |
| --- | --- | --- | --- |
| 일반 사이트 | http://localhost:8083/login | class-student | classroom1234! |
| 감시 사이트 | http://localhost:8084 | class-operator | classroom1234! |

수업용 공개 계정과 설정이다. 인터넷 서버에 그대로 배포하지 않는다. 두 사이트는 `localhost` 주소를 사용한다. `127.0.0.1`과 섞으면 브라우저 쿠키가 서로 달라진다.

## 직접 확인

1. 감시 사이트에 `class-operator`로 로그인한다. 일반 사이트는 로그인 입력 화면에 둔다. 이미 로그인되어 있으면 일반 사이트의 로그아웃을 누른다.
2. 감시 화면에서 **새 관찰 시작**을 누른다. 시작 시각 이후의 기록만 이번 관찰에 포함한다. 기존 원본 파일은 삭제하지 않는다.
3. 일반 사이트에 아이디 `class-student`, 틀린 비밀번호 `wrong-password`를 입력하고 로그인한다. 실패 메시지를 확인한 뒤 감시 화면의 **탐지 새로고침**을 누른다. 실패 1회, 경고 0건이다.
4. 첫 실패로부터 60초가 지나기 전에 같은 아이디와 틀린 비밀번호로 두 번 더 로그인한다. 입력한 비밀번호는 시도 후 비워지므로 매번 다시 입력한다. 감시 화면에서 **탐지 새로고침**을 누른다.
5. 경고의 근거를 열고 서로 다른 이벤트 ID 세 개, 같은 입력 아이디, 발생 시각, `POST /auth/login`, 상태 `401`을 확인한다. 앱과 Nginx를 합쳐 여섯 번으로 세지 않는다.
6. 시간이 지나 세 번이 한 시간창에 들지 않았다면 **새 관찰 시작**부터 다시 해 본다. 정상 비밀번호로 로그인해도 실패 횟수는 늘지 않으며, 기존 경고는 저절로 지워지지 않는다.

현재 횟수는 조회 시점의 최근 60초다. 경고는 이번 관찰 중 조건을 처음 만족한 시점의 근거를 유지하므로 60초가 지나 현재 횟수가 0이 되어도 남는다. 같은 관찰에서 같은 아이디에 대한 경고는 하나만 만든다. 새로고침으로 같은 이벤트를 다시 세지 않는다. 여러 운영자 탭은 같은 PC의 관찰을 공유한다.

실패 시 입력한 아이디는 시도 대상 이름일 뿐 로그인한 사람의 신원이 아니다. 오타, 자동 완성, 정상 사용자의 반복 실수도 이 조건에 걸릴 수 있다. 로그인 성공은 실패 횟수를 더하지 않지만 이 단순 규칙의 시간창을 초기화하지도 않는다.

## 어느 코드가 만드는가

- `general/routes/auth.py`: 실제 계정·비밀번호 확인 결과에 따라 인증 성공 또는 실패 정보를 남긴다.
- `general/request_logging.py`: 이벤트 ID·UTC 발생 시각·입력 아이디·인증 결과를 기존 요청 정보에 더해 `/classroom-logs/app.jsonl`에 기록한다. 비밀번호는 기록하지 않는다.
- `gateways/general.conf`: 같은 요청을 앞단 웹서버의 `/classroom-logs/nginx.log`에 기록한다. 탐지 횟수에는 앱 인증 결과만 사용한다.
- `monitor/backend/detection_rules.py`: 같은 입력 아이디의 시간창 안 실패를 모아 `len(window) >= THRESHOLD`를 확인한다.
- `monitor/backend/detection_service.py`: 원본을 읽고 이벤트 ID 중복을 제외한다. 관찰 시작 정보를 별도 볼륨에 보존한다.
- 감시의 탐지 화면은 **탐지 새로고침**을 누를 때 현재 원본으로 계산한다. 백그라운드 실시간 푸시나 이메일·Slack 알림은 아니다.

## Linux 원본 확인

아래 명령은 프로젝트 폴더의 호스트 터미널에서 실행한다. 명령 안의 `sh -c`와 `tail`은 Linux 컨테이너에서 실행된다. 원본 전체를 삭제하거나 편집하지 않는다.

```bash
docker compose -f compose-general.yaml exec general-api sh -c 'tail -n 8 /classroom-logs/app.jsonl'
docker compose -f compose-general.yaml exec general-gateway sh -c 'tail -n 8 /classroom-logs/nginx.log'
```

Windows CMD에서는 작은따옴표 대신 큰따옴표로 `sh -c` 뒤를 감싼다. PowerShell에서는 위 명령을 그대로 사용한다.

## 서비스 확인과 종료

```bash
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml ps
docker compose -f compose-general.yaml down
docker compose -f compose-monitor.yaml down
```

두 Compose 프로젝트는 `m5d4-general`·`m5d4-monitor`이며 API끼리 `m5d4-events` 네트워크를 사용한다. 원본은 공통 Docker 볼륨 `m5d4-classroom-logs`, 일반 DB·감시 DB·관찰 시작 정보는 별도 Day4 볼륨에 저장된다. 호스트 폴더 바인드 마운트는 사용하지 않는다. Day3의 컨테이너·8081/8082 포트·DB·원본·로그인 쿠키와 분리했다.

`down`은 컨테이너와 프로젝트 내부 네트워크만 내린다. 다시 시작하면 DB·원본·관찰 기록이 남는다. 새 수업 관찰은 화면의 **새 관찰 시작**으로 시작한다. `down -v`나 `docker volume rm`은 필요 없다.

이 자료는 Day4 1교시 준비본이다. 파일 감시·다른 영역의 근거 연결·AI API 호출·승인·조치 자동화는 구현하지 않았다.
