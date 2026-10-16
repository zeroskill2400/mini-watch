import os

from seed_classroom import main as prepare_classroom
from notice_state import prepare_notice
from request_history_state import prepare_request_history


def main():
    prepare_classroom()
    prepare_notice()
    prepare_request_history()
    os.execvp("waitress-serve", [
        "waitress-serve",
        "--host=0.0.0.0",
        f"--port={os.environ.get('PORT', '5000')}",
        "app:app",
    ])


if __name__ == "__main__":
    main()
