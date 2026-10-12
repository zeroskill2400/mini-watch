from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False

@app.get("/api/hello")
def hello():
    return {"message": "코드를 바꾸고 다시 빌드했습니다."}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
