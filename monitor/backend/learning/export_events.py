import json
from db import connect_db

# 화면과 같은 최신50건을 DB에서 읽어 한 줄에 기록 하나씩 출력한다.
# 계정·비밀번호·게시글 내용은 읽지 않는다.
with connect_db() as conn:
    rows = conn.execute("SELECT * FROM http_events ORDER BY id DESC LIMIT 50").fetchall()
for row in reversed(rows):
    row["occurred_at"] = row["occurred_at"].isoformat()
    print(json.dumps(row, ensure_ascii=False))
