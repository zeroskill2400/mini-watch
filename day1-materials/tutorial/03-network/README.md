# 2교시 비교 코드 — 기본 망 이름 요청

폴더 번호는 비교 단계 번호다. 교안은 같은 C:\work\m5d1-sample에서 이어간다. 각 비교 폴더는 동시에 실행하지 않는다.

```cmd
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

web에서 Flask에 요청한다.

```cmd
docker compose exec web curl --max-time 3 http://api:5000/api/hello
```

해당 단계만 비교한 뒤 종료할 때는 docker compose down을 사용한다. 연속 수업에서는 교안의 다음 단계로 그대로 이어간다. DB 자료를 남기려면 -v를 붙이지 않는다.
