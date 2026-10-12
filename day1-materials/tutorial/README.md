# 5과목 Day1 단계별 비교 코드

| 교시 | 비교 폴더 | 종료 상태 |
|---|---|---|
|1|01-flask → 01-flask-edited|Flask 실행과 수정 재빌드|
|2|02-next → 03-network|web 추가와 기본망 이름 요청|
|3|04-connected|DB의 문장을 Flask·Next에서 조회|
|4|05-separated → 06-gateway|망 분리와 8085 HTTP 입구|
|5|07-two-compose|앱·DB를 독립 Compose로 실행|

폴더 앞 숫자는 비교 단계 번호이며 교시 번호가 아니다. 1~4교시는 같은 C:\work\m5d1-sample의 compose.yaml을 수정한다. 5교시에는 기존 파일을 compose-single.yaml로 보관하고 compose-app.yaml과 compose-data.yaml을 각각 실행한다.
각 폴더는 비교본이므로 동시에 실행하지 않는다. 5교시 DB 프로젝트는 기존 m5d1-sample 이름을 유지해 sample-data 볼륨을 이어 쓰고, 앱 프로젝트는 m5d1-app을 쓴다. 07-two-compose/README.md의 시작 상태와 순서를 확인한다.
6교시는 Git 프로젝트의 day1-materials/project-starter로 시작하고 Compose 두 개를 직접 완성한다. 정답은 project-docker와 day07-start에 있다.
Windows CMD · Docker Desktop Linux 컨테이너 모드 기준이다. 비밀번호는 로컬 수업용 공개 예시다.
