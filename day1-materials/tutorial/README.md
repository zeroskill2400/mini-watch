# 5과목 Day1 단계별 비교 코드
1. 01-flask → 01-flask-edited: 로컬·이미지·코드 변경
2. 02-next: 공식 생성 뒤 작은 Next.js 화면 (수정 제목은 교안 전문 참고)
3. 03-network: 같은 이미지, 네트워크 명령으로 연결/해제/복구
4. 04-connected: 같은 앱에 PostgreSQL → 서버 fetch → Compose
5. 05-separated: 5교시 전반, front-net/data-net 추가
6. 06-gateway: 5교시 후반, Nginx HTTP 입구 추가

본문에서는 C:\work\m5d1-sample\connected 한 폴더를 계속 수정한다.
이 자료는 각 교시 종료 상태의 비교본이다. 단계 폴더를 동시에 실행하지 않는다.
Docker Desktop Linux 컨테이너 모드와 Windows CMD 기준.
패키지·볼륨 비밀번호는 로컬 수업용 공개 예시값이다.
컨테이너 실기동과 Windows에서의 실행은 제작 환경에서 검증하지 않았다.

폴더 앞 숫자는 비교 코드 단계 번호이며 교시 번호와 다를 수 있다. 6교시는 이 샘플의 동작을 확인한 뒤 실제 프로젝트에 적용한다.
