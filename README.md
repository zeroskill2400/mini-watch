# Mini Watch Day5 기본 실습 시작 코드

Day4 본문 6교시에서 완성한 코드를 새 Day5 폴더로 받아 사용한다.

- general: Flask/Jinja2 일반 게시판.
- monitor/backend: 계정 확인, 관찰 메모 CRUD, 요청 기록 수집·조회 API.
- monitor/frontend: React/Vite 감시 대시보드와 분리된 컴포넌트·API 모듈.

## 새 Day5 폴더로 받기

VS Code에서 C:\work 같은 상위 폴더를 열고 새 CMD에서 실행한다.

```text
git clone --branch day05-basic-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-day05
```

받은 mini-watch-day05 폴더를 VS Code로 열고 새 CMD를 연다. 내 PC의 실습 기준 브랜치를 준비한다.

```text
git switch -c main
```

day05-basic-start는 수업 시작 코드의 이름이고 main은 내 PC에서 비교할 기준이다. 여기에서 feature/minsu 같은 작업 브랜치를 만든다.

1교시는 문서 파일로 브랜치를 연습하므로 서버와 DB를 켜지 않는다. 교사용 저장소에는 학생 수정 내용을 push하지 않는다. 팀 저장소와 원격 협업은 5교시에 준비한다.

## 다음 교시로 이어갈 상태

감시 로그인은 Flask의 DB 계정 확인 후 React state로 화면을 전환한다. 새로고침하면 로그인 폼으로 돌아오며, 이 로컬 학습판은 서버 API의 세션 접근 보호를 포함하지 않는다.

앱을 실행할 때는 서비스별로 .env·가상환경과 npm 의존성을 준비한다. 기존 general_db·monitor_db는 그대로 사용하며, Git clone은 실제 DB 데이터를 복사하지 않는다. SQL·설정 예시는 각 서버 폴더에 있다.

기존 day05-start는 쿠키·세션 확장 부록 버전이다. 이번 기본 실습은 day05-basic-start를 사용한다.
