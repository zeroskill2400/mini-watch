# 내 배포 설정 기록

실제 비밀번호나 키는 적지 않는다.

| 대상 | Root Directory | 외부 주소 |
|---|---|---|
| 일반 앱 | general | [내 주소] |
| 감시 API | monitor/backend | [내 주소] |
| 감시 화면 | monitor/next-frontend | [내 주소] |

일반 DB: 2교시의 샘플 Supabase 프로젝트를 재사용한다.

감시 DB: 별도 Supabase 무료 프로젝트를 사용한다.

일반의 MONITOR_URL은 감시 API 주소 + /api/events다. 감시 화면의 MONITOR_API_URL은 감시 API 기준 주소다.

DB_*와 SSL 설정은 각 DB 연결 화면에 대응한다. SESSION_COOKIE_SECURE=true를 Render에 넣고 두 API는 서로 다른 SECRET_KEY와 같은 EVENT_TOKEN을 사용한다.

실행 확인은 본인 외부 주소로 수행하고, 이 비교 설명 자체를 배포 성공 증거로 사용하지 않는다.
