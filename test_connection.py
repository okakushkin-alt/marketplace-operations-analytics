import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

try:
    with psycopg.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version();")
            db, user, version = cur.fetchone()

    print("Подключение успешно!")
    print(f"База данных: {db}")
    print(f"Пользователь: {user}")
    print(f"PostgreSQL: {version.split(',')[0]}")

except Exception as e:
    print(f"Ошибка подключения: {type(e).__name__}: {e}")
