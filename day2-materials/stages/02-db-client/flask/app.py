import os

from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False

VERSION = "v2"


@app.get("/")
def index():
    return '<a href="/api/hello">API 응답 보기</a>'


@app.get("/api/hello")
def hello():
    place = os.environ.get("APP_PLACE", "local")
    print(f"hello version={VERSION} place={place}", flush=True)
    return {"message": "Flask 배포 연습", "version": VERSION, "place": place}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
