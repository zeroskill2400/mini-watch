# 5교시 비교 코드 — 샘플 Compose 두 개

4교시 샘플의 화면·JSON에 두 문장이 있는 상태에서 전환한다. 교안의 m5d1-sample 폴더에서 기존 compose.yaml로 docker compose down을 실행한다(-v 제외). 기존 파일은 compose-single.yaml로 이름을 바꾸고 이 폴더의 compose-data.yaml과 compose-app.yaml을 작성한다. 앱 코드는 그대로다.

```cmd
docker network create m5d1-shared-data
docker network inspect m5d1-shared-data
docker compose -f compose-data.yaml up -d
docker compose -f compose-data.yaml exec db pg_isready -U sample -d sample_db
```

DB 준비 후 실행한다. 같은 이름의 공유 망이 이미 있으면 inspect로 확인하고 재사용한다.

```cmd
docker compose -f compose-app.yaml up -d --build
curl http://localhost:8085/api/messages
```

기존 m5d1-sample_sample-data 볼륨을 이어 쓰므로 두 문장이 남는다. 빈 환경에서 이 비교 폴더만 실행하면 init.sql의 첫 문장만 생긴다. 다음 SQL로 수업의 두 번째 문장을 준비할 수 있다.

```cmd
docker compose -f compose-data.yaml exec db psql -U sample -d sample_db -c "INSERT INTO messages (body) VALUES ('두 번째 문장') ON CONFLICT (body) DO NOTHING;"
```

8085 화면과 JSON을 확인한 뒤 각각 종료한다.

```cmd
docker compose -f compose-app.yaml down
docker compose -f compose-data.yaml down
```

compose-single.yaml은 비교 보관용이다. 새 두 파일과 동시에 실행하지 않는다. -f 두 개를 한 명령에 붙여 병합하지 않는다.
