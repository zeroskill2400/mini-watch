# 5과목 Day1 비교 자료

1~5교시는 교안의 작은 샘플을 직접 만든다.
Docker에서 gateway·web·api·db를 함께 실행하고 화면과 API의 DB 응답을 확인한 뒤 프로젝트에 적용한다.

- tutorial: 교시별 비교 코드. 단계별 폴더를 동시에 실행하지 않는다.
- project-docker: 프로젝트에 적용할 13개 설정 파일. 각 파일 전문은 6교시 교안에 있다.

받은 프로젝트의 루트에서 Windows CMD로 적용한다.

```bat
xcopy /E /I /Y day1-materials\project-docker .
git status
docker compose config --quiet
docker compose config --services
```

로그인·요청 기록·메모 CRUD·데이터 보존 확인 순서는 6교시 교안을 따른다.
수업용 공개 예시값을 사용한다. 실제 비밀값·DB 데이터·설치된 패키지는 포함하지 않는다.
