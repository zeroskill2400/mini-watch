# 5과목 Day1 단계별 비교 코드

1. 01-flask → 01-flask-edited: compose.yaml에 api 하나를 작성하고 Flask 응답 수정·재빌드
2. 02-next: 같은 compose.yaml에 web 추가, 수정한 Next.js 화면 확인
3. 03-network: Compose 기본 네트워크와 api 서비스 이름 통신
4. 04-connected: 같은 compose.yaml에 db·sample-data 추가, Next → Flask → PostgreSQL
5. 05-separated: 5교시 전반, front-net/data-net으로 연결 범위 분리
6. 06-gateway: 5교시 후반, gateway 추가와 브라우저 입구 8085

수업에서는 C:\work\m5d1-sample 폴더의 compose.yaml 하나를 계속 수정한다.
앱 경로는 flask/, next/이며 이후 db/, gateway/가 추가된다.
각 폴더는 중간·종료 상태의 비교본이며 동시에 실행하지 않는다.
모든 단계의 Compose 프로젝트 이름은 m5d1-sample이다.

숫자는 비교 단계 번호이며 교시 번호와 다를 수 있다. 6교시에는 별도 mini-watch 프로젝트로 전환한다.
실제 프로젝트의 일반·감시는 각각 compose-general.yaml·compose-monitor.yaml로 실행한다.
Docker Desktop Linux 컨테이너 모드와 Windows CMD 기준이다.
비밀번호는 로컬 수업용 공개 예시값이다. Docker 엔진·Windows 실기동은 제작 환경에서 미검증이다.
