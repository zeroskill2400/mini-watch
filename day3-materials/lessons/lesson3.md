정상 기준은 평소 어떤 값이 나오는지 비교할 자료이고, 임계값은 검토할 후보를 고르는 경계값이다. 관찰 구간은 값을 셀 시간 범위다.

같은 60초의 목록 조회 4건과 12건을 비교하며 작은 조회 규칙을 완성해 보자.
같은 종류·같은 60초의 조회 횟수에 기준을 적용한다.
<image src="../assets/lesson3.svg">설명용 그림. 같은 종류·같은 60초의 조회 횟수에 기준을 적용한다.</image>
그림의 입력 자료에서 비교 기준을 거쳐 확인할 결과로 읽어 보자.
- 조회 규칙의 조건과 카운터를 완성한다.
- 4건과 12건의 기준10·20 판정 차이를 설명한다.
- 검토 후보를 공격 확정과 구분한다.
<table_of_contents/>
## 1단계. 무엇을 얼마나 셀지 고정하기
준비된 정상 예제와 비교 예제는 각각 60초의 교육용 HTTP 기록이다. 실제 DB에서 읽은 기록과 구분해 source=http\_demo라고 표시했다.
입력 파일 위치는 monitor/backend/learning/data이다. VS Code에서 이 폴더의 `normal-requests.json`과 `busy-requests.json`을 연다.
<table header-row="true" fit-page-width="true">
<tr>
<td>조건</td>
<td>세는 기록</td>
<td>제외하는 기록</td>
</tr>
<tr>
<td>방법</td>
<td>GET</td>
<td>POST 등 다른 방법</td>
</tr>
<tr>
<td>경로</td>
<td>/</td>
<td>/board/숫자 등 상세 경로</td>
</tr>
<tr>
<td>상태</td>
<td>200</td>
<td>404 등 다른 결과</td>
</tr>
<tr>
<td>종류</td>
<td>post\_list</td>
<td>post\_view·request\_error 등</td>
</tr>
</table>
상세 조회와 없는 글 조회를 섞으면 목록을 얼마나 읽었는지 설명하기 어렵다. 비교 대상을 같은 종류로 고정하고 구간 길이도 맞춰 보자.
먼저 결과 예상하기
1. `normal-requests.json`과 `busy-requests.json`에서 조건에 맞는 행을 읽는다.
2. 조건에 맞지 않는 상세 조회와 실패 조회를 왜 빼야 하는지 말한다.
<details>
<summary>예상 결과</summary>
	정상 자료는 4건, 비교 자료는 12건이다. 전체 행 수가 아니라 네 조건을 모두 만족한 목록 조회만 센다.
</details>
## 2단계. 조회 규칙의 다섯 줄 채우기
VS Code에서 monitor/backend/learning/checks.py를 연다. count\_views 함수의 수정 시작과 수정 끝 사이만 채운다. 다른 함수는 준비되어 있다.
`checks.py` — 시작 함수
```python
from learning.support import failures_before


def count_views(events):
    total = 0
    for event in events:
        valid_method = event["method"] == "GET"
        # >>>>> 수정 시작 (목록 조회 조건과 횟수) >>>>>
        # 경로 /, 상태200, 종류post_list인지 각각 확인한다.
        # 방법까지 네 조건이 맞으면 total에1을 더한다.
        # <<<<< 수정 끝 <<<<<
    return total

```
event는 기록 한 건이고 total은 맞는 기록을 센 횟수다. 방법 확인은 이미 준비됐으므로 경로·상태·종류를 비교한 뒤 모두 맞을 때 1을 더한다.
and는 여러 조건을 모두 만족해야 한다는 뜻이고 total += 1은 현재 횟수에 1을 더한다. if 아래에서 들여쓴 줄은 조건이 맞을 때만 실행된다.
조건과 횟수 완성하기
1. 수정 표시 사이에 경로 /·상태200·종류 post\_list를 확인하는 세 줄을 쓴다.
2. 네 조건이 모두 맞으면 total에 1을 더하고 Ctrl+S로 저장한다.
<details>
<summary>정답 함수와 해설</summary>
	`checks.py` — count\_views 함수
	```python
from learning.support import failures_before


def count_views(events):
    total = 0
    for event in events:
        valid_method = event["method"] == "GET"
        # >>>>> 수정 시작 (목록 조회 조건과 횟수) >>>>>
        valid_path = event["path"] == "/"
        valid_status = event["status_code"] == 200
        valid_kind = event["kind"] == "post_list"
        if valid_method and valid_path and valid_status and valid_kind:
            total += 1
        # <<<<< 수정 끝 <<<<<
    return total

	```
	and는 조건을 모두 만족해야 한다는 뜻이다. if 아래 total += 1은 들여써서 맞는 기록에만 적용한다.
