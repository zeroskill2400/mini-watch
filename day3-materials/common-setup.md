일반 서비스와 감시 서비스에 처음 들어갈 때 사용하는 공통 준비 안내이다. Git·도구 확인·계정·DB 준비를 여기서 마치고, 이후 교시에서는 정상 상태 확인부터 이어서 시작하자.
이미 두 화면이 열리면 설치나 DB 생성 명령을 반복하지 않고 마지막의 두 화면 확인만 한다.
## 1단계. 도구와 작업 폴더 확인하기
Windows CMD, Git, VS Code, Docker Desktop을 사용한다. Docker Desktop은 실행해 두고 Linux 컨테이너를 사용한다.
Windows CMD에서 다음 버전을 확인한다.
```plain text
git --version
docker compose version
```
명령을 찾을 수 없으면 강사와 도구 설치 상태를 확인한다. 도구가 이미 준비됐다면 새로 설치하지 않는다.
## 2단계. 시작 자료 받기
현재 분석 실습에 사용할 시작본은 m5d3-start이고, 작업 폴더는 `C:\work\mini-watch-m5d3`이다. 다른 날짜 실습의 Git·폴더는 해당 교안에 적힌 값을 사용한다.
Windows CMD
```plain text
if not exist C:\work mkdir C:\work
cd /d C:\work
git clone --branch m5d3-start --single-branch https://github.com/zeroskill2400/mini-watch.git mini-watch-m5d3
cd mini-watch-m5d3
code .
```
Git은 코드·SQL·설정 예시를 가져온다. 실제 계정·DB 데이터·비밀값은 복사하지 않는다. 폴더가 이미 있다면 clone의 마지막 폴더 이름과 cd를 함께 mini-watch-m5d3-2로 바꾸고 이후 명령도 새 폴더에서 실행한다.
code .을 찾지 못하면 VS Code의 파일 → 폴더 열기로 새로 받은 폴더를 연다.
## 3단계. 공유망과 두 서비스를 실행하기
먼저 공유망이 있는지 확인한다.
```plain text
docker network inspect m5d1-events
```
공유망 정보가 나오면 그대로 쓴다. No such network가 나오면 한 번 만든다.
```plain text
docker network create m5d1-events
```
두 Compose를 차례대로 실행한다.
```plain text
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build
```
프로젝트 이름의 m5d1은 앞 실습의 로컬 DB 볼륨을 이어 쓰기 위해 유지한 이름이다. 새 폴더에 코드를 받아도 같은 Docker 환경의 같은 프로젝트 이름·볼륨을 사용하면 기존 계정과 자료가 남는다.
`monitor/backend/learning` 폴더는 감시 API에 읽기 전용으로 연결된다. VS Code에서 저장한 실습 파일은 다음 Python 실행에서 읽는다. Scapy도 이미지에 포함되어 있어 학생 PC에 따로 설치하지 않는다.
## 4단계. DB 자동 준비 방식 확인하기
새 로컬 DB 볼륨에서는 Compose가 초기 SQL을 자동 실행한다. 학생이 SQL 파일을 따로 실행할 필요는 없다.
`compose-general.yaml`의 `general-db` 설정 일부
```yaml
volumes:
- general-data:/var/lib/postgresql/data
# 새 DB 볼륨의 첫 실행에서 자동 적용한다.
- ./general/sql/docker-init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
```
`compose-monitor.yaml`의 `monitor-db` 설정 일부
```yaml
volumes:
- monitor-data:/var/lib/postgresql/data
# 새 DB 볼륨의 첫 실행에서 자동 적용한다.
- ./monitor/backend/sql/docker-init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
```
이 설정은 제공한 YAML에 이미 들어 있다. 일반 DB는 게시글 등 업무 자료를, 감시 DB는 `http_events` 등 감시 자료를 준비한다.
초기 SQL은 처음 DB를 만들 때만 실행되므로 기존 볼륨에서는 다시 적용하지 않는다. 테이블이 없다는 오류가 나면 강사와 기존 DB 상태를 확인한다.
## 5단계. 없는 앱 계정만 만들기
계정이 있으면 기존 계정으로 로그인한다. 새 환경이면 아래 명령을 하나씩 실행하고 일반은 student, 감시는 operator와 본인이 정한 12자 이상 비밀번호를 직접 입력한다.
```plain text
docker compose -f compose-general.yaml exec general-api python create_user.py
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```
비밀번호는 입력 중 표시되지 않는다. 기존 계정이 있다는 안내가 나오면 덮어쓰지 않고 기존 비밀번호를 사용한다.
## 6단계. 두 화면의 정상 상태 확인하기
1. 일반 화면 http://localhost:8081에서 자신의 계정으로 로그인하고 게시글 목록을 확인한다.
2. 감시 화면 http://localhost:8082에서 현재 로그인 확인을 누르고 자신의 감시 계정으로 로그인한다.
3. 감시 화면의 기록 불러오기를 눌러 방법·경로·상태·종류를 확인한다.
일반 기능과 감시 표가 열리면 준비가 끝났다. 수집 실습에서 DB의 행과 화면의 같은 요청을 확인한다.
<details>
<summary>두 화면이 열리지 않거나 기록이 없으면</summary>
	저장소 루트의 Windows CMD에서 상태와 로그를 읽는다.
	```plain text
docker compose -f compose-monitor.yaml ps
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml logs --tail 20 monitor-api
docker compose -f compose-general.yaml logs --tail 20 general-api
	```
	일반 앱의 MONITOR_URL은 감시 수집 API를 가리키고 두 앱의 EVENT_TOKEN은 같아야 한다. 제공한 로컬 Compose에는 연결값이 준비되어 있다. 전송 실패 경고는 general-api 로그에서 확인한다.
</details>
