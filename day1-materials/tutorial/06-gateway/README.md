# 4교시 비교 코드 — 게이트웨이 추가

폴더 번호는 비교 단계 번호다. 교안은 같은 C:\work\m5d1-sample에서 이어간다. 각 비교 폴더는 동시에 실행하지 않는다.

```cmd
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

기존 sample-data 볼륨을 재사용한다. 빈 환경에서는 init.sql의 첫 문장만 보인다. 두 번째 문장은 3교시 INSERT 실습으로 추가한다.

해당 단계만 비교한 뒤 종료할 때는 docker compose down을 사용한다. 연속 수업에서는 교안의 다음 단계로 그대로 이어간다. DB 자료를 남기려면 -v를 붙이지 않는다.
