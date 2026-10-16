from werkzeug.security import generate_password_hash
from db import connect_db


def main():
    username = 'class-student'
    password = 'classroom1234!'
    with connect_db() as conn:
        result = conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s) '
            'ON CONFLICT (username) DO NOTHING',
            (username, generate_password_hash(password)),
        )
    if result.rowcount == 1:
        print(f'{username} 수업 계정을 준비했습니다.')
    else:
        print(f'{username} 계정이 이미 있습니다. 기존 비밀번호를 유지합니다.')


if __name__ == '__main__':
    main()
