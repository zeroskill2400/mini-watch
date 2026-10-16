from flask import Blueprint, request

from ai_client import AIError, analyze_case
from auth_helpers import api_access_error
from investigation_service import read_investigation

investigation_bp = Blueprint("investigation", __name__)


@investigation_bp.get("/api/investigation")
def investigation():
    error = api_access_error()
    if error:
        return error
    return read_investigation()


@investigation_bp.post("/api/investigation/policy")
def policy():
    error = api_access_error()
    if error:
        return error
    return {"error": "Day5에서는 대응 요청의 사람 승인과 복구 승인을 사용해 주세요."}, 409


@investigation_bp.post("/api/investigation/ai")
def ai():
    error = api_access_error()
    if error:
        return error
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {"case_id"} or not isinstance(data["case_id"], str) or not 1 <= len(data["case_id"]) <= 128:
        return {"error": "현재 사건의 case_id만 보내 주세요."}, 400
    state = read_investigation()
    case = next((candidate for candidate in state["cases"] if candidate["id"] == data["case_id"]), None)
    if case is None:
        return {"error": "현재 관찰에서 사건을 찾지 못했습니다. 사건을 새로고침해 주세요."}, 404
    try:
        return analyze_case(case, state["correlation"])
    except AIError as error:
        return {"error": str(error), "code": error.code}, error.status
