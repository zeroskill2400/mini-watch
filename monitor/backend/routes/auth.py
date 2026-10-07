from flask import Blueprint, request
from werkzeug.security import check_password_hash
from repositories import users as user_repository

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "아이디와 비밀번호를 JSON으로 보내 주세요."}, 400
    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return {"error": "아이디와 비밀번호를 문자열로 보내 주세요."}, 400
    if not username.strip() or not password.strip():
        return {"error": "아이디와 비밀번호를 모두 입력해 주세요."}, 400

    user = user_repository.find_user(username.strip())
    if user is None or not check_password_hash(user["password_hash"], password):
        return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, 401

    return {"user": {"id": user["id"], "username": user["username"]}}
