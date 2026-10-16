import os

from detection_service import prepare_observation
from seed_classroom import main as prepare_classroom
from soar_store import prepare_state
from url_playbook_automation import prepare_automation


def main():
    prepare_classroom()
    prepare_state()
    prepare_observation()
    prepare_automation()
    os.execvp("waitress-serve", [
        "waitress-serve",
        "--host=0.0.0.0",
        f"--port={os.environ.get('PORT', '5000')}",
        "app:app",
    ])


if __name__ == "__main__":
    main()
