from getpass import getpass

import psycopg

host = input("Session pooler Host: ").strip()
user = input("Session pooler User: ").strip()
password = getpass("DB 비밀번호: ")

with psycopg.connect(
    host=host,
    port=5432,
    dbname="postgres",
    user=user,
    password=password,
    sslmode="require",
    connect_timeout=10,
) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.messages (content) VALUES (%s) RETURNING id",
            ("Python에서 저장",),
        )
        message_id = cur.fetchone()[0]
        cur.execute(
            "SELECT id, content FROM public.messages WHERE id = %s",
            (message_id,),
        )
        print("저장한 행:", cur.fetchone())

print("저장 완료. SQL Editor에서도 같은 id를 조회하세요.")
