from flask import Blueprint
from auth_helpers import api_access_error
from learning.report import build_report

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.get("/api/analysis")
def analysis():
    error = api_access_error()
    if error:
        return error
    try:
        return build_report()
    except (OSError, ValueError) as error:
        return {"error": str(error)}, 400
