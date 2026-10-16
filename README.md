# Day5 — 실제 요청 이력을 규칙과 AI로 판단하기

Day4의 일반 앱·공지 저장·독립 센서 사건을 이어 쓴다. 새 공지를 저장하면 감시 서버가 앱 저장과 센서의 같은 해시를 확인하고 이력 수집 → 규칙 판단 → 사용할 판단 → 대응 계획 → 대응 실행 → 결과 알림을 자동 처리한다. 화면을 열거나 실행 버튼을 눌러 시작하는 방식이 아니다.

실제 요청 이력을 짧은 `if`문으로 판단한 뒤 같은 고정 이력에 AI 판단을 비교한다. 학생 함수의 한 줄을 바꾸면 다음 새 사건의 판단을 실제 AI에 맡긴다. 가상 URL 점수나 준비된 AI 성공 답을 넣지 않는다. 조치는 내 PC의 수업용 공지 저장 제한과 감시 화면 안의 알림·티켓뿐이다.

## 시작

Day5 시작본은 `m5d5-start` 브랜치다. Day4나 `day05-start`가 아닌 아래 브랜치를 받는다. Windows 터미널에서 `C:\work` 폴더로 이동한 뒤 실행한다.

```powershell
cd C:\work
git clone --branch m5d5-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-day5
cd mini-watch-day5
```

Docker Desktop을 켜고 VS Code에서 프로젝트 폴더를 연다. 두 Compose 파일이 있는 루트의 Windows 터미널에서 일반 → 감시 순서로 실행한다.

```powershell
docker compose -f compose-general.yaml up -d --build --wait
docker compose -f compose-monitor.yaml up -d --build --wait
```

두 독립 Compose·8개 서비스와 내부 `init.py`가 계정·DB·서버를 준비한다. 감시 DB에 관찰이 없을 때만 첫 관찰을 만들고 자동 감지의 최초 활성 시각도 한 번만 저장한다. 일반 서버는 새 요청 기록 형식의 시작점을 한 번만 저장한다. 재시작해도 기존 관찰·원본·공지·활성 시각·처리 이력을 지우지 않는다. 별도 시작 실행파일과 예제 로그 주입은 없다.

| 역할 | 주소 | 아이디 | 비밀번호 |
| --- | --- | --- | --- |
| 일반 사이트 | `http://localhost:8085/login` | class-student | classroom1234! |
| 공지 저장 | `http://localhost:8085/notice` | 같은 일반 로그인 | 같은 일반 로그인 |
| 감시 화면 | `http://localhost:8086` | class-operator | classroom1234! |

공개 수업 계정은 내 PC의 격리된 실습에서만 사용한다. 두 사이트의 로그인은 새로고침 뒤에도 유지되고 Day3·Day4와 쿠키 이름을 분리했다.

## 학생 함수 네 개

수정하는 파일은 `monitor/backend/soar_rules.py` 하나다. 준비된 전체 내용은 다음과 같다.

```python
from history_ai import decide_with_ai


def decide_with_rule(history):
    if history["login_failure_count"] >= 3:
        return {"decision": "respond", "reason": "최근 이력에 로그인 실패가 3회 이상 있습니다."}
    return {"decision": "review", "reason": "최근 이력의 로그인 실패가 3회 미만입니다."}


def make_prompt():
    return "요청 횟수와 시간순서를 보고 판단하세요. 관찰 사실과 추정을 구분하고 근거 ID와 한계를 적으세요."


def decide(history):
    return decide_with_rule(history)


def choose_actions(decision):
    if decision == "respond":
        return ["notify", "create_ticket"]
    return ["notify", "create_ticket"]
```

수정 뒤에는 **Ctrl+S → 일반 사이트에 다른 내용의 새 공지 저장 → 자동 결과 확인**으로 진행한다. 학생 파일 하나만 읽기 전용으로 연결하고 다음 새 사건에서 다시 읽으므로 매번 Docker를 재빌드하지 않는다. 문법 오류는 해당 사건의 실패로 남기고 다음 사건을 계속 감지한다. 과거 실행의 함수·이력·판단·계획은 바꾸지 않으며 기존 승인·복구는 고정된 계획으로 처리한다.

## 첫 실행과 이력의 의미

