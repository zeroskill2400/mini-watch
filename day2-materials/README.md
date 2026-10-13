# 5과목 Day2 실습 자료

1교시에서 만든 Flask 예제를 이어 사용한다. 단계별 폴더는 비교·복구용이며 자신의 저장소를 덮어쓰기 위한 일괄 설치 명령이 아니다.

2교시 샘플은 RLS 정책 없이 Python·Flask가 PostgreSQL에 접속한다. SQL 실행 전에 [Data API 설정](https://supabase.com/dashboard/project/_/integrations/data_api/overview)에서 수업용 프로젝트의 Enable Data API를 끄고 Save를 누른다. 다시 열어서 꺼져 있는지 확인한다. 프로젝트 생성 화면의 Enable automatic RLS는 체크하지 않으며, 해당 항목이 없으면 넘어간다. 각 단계의 messages.sql은 기존 메시지를 유지하면서 messages 테이블의 RLS를 끄도록 맞춰져 있다.

접속 정보는 프로젝트 상단 Connect → Direct에서 Connection Method의 Session pooler를 클릭하고 Type=URI를 유지한 뒤, 1 Connection string 아래 Connection parameters의 host·user를 복사한다. 처음 보이는 Framework/Next.js 안내는 Direct로 바꾸며, 아래의 Install Agent Skills (optional)는 건너뛴다. 포트는 5432이며 DB 비밀번호는 프로젝트 생성 때 정한 값을 사용한다.

Render 생성 화면은 New → Web Service → Git Provider의 저장소 행 선택 순서다. 서버 사양은 Free · $0 / month 카드를 직접 선택한다. Root Directory를 앱 폴더로 정하고 Dockerfile Path=./Dockerfile, Advanced의 Docker Build Context Directory=., Docker Command=빈칸, Auto-Deploy=On Commit으로 맞춘다.

기존 서비스의 설정은 Environment → Environment Variables의 Edit에서 바꾸고 새 키는 Add variable로 추가한다. 저장 버튼 오른쪽 화살표에서 방식을 고른 뒤, 이름이 바뀐 버튼을 눌러야 저장된다. 설정만 적용할 때는 Save and deploy, 곧 코드 push를 할 때는 Save only로 저장하고 새 커밋의 배포를 확인한다. Deploys에서 커밋과 서비스 상단의 Live 표시를 보고 Logs의 Application logs에서 실행 기록을 확인한다.

| 폴더 | 확인하는 단계 |
|---|---|
| stages/02-db-client | SQL과 독립 Python으로 같은 메시지 저장·조회 |
| stages/03-api | Flask 저장·조회 API와 DB 연결 |
| stages/04-next | Next.js 화면 → 서버 프록시 → Flask → DB |
| stages/05-sentry-error | 단독 오류 전송과 Flask 오류 재현 |
| stages/05-sentry-fixed | 같은 URL 수정 후 기존 메시지 기능 확인 |
| project-support/starter | 기존 mini-watch에 적용할 배포 지원 코드 |
| project-support/solution | 6교시 오류 수정 비교본 |

프로젝트 기준은 `day06-start`의 `7ac02c0b968caf0a35d09e235389d77e7c8eafc7`이다. Git에는 실제 .env·DB 비밀번호·Sentry DSN·로그인 계정을 넣지 않는다. .env.example을 복사하고 본인의 설정을 입력한다. Render 환경 변수에는 .env의 바깥 따옴표를 제외한 값만 넣는다.

코드의 로컬 검증 환경은 Python 3.12, PostgreSQL 16.15(TLS), Node 24.21.0, Next.js 16.4.0이다. Next 프로덕션 빌드, 실제 HTTP/DB 연결, 입력 검증, 기존 로그인·쿠키·기록·CRUD, 오류 SDK의 로컬 수신을 검사했다. Docker는 Compose 설정 검사까지 진행했다. 2026-10-13 로그인된 Render의 생성·환경 변수·배포 목록·로그 화면과 Supabase의 생성·연결·Data API 설정 화면도 대조했다. Windows CMD, Docker 이미지 실행, 새 외부 서비스 배포와 실제 Sentry 수신은 이 UI 검수에서 수행하지 않았다. Sentry 메뉴는 공식 문서 기준이다.

실습은 Render Free·Supabase Free·Sentry Developer의 기본 기능으로 진행한다. 외부 서비스의 무료 조건과 화면은 변경될 수 있으므로 교안의 공식 링크와 현재 설정 화면을 확인한다.
