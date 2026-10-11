# 5교시 전반 — 같은 앱을 두 망으로 나누기
앱 파일은 4교시와 같다. Compose의 networks만 바꾼 비교용 완성본이다.
web=front-net, api=front-net+data-net, db=data-net.
API와 DB에는 ports가 없다. DB로의 직접 접속과 API를 통한 DB 조회를 구별한다.
4교시 실행을 먼저 docker compose down으로 종료한 후 이 폴더에서 실행한다.
```cmd
docker volume create m5d1-sample-data
docker compose up -d --build
```
http://localhost:3300 에서 같은 DB 문장을 확인한다.
