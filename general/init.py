import os

from seed_classroom import main as prepare_classroom


def main():
    prepare_classroom()
    os.execvp("waitress-serve", [
        "waitress-serve",
        "--host=0.0.0.0",
        f"--port={os.environ.get('PORT', '5000')}",
        "app:app",
    ])


if __name__ == "__main__":
    main()
