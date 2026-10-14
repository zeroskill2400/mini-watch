import json
from pathlib import Path

CASE_FILE = Path(__file__).with_name("data") / "case.json"


def read_case():
    if not CASE_FILE.exists():
        raise FileNotFoundError("실습 원본이 없습니다. start-class를 먼저 실행하세요.")
    return json.loads(CASE_FILE.read_text(encoding="utf-8"))
