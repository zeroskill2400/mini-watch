# 5과목 Day1 Docker 적용 비교본

Windows CMD에서 이 폴더를 열고 실행한다.

    docker compose up -d --build
    docker compose exec general-api python create_user.py
    docker compose exec monitor-api python create_user.py

일반 http://localhost:8081 / 감시 http://localhost:8082
일반 student / 감시 operator, 공개 실습 비밀번호 Learn123!
DB 및 SECRET_KEY 값도 공개된 격리 로컬 수업용 값이다. 외부 배포용 설정이 아니다.
감시 화면 로그인 후 기록 불러오기·메모 목록 불러오기를 누른다.

종료: docker compose down
재시작: docker compose up -d
앱 재빌드 뒤에는 해당 gateway를 restart해 바뀐 컨테이너 주소를 다시 찾게 한다.
예: docker compose up -d --build general-api → docker compose restart general-gateway
down에는 -v를 붙이지 않는다. -v는 DB 볼륨까지 지운다.

일반/감시 각각 front 망과 data 망을 사용하고 두 API만 events-net을 공유한다.
이 비교본은 이전 수업 앱·DB 연결·세션 부록을 준비한 공통 시작본에 Docker 설정을 적용한 것이다.
컨테이너 네트워크·Windows 실기동은 제작 환경에서 미검증이다.

## 수업 순서와 Git 시작점

1~5교시와 6교시 앞부분은 교안의 작은 코드를 직접 작성한다.
Docker에서 gateway·web·api·db의 요청과 응답을 확인한 뒤 6교시 프로젝트 적용을 시작한다.

```bat
cd /d C:\work
git clone --branch day06-start https://github.com/zeroskill2400/mini-watch.git mini-watch-day06
cd mini-watch-day06
```

general·monitor는 기존 앱이며 day1-materials는 비교 코드와 적용할 설정이다.
프로젝트 루트에는 아직 Docker 설정을 적용하지 않은 day06-start를 사용한다.
day07-start는 설정을 적용한 완성 비교본이다.
교안: https://www.notion.so/3f6ae3d1800c81c59d93e70132b2157f
