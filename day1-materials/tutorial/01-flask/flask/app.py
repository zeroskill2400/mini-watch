from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False

@app.get("/api/hello")
def hello():
    return {"message": "Flask 컨테이너입니다."}
