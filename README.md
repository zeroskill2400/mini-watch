# 5과목 Day1 Docker 적용 비교본

Windows CMD에서 이 폴더를 연다. 일반 서비스와 감시 서비스를 각각 독립 Compose 프로젝트로 실행한다.
최초 한 번 공유 네트워크를 만든다. 이미 있으면 다시 만들지 않는다.

```cmd
docker network create m5d1-events
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-monitor.yaml ps
curl -i http://localhost:8082/api/auth/me
```

감시 DB의 healthy와 API의 HTTP 200을 확인한 뒤 아래를 실행한다. 시작 중 502가 나오면 logs monitor-api monitor-web으로 준비 상태를 확인하고 다시 요청한다.

```cmd
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-general.yaml up -d --build
docker compose -f compose-general.yaml exec general-api python create_user.py
```

일반 http://localhost:8081 / 감시 http://localhost:8082
일반 student / 감시 operator, 공개 실습 비밀번호 Learn123!
DB 및 SECRET_KEY 값도 공개된 격리 로컬 수업용 값이다. 외부 배포용 설정이 아니다.
감시 화면 로그인 후 기록 불러오기·메모 목록 불러오기를 누른다.

일반은 m5d1-general, 감시는 m5d1-monitor 프로젝트다.
일반·감시는 각자 front 망과 data 망·DB 볼륨을 갖고, 두 API만 외부 망 m5d1-events를 공유한다.
일반 API의 MONITOR_URL은 http://monitor-api:5000/api/events다.

```cmd
docker compose -f compose-general.yaml down
docker compose -f compose-monitor.yaml down
```

down에는 -v를 붙이지 않는다. 공유 외부 망은 위 down 명령으로 제거되지 않는다.
재시작은 각 파일에 대해 up -d를 실행한다.
API나 Next 앱을 재빌드한 뒤에는 해당 gateway를 restart해 바뀐 컨테이너 주소를 다시 찾게 한다.
예: docker compose -f compose-general.yaml up -d --build general-api 다음 docker compose -f compose-general.yaml restart general-gateway

1~4교시 샘플은 compose.yaml 하나를 확장하고 5교시는 compose-app.yaml·compose-data.yaml로 나눈다. 6교시는 별도 미니프로젝트 폴더의 compose-general.yaml·compose-monitor.yaml을 완성한다. 시작틀은 day06-start의 day1-materials/project-starter이며, 이 브랜치의 루트는 정답 적용 상태다.
이전 단일 m5d1-mini 프로젝트에서 넘어오면 볼륨 이름도 달라진다. 기존 DB를 옮기는 절차는 이 새 시작본 실습에 포함하지 않는다.
컨테이너 네트워크·Windows 실기동은 제작 환경에서 미검증이다.
