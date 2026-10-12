import os

import psycopg
from dotenv import load_dotenv
from flask import Flask, request
from psycopg.rows import dict_row

load_dotenv(interpolate=False)
app = Flask(__name__)
app.json.ensure_ascii = False
VERSION = "v3"


def connect_db():
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "postgres"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        sslmode=os.environ.get("PGSSLMODE", "require"),
        connect_timeout=10,
        row_factory=dict_row,
    )


@app.get("/")
def index():
    return '<a href="/api/messages">메시지 목록 보기</a>'


@app.get("/api/hello")
def hello():
    place = os.environ.get("APP_PLACE", "local")
    print(f"hello version={VERSION} place={place}", flush=True)
    return {"message": "Flask 배포 연습", "version": VERSION, "place": place}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/messages")
def list_messages():
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT id, content FROM public.messages ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return {"messages": rows}


@app.post("/api/messages")
def add_message():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "JSON 객체를 보내세요."}, 400
    content = data.get("content")
    if not isinstance(content, str) or not 1 <= len(content.strip()) <= 200:
        return {"error": "내용은 1~200자로 입력하세요."}, 400
    with connect_db() as conn:
        saved = conn.execute(
            "INSERT INTO public.messages (content) VALUES (%s) RETURNING id, content",
            (content.strip(),),
        ).fetchone()
    return saved, 201


@app.errorhandler(psycopg.Error)
def database_error(error):
    app.logger.exception("메시지 DB 작업 실패")
    return {"error": "DB 연결과 테이블을 확인하세요."}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