1. 일반 사이트에 정상 로그인하고 공지에 `오늘 요청 이력 실습을 시작합니다. 1`을 저장한다. 로그인 실패나 URL 입력이 필수는 아니다.
2. 센서와 감시 서버가 새 사건을 읽으면 자동 실행이 생긴다. 두 감지 주기 때문에 잠시 지연될 수 있다.
3. 감시 화면에서 새 결과를 선택해 이력 수집과 규칙 판단을 읽는다. 새로고침과 최신 결과 보기는 조회이며 실행 명령이 아니다.
4. 실제 로그인 실패가3회 미만이면 검토 대기다. 이미 최근 실패가 있다면 그 실제 숫자를 읽는다. 초기 상태를 맞추려고 원본을 지우지 않는다.

기본 review와 respond는 모두 내부 알림·티켓만 남긴다. 제한은 학생이 respond 목록에 직접 추가한 뒤에만 연결된다.

이력 범위는 **이번 공지 저장 시각까지 최대300초 동안 일반 앱 서버 전체의 완료 요청**이다. 공지 작성자 한 사람만의 이력이 아니다. 앱의 `request_id`를 한 번만 세고 nginx 복제 기록·health·내부 API는 제외한다. 로그인 실패는 POST 로그인의 명시적 `auth_failure`·HTTP401만, 성공은 `auth_success`·HTTP200만 센다. 실패 입력 계정 이름을 인증 사용자나 같은 사람으로 단정하지 않는다.

건수는 확인한 창 전체에서 집계한다. 시간순 상세 원본과 AI 입력은 최대40건 표본이므로 전체 목록과 다를 수 있다. 실제 시간창·표본 수·누락·읽기 상한을 표시한다. 새 기록 형식 이전의 원본은 삭제하지 않고 제외 건수로 표시한다. 최초 창은 실제 기록 시작점부터이므로 아직5분 전체가 아닐 수 있다. 원본이 깨졌거나 이번 저장 요청이 빠졌으면 완전한 이력으로 처리하지 않고 검토로 남긴다.

## 같은 이력 비교와 AI로 교체

**같은 이력으로 AI 판단 비교**는 선택한 실행의 고정 이력과 현재 `make_prompt()` 문장을 사용한다. 원래 규칙 결과·시간창·이력 해시·프롬프트·AI 결과와 오류를 따로 보존한다. 비교는 새 조치나 알림·티켓·제한을 만들지 않고 원래 실행의 분기도 바꾸지 않는다.

다음 새 사건부터 AI 판단을 쓰려면 `decide`의 한 줄을 바꾼다.

```python
def decide(history):
    return decide_with_ai(history, make_prompt())
```

이 상태에서는 새 사건을 감지한 서버가 실제 AI를 요청한다. 단순한 사후 요약이 아니다. AI는 review/respond·위험 수준·이유·실제 근거 ID·추정·한계를 반환한다. 형식과 보낸 근거 ID를 검증하며 고위험 판단과 충분한 근거가 있는 respond만 자동 대응에 연결한다. 규칙의 실패3회를 AI 뒤에서 다시 강제하지 않으므로 두 판단은 다를 수 있다. AI는 임의 명령·대상·조치 목록을 만들 수 없다.

강사가 `OPENAI_API_KEY`·`OPENAI_MODEL`을 안전하게 준비해야 AI 실습을 진행할 수 있다. 현재 실제 연결·성공 호출 검증은 대기 중이다. 설정이 없거나 통신·형식·근거 검증에 실패하면 원인과 `mode: fallback`·review를 표시한다. 가짜 성공·낮은 위험으로 바꾸지 않으며 실패한 AI 결과로 대응 승인을 허용하지 않는다. 미연결 환경에서는 규칙 실습과 AI 미연결 안내까지 확인할 수 있고 실제 AI 교체 성공으로 보고하지 않는다.

같은 이력·프롬프트·모델의 호출은 영속 캐시로 중복을 막는다. 진행 중이면 추가 호출하지 않고 성공과 통신 실패·중단 결과도 보존한다. 이미 전송됐을 수 있는 실패를 자동 재호출하지 않으며 다른 프롬프트나 모델로 명시 비교할 때만 새 시도다. 설정이 없어 전송하지 않은 경우는 연결 설정이 생기면 같은 입력을 다시 비교할 수 있다. 이전 미연결 비교 항목은 남긴다. AI 응답을 기다리는 동안 조회와 다른 실행의 복구는 가능하다.

## 실제 효과 확인과 복구

