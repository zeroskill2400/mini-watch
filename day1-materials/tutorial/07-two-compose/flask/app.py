import os
import psycopg
from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False

@app.get("/api/hello")
def hello():
    return {"message": "코드를 바꾸고 다시 빌드했습니다."}

@app.get("/api/messages")
def messages():
    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=3,
    ) as conn:
        rows = conn.execute("SELECT body FROM messages ORDER BY id").fetchall()
    return {"messages": [row[0] for row in rows]}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
