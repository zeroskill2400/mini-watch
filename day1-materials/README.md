# 5과목 Day1 실습 자료

1~4교시는 작은 샘플의 compose.yaml에 서비스를 추가한다. 5교시는 샘플을 앱·DB용 Compose 두 개로 나누고 공유 망으로 연결한다. 6교시는 준비된 미니프로젝트에서 일반·감시 실행 구성을 완성하는 종합 실습이다.

- tutorial: 1~5교시 단계별 비교 코드. 폴더 숫자는 교시 번호와 다르므로 tutorial/README.md의 대응표를 본다.
- project-starter: 6교시 시작틀. 앱 실행에 필요한 Dockerfile·SQL·Nginx 파일과 DB만 있는 Compose 두 개다.
- project-docker: 정답 설정. 먼저 문제를 풀고 교안의 접힌 정답·해설에서 비교한다.

## 6교시 시작하기

day06-start로 받은 프로젝트 루트에서 Windows CMD로 시작틀을 적용한다. 아래 복사는 루트의 Compose·앱 실행 설정을 시작 상태로 적용하므로 실습 도중 반복하지 않는다.

```cmd
xcopy /E /I /Y day1-materials\project-starter .
git status
```

compose-general.yaml과 compose-monitor.yaml에 요구사항의 서비스를 추가한다. 일반은 m5d1-general, 감시는 m5d1-monitor 프로젝트다. 공유 외부 망은 m5d1-events이며 두 API만 참여한다. 파일을 각각 -f로 지정하고 감시 준비를 확인한 뒤 일반을 실행한다.

일반 http://localhost:8081 / 감시 http://localhost:8082

로그인 실패·성공 기록과 메모 저장·다시 조회를 완료 기준으로 확인한다. 실행/종료 명령과 확인 결과를 README에 기록하고 Git 커밋한다. down에 -v를 붙이지 않아 DB 자료를 남긴다.

<details>
<summary>정답과 다음 수업 시작 상태</summary>

project-docker의 두 Compose 파일이 완성 설정이다. day07-start 루트에는 정답 설정이 적용되어 있다. 답을 비교한 뒤 감시→API 준비 확인→일반 순서로 실행한다.

```cmd
docker network create m5d1-events
docker network inspect m5d1-events
docker compose -f compose-monitor.yaml up -d --build
curl -i http://localhost:8082/api/auth/me
```

공유 망이 이미 있으면 inspect로 확인하고 재사용한다. HTTP 200이 확인되면 일반을 실행한다.

```cmd
docker compose -f compose-general.yaml up -d --build
docker compose -f compose-general.yaml exec general-api python create_user.py
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```

종료는 각각 수행한다.

```cmd
docker compose -f compose-general.yaml down
docker compose -f compose-monitor.yaml down
```
</details>

공개 예시 계정·비밀번호를 쓰는 로컬 수업이다. 실제 비밀값·DB 데이터·설치된 패키지는 포함하지 않는다.
