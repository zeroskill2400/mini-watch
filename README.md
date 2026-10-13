# mini-watch — 5과목 Day3 시작 자료

Day2 완성 비교본에 게시글 관련 요청 종류를 구분하는 준비 코드를 포함했다. general의 조회·작성·수정·삭제 요청을 monitor에서 수집·조회한다. 소스의 DB 스키마는 Day2와 같다. 실제 계정·DB 데이터·비밀값은 Git clone으로 복제되지 않는다.

## 1교시 로컬 시작

Windows CMD에서 새 폴더에 받는다.

```cmd
cd /d C:\work
git clone --branch m5d3-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-m5d3
cd mini-watch-m5d3
code .
```

Docker Desktop 실행 후 공유 망이 있는지 확인한다. 기존 망은 유지하며 없는 경우에만 만든다.

```cmd
docker network inspect m5d1-events
```

없는 경우:

```cmd
docker network create m5d1-events
```

같은 폴더에서 감시와 일반을 실행한다. 앞 실습과 같은 프로젝트/볼륨 이름으로 기존 자료를 유지한다.

```cmd
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build
```

앞 실습과 같은 Compose 프로젝트 이름과 로컬 DB 볼륨을 사용하므로 기존 계정·게시글·기록이 유지된다. 프로젝트 이름의 `m5d1`은 앞 실습의 DB를 이어 쓰기 위해 유지한 이름이다.

새로 만드는 로컬 DB에서는 Compose가 `general/sql/docker-init.sql`과 `monitor/backend/sql/docker-init.sql`을 자동 실행해 테이블과 실행 확인용 게시글을 준비한다. SQL 파일을 따로 실행할 필요는 없다.

초기화 SQL은 DB가 처음 만들어질 때만 실행되며 기존 DB에는 다시 적용되지 않는다. 필요한 테이블이 없다는 오류가 나오면 [1교시 교안](day3-materials/lessons/lesson1.md)의 “준비 중 막히면”에서 로그를 확인하고 강사와 기존 DB 상태를 확인한다.

일반 http://localhost:8081 / 감시 http://localhost:8082. 기존 계정이 있으면 사용한다. 새 DB라면 다음을 하나씩 실행해 일반 student, 감시 operator를 생성하고 본인이 정한 새 비밀번호를 직접 입력한다. 기존 계정 비밀번호는 덮어쓰지 않는다.

```cmd
docker compose -f compose-general.yaml exec general-api python create_user.py
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```

두 화면에 로그인하고 일반에서 실습용 게시글을 작성·조회·수정·삭제한다. 감시에서는 각 동작 뒤 기록 불러오기를 누른다. 종류는 post_list/post_view/post_create_request/post_update_request/post_delete_request로 구분된다. 작성·수정·삭제는 요청의 목적이며 완료는 일반 화면 결과와 상태를 함께 확인한다. 303 응답만으로 작업 완료를 확정하지 않는다.

모든 게시글과 기록을 초기화하거나 기존 볼륨을 삭제하는 명령은 사용하지 않는다. 로그/조회는 최신50건이며 삭제한 글의 기존 수집 기록은 감시DB에 유지된다. 일반 앱의 전송은 연결 실패 때 누락될 수 있다. 제공 연결/쿠키/이벤트 토큰/오류 SDK는 준비 코드로 활용하며 1교시에서 새로 구현하지 않는다.

클라우드 실행 안내와 자신의 환경값은 DAY2-SETUP.md를 따른다. 기존 Sentry 오류 수집은 유지하며 행동 기록은 general→monitor로 직접 전달한다. Day3 2~6교시 자료와 탐지·승인·대응 기능은 아직 작성 전이다.

[1교시 교안](day3-materials/lessons/lesson1.md) · [로컬 HTML 미리보기](day3-materials/lessons/lesson1.html)
