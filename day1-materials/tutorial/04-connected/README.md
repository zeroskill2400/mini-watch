# 04-connected 비교 코드

4교시 종료 상태. 같은 Compose에 db와 sample-data 볼륨을 추가했다. Next 서버가 api를 거쳐 DB 문장을 조회한다.

수업에서는 C:\work\m5d1-sample 폴더의 compose.yaml 하나를 계속 수정한다.
이 폴더는 해당 시점의 비교본이다. 단계 폴더를 동시에 실행하지 않는다.

```cmd
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

종료는 docker compose down이다. DB 자료를 유지하려면 -v를 붙이지 않는다.
4교시부터 sample-data는 Compose가 관리하며 docker volume create로 따로 만들지 않는다.
제작 환경에서는 Docker 엔진과 Windows에서의 컨테이너 실기동을 검증하지 않았다.
