# 4교시 — 단일 망에서 DB까지 연결
1~3교시의 Flask와 Next.js에 DB 조회를 더한 비교용 완성본이다.
교안은 PostgreSQL을 단독 실행해 준비한 뒤 Flask·Next 연결 코드를 수정하고 Compose로 세 서비스를 한 번에 연결한다.

이 폴더에서 독립적으로 비교할 때:
```cmd
docker volume create m5d1-sample-data
docker compose config --quiet
docker compose up -d --build
```
http://localhost:3300 에서 DB 문장을 확인한다.
외부 볼륨은 수동 실행 단계와 Compose가 같은 데이터를 사용하기 위해 지정했다.
04~06 단계 비교 폴더는 같은 프로젝트 이름과 포트를 쓰므로 하나만 실행한다.
다른 단계로 바꿀 때 현재 폴더에서 docker compose down으로 먼저 종료한다.