respond 목록만 `["restrict_notice", "notify", "create_ticket"]`로 바꾸고 새 사건을 만든다. 실제 판단이 respond이면 준비된 공지 저장 제한 API가 실행된다. 유효한 review일 때는 사람이 **검토 후 대응 승인**을 눌러 실행 생성 당시 고정된 respond 계획을 적용할 수 있다. 자동 제한의 주체는 `system`이며 사람의 승인을 했다고 기록하지 않는다.

제한 직전 현재 공지 해시와 사건 스냅샷을 다시 비교한다. 이미 공지가 바뀌었다면 오래된 사건으로 현재 공지를 제한하지 않는다. 제한 범위는 공지 저장뿐이고 로그인·공지 조회·계정·IP·서버 전체는 차단하지 않는다.

1. 일반 공지에 다른 문장을 저장해 실제 정책403과 제한 안내를 확인한다.
2. 같은 실행의 **실제 저장 결과 확인**을 눌러 정책 거부 근거를 연결한다. 요청 확인 값(CSRF) 오류403은 인정하지 않는다.
3. respond 목록을 먼저 `["notify", "create_ticket"]`로 복원하고 Ctrl+S로 저장한다. 다음 새 사건의 재제한을 막는 준비이며 기존 실행의 제한은 그대로다.
4. 같은 실행의 **저장 허용 복구 승인**을 누른다. 사람의 승인으로 프로그램이 저장 제한을 푼다.
5. 일반 사이트에서 다른 내용을 저장해200을 확인하고 원래 실행의 **실제 저장 결과 확인**으로 완료한다. 변경 없는200은 완료 근거가 아니다. 복구 뒤 새 저장은 별도 자동 실행이므로 원래 실행을 선택해 확인한다.

복구는 저장 권한 허용이지 과거 공지 문장 복원이 아니다. 안전을 위해403 검사보다 복구를 먼저 승인할 수도 있으며 이 경우403 검증은 비어 있고 실제 복구200만 남는다. 다른 실행이 소유한 제한은 해제하지 못한다. 응답 유실은 완료가 아니며 같은 조치 번호와 실제 영수증으로 다시 확인하거나 안전하게 복구한다.

## 원본과 준비된 연결

Windows 프로젝트 루트에서 Docker 안의 Linux 파일을 읽는다.

```powershell
docker compose -f compose-general.yaml exec general-api cat /classroom-data/notice.txt
docker compose -f compose-general.yaml exec general-api tail -n 8 /classroom-logs/app.jsonl
docker compose -f compose-general.yaml exec file-sensor tail -n 5 /classroom-logs/file-events.jsonl
```

- `general/request_logging.py`는 실제 요청의 시각·번호·인증 결과를 기록한다. 비밀번호·공지 전문·쿠키를 이력에 넣지 않는다.
- `general/request_history_state.py`는 새 기록 형식의 시작점을 멱등하게 준비하고 이전 원본을 보존한다.
- `monitor/backend/request_history.py`는 창·중복·표본을 명시해 집계하고 `history_playbook_service.py`가 학생 함수와 허용 조치를 연결한다.
- `monitor/backend/history_ai.py`는 기존 실제 AI 전송기를 재사용해 구조화 응답과 근거를 검증하고 호출 결과를 영속 저장한다. 필요한 실제 요청 필드만 보내고 공지 전문·비밀번호는 보내지 않는다.
- `monitor/backend/url_playbook_automation.py`는 API 안에서1초마다 새 앱·센서 사건을 읽는다. 활성 시각과 저장별 처리 이력을 보존해 같은 사건은 재시작에도 한 번만 처리한다. 실패한 옛 사건을 임의 재실행하지 않는다.
- 이전 URL 실행과 승인형 요청·원본·영수증은 삭제하지 않는다. 새 실행만 `history-v1`이며 이전 기록의 조회·복구와 API 호환을 유지한다.

## 확인과 종료

진행 중인 제한을 복구하고 실제 저장되는지 확인한다.

```powershell
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml ps
docker compose -f compose-monitor.yaml stop
docker compose -f compose-general.yaml stop
```

프로젝트는 `m5d5-general`·`m5d5-monitor`다. Day3·Day4의 포트·볼륨·원본과 분리하며 전체 Docker나 다른 수업을 중지하지 않는다. 볼륨 삭제·DB 초기화는 수업 절차가 아니다.
