
import csv
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


# Загружаем настройки из .env
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "raw"

load_dotenv(BASE_DIR / ".env")


# Соответствие CSV-файлов таблицам PostgreSQL
FILES = {
    "olist_customers_dataset.csv": "customers",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}


# Исправляем известную опечатку в названиях столбцов.
# Например, lenght -> length.
COLUMN_ALIASES = {
    "product_name_lenght": "product_name_length",
    "product_description_lenght": "product_description_length",
}


def get_csv_header(path: Path) -> list[str]:
    """Читаем заголовок CSV с учётом возможного BOM."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)

    if not header:
        raise ValueError(f"CSV пустой или не содержит заголовок: {path}")

    return [column.strip() for column in header]


def get_db_columns(cursor, table: str) -> list[str]:
    """Получаем названия столбцов целевой таблицы."""
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'raw'
          AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (table,),
    )

    return [row[0] for row in cursor.fetchall()]


def main() -> None:
    # Проверяем наличие всех файлов до подключения к базе.
    missing_files = [
        filename
        for filename in FILES
        if not (DATA_DIR / filename).is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Не найдены CSV-файлы:\n"
            + "\n".join(missing_files)
        )

    # Проверяем настройки подключения.
    required_vars = (
        "PGHOST",
        "PGPORT",
        "PGDATABASE",
        "PGUSER",
        "PGPASSWORD",
    )

    missing_vars = [
        name for name in required_vars if not os.getenv(name)
    ]

    if missing_vars:
        raise ValueError(
            "Не заданы переменные в .env: "
            + ", ".join(missing_vars)
        )

    total_rows = 0

    # При ошибке контекст соединения откатит транзакцию.
    with psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=int(os.getenv("PGPORT")),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    ) as conn:

        with conn.cursor() as cur:
            for filename, table in FILES.items():
                path = DATA_DIR / filename

                print(f"\nЗагружаем {filename}...")

                # 1. Читаем заголовок CSV.
                header = get_csv_header(path)

                # 2. Получаем схему таблицы.
                db_columns = get_db_columns(cur, table)

                if not db_columns:
                    raise ValueError(
                        f"Таблица raw.{table} не найдена "
                        "или в ней нет столбцов."
                    )

                # 3. Приводим известные опечатки к правильным именам.
                copy_columns = [
                    COLUMN_ALIASES.get(column, column)
                    for column in header
                ]

                # 4. Проверяем, что столбцы CSV соответствуют таблице.
                if len(copy_columns) != len(set(copy_columns)):
                    raise ValueError(
                        f"После исправления названий в {filename} "
                        "появились повторяющиеся столбцы."
                    )

                missing_columns = set(copy_columns) - set(db_columns)
                extra_columns = set(db_columns) - set(copy_columns)

                if missing_columns or extra_columns:
                    print("Столбцы CSV после нормализации:")
                    print(copy_columns)

                    print("Столбцы PostgreSQL:")
                    print(db_columns)

                    raise ValueError(
                        f"Структура CSV не совпадает с raw.{table}.\n"
                        f"Нет в таблице: {sorted(missing_columns)}\n"
                        f"Нет в CSV: {sorted(extra_columns)}"
                    )

                # 5. Готовим COPY с явным списком столбцов.
                # Это позволяет не зависеть от порядка столбцов
                # в таблице PostgreSQL.
                copy_query = sql.SQL(
                    """
                    COPY {}.{} ({})
                    FROM STDIN
                    WITH (FORMAT CSV, HEADER TRUE, NULL '')
                    """
                ).format(
                    sql.Identifier("raw"),
                    sql.Identifier(table),
                    sql.SQL(", ").join(
                        sql.Identifier(column)
                        for column in copy_columns
                    ),
                )

                # 6. Очищаем таблицу только после проверки схемы.
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}.{}").format(
                        sql.Identifier("raw"),
                        sql.Identifier(table),
                    )
                )

                # 7. Загружаем CSV.
                with path.open(
                    "r",
                    encoding="utf-8-sig",
                    newline="",
                ) as csv_file:
                    cur.copy_expert(
                        copy_query.as_string(conn),
                        csv_file,
                    )

                # 8. Проверяем количество загруженных строк.
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                        sql.Identifier("raw"),
                        sql.Identifier(table),
                    )
                )

                count = cur.fetchone()[0]
                total_rows += count

                print(f"Загружено строк: {count:,}")

        # Соединение подтвердит транзакцию при успешном выходе.
        # При ошибке изменения будут отменены.

    print("\nЗагрузка завершена успешно!")
    print(f"Всего загружено строк: {total_rows:,}")


if __name__ == "__main__":
    main()