</details>
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson3
```
```plain text
normal-requests.json 4 False
busy-requests.json 12 True
```
False는 10회 기준 미해당, True는 10회 이상인 검토 후보다. 이 출력은 교육용 자료의 계산이며 실제 general DB의 조회량이 아니다.
<details>
<summary>0건이 나오거나 실행 오류가 나면</summary>
	0건이면 수정 부분을 저장했는지, 종류가 post\_list인지 확인한다. 들여쓰기 오류가 나면 if 아래 total += 1의 위치를 정답 함수와 대조한다. 저장한 learning 폴더가 컨테이너에 연결되어 있어 이미지 재빌드 없이 다시 실행할 수 있다.
</details>
## 3단계. 같은 자료에서 기준 바꾸기
monitor/backend/learning/lesson3.py를 열어 threshold = 10을 threshold = 20으로 바꾸고 저장한다. 나머지 자료와 조건은 유지한다.
Windows CMD
```plain text
docker compose -f compose-monitor.yaml exec monitor-api python -m learning.lesson3
```
```plain text
normal-requests.json 4 False
busy-requests.json 12 False
```
12건이 달라진 것이 아니라 비교 경계가 20건으로 올라갔다. 낮은 기준은 많은 후보를 만들고 높은 기준은 더 적은 후보를 만든다.
판정 이유 말하기
1. 12건이 정상으로 확정된 것인지, 이번 20회 기준에만 미해당한 것인지 판단한다.
2. threshold = 10으로 되돌리고 저장한다.
<details>
<summary>해설</summary>
	기준 미해당이 무조건 정상이라는 뜻은 아니다. 기준을 넘은 것 역시 공격 확정이 아니다. 지금 규칙은 검토할 목록 조회량을 고르는 조건이다.
</details>
## 챙겨 가기 — 횟수와 기준을 함께 읽기
<table header-row="true" fit-page-width="true">
<tr>
<td>개념</td>
<td>적용한 판단</td>
</tr>
<tr>
<td>정상 기준</td>
<td>비교할 4건 자료를 둔다.</td>
</tr>
<tr>
<td>관찰 구간</td>
<td>두 교육용 자료의 60초를 맞춘다.</td>
</tr>
<tr>
<td>임계값</td>
<td>10과 20에서 같은 12건의 판단 차이를 말한다.</td>
</tr>
<tr>
<td>후보와 근거</td>
<td>조회한 원본 행을 근거로 남기고 공격으로 확정하지 않는다.</td>
</tr>
</table>
마지막에는 이 함수를 실제 HTTP에도 사용한다. 화면의 새 관찰 시작 이후 ID이며 첫 결과를 불러온 때의 최근 60초인 기록만 세도록 준비된 DB 읽기 코드가 범위를 정한다.
## 확인문제
**확인문제 1.** 정상 기준과 임계값은 어떻게 다른가?
<details>
<summary>정답과 해설</summary>
	정상 기준은 평소를 비교할 자료이고 임계값은 후보를 고르는 경계값이다. 정상 4건과 경계 10회는 역할이 다르다.
</details>
**확인문제 2.** 이 규칙이 세는 요청의 네 조건은 무엇인가?
<details>
<summary>정답과 해설</summary>
	방법GET·경로/·상태200·종류post\_list를 모두 만족해야 한다.
</details>
**확인문제 3.** 상세 조회를 목록 조회 횟수에 넣지 않는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	다른 종류의 요청을 섞으면 목록 조회량을 설명할 수 없기 때문이다.
</details>
**확인문제 4.** 전체 JSON 행 수와 규칙 횟수가 다른 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	상세·실패 요청 등 조건에 맞지 않는 행을 제외하기 때문이다.
</details>
**확인문제 5.** if 아래에서만 total을 늘리는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	모든 기록이 아니라 네 조건을 만족한 기록만 세기 위해서다.
</details>
**확인문제 6.** 관찰 구간 길이를 맞추는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	긴 시간 동안 세어 양이 늘어난 것을 같은 조건의 증가로 잘못 비교하지 않기 위해서다.
</details>
**확인문제 7.** 기준 10회에서 4건과 12건은 어떻게 표시되는가?
<details>
<summary>정답과 해설</summary>
	4건은미해당,12건은검토 후보다. 12가 10이상이기 때문이다.
</details>
**확인문제 8.** 기준 20회에서 같은 12건이 달라지는 이유는 무엇인가?
<details>
<summary>정답과 해설</summary>
	자료는그대로이고 12가 20미만이므로 이조건에는미해당이된다.
</details>
**확인문제 9.** True는 공격이 확정되었다는 뜻인가?
<details>
<summary>정답과 해설</summary>
	아니다. 정한 조건에 맞는검토 후보이며 정상작업도 조회가많을수있다.
</details>
**확인문제 10.** 실제 HTTP에 적용할 때 과거 요청을 어떻게 제외하는가?
<details>
<summary>정답과 해설</summary>
	새관찰시작에서현재마지막ID를읽고이후ID이면서최근 60초인기록만쓴다. 원본DB를삭제하지않는다.
</details>
## 되새김 문제
다음 질문에 말로 답할 수 있으면 이번 시간을 제대로 이해한 것이다.
- 어떤 출처와 단위를 비교했는가?
- 판정 기준과 근거는 무엇인가?
- 이 결과만으로 확정할 수 없는 것은 무엇인가?
다음 활동에서도 출처와 비교 기준을 확인하며 근거를 읽어 보자.