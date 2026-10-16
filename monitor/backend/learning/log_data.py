import json
import os
from pathlib import Path

LOG_DIRECTORY = Path(os.environ.get("CLASSROOM_LOG_DIR", "/classroom-logs"))


def read_complete_lines(filename):
    try:
        content = (LOG_DIRECTORY / filename).read_bytes()
    except FileNotFoundError:
        return []
    return [
        line.decode("utf-8").rstrip("\r\n")
        for line in content.splitlines(keepends=True)
        if line.endswith(b"\n") and line.strip()
    ]


def read_logs():
    return {
        "app": [json.loads(line) for line in read_complete_lines("app.jsonl")],
        "nginx": read_complete_lines("nginx.log"),
    }
