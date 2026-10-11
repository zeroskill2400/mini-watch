# 5교시 후반 — HTTP 입구 추가
앞 05-separated 단계와 앱 파일은 같다. gateway/default.conf와 Compose gateway를 추가했다.
PC 포트는 gateway의 8085만 공개한다. web/api/db는 내부 서비스 이름으로 통신한다.
기존 단계에서 docker compose down 후 이 폴더에서 다음을 실행한다.
```cmd
docker volume create m5d1-sample-data
docker compose up -d --build
```
http://localhost:8085 : Next.js 화면
http://localhost:8085/api/messages : Flask JSON
화면은 Next 서버→Flask→DB 경로를 계속 쓰며, 브라우저의 /api 요청은 Nginx→Flask로 간다.

06은 비교 코드 단계 번호이다. 이 단계에서 작은 샘플을 완성하고 종료한 뒤 6교시의 프로젝트 적용으로 넘어간다.
