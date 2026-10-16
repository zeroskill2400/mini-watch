from flask import Blueprint

from auth_helpers import api_access_error
from detection_service import read_detection, start_observation

detection_bp = Blueprint("detection", __name__)


@detection_bp.get("/api/detection")
def detection():
    error = api_access_error()
    if error:
        return error
    return read_detection()


@detection_bp.post("/api/detection/start")
def start():
    error = api_access_error()
    if error:
        return error
    start_observation()
    return read_detection(), 201
