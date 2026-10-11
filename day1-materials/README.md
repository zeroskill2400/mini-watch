# 5과목 Day1 비교 자료

1~5교시는 같은 작은 샘플 폴더에 compose.yaml 하나를 확장하며 Flask·Next.js·DB·게이트웨이를 연결한다.
샘플의 화면과 API에서 DB 응답을 확인한 뒤 6교시에 기존 프로젝트로 이동한다.
실프로젝트는 compose-general.yaml과 compose-monitor.yaml 두 파일로 일반·감시 서비스를 각각 실행한다.

- tutorial: 교시별 비교 코드. 필요한 단계만 별도 폴더에서 확인하며 단계별 폴더를 동시에 실행하지 않는다.
- project-docker: 프로젝트에 적용할 14개 파일. 두 Compose 파일과 Dockerfile·DB 초기화·게이트웨이 설정 등을 담는다.

day06-start로 받은 프로젝트의 루트에서 Windows CMD로 적용한다.
day07-start 비교본에는 이미 루트에 적용되어 있다.

```cmd
xcopy /E /I /Y day1-materials\project-docker .
git status
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-general.yaml config --services
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-monitor.yaml config --services
```

공유 네트워크는 최초 한 번 만든다. 이미 m5d1-events가 있으면 생성 명령을 건너뛴다.
감시 수신 서비스를 먼저 실행하고 일반 서비스를 실행한다.

```cmd
docker network create m5d1-events
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
docker compose -f compose-general.yaml up -d --build
docker compose -f compose-general.yaml exec general-api python create_user.py
```

일반 http://localhost:8081 / 감시 http://localhost:8082
두 API만 외부 네트워크 m5d1-events를 공유한다. DB와 화면·게이트웨이는 각 프로젝트의 망을 쓴다.
같은 명령에 두 -f를 함께 넣으면 설정이 병합되므로 위처럼 각각 실행한다.
로그인·요청 기록·메모 CRUD·데이터 보존 확인 순서는 6교시 교안을 따른다.

```cmd
docker compose -f compose-general.yaml down
docker compose -f compose-monitor.yaml down
```

down에는 -v를 붙이지 않는다. 공유 외부 네트워크는 위 down으로 제거되지 않는다.
수업용 공개 예시값을 사용한다. 실제 비밀값·DB 데이터·설치된 패키지는 포함하지 않는다.
