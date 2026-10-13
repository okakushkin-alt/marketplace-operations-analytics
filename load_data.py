
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "raw"

load_dotenv(BASE_DIR / ".env")


# CSV-файл -> таблица PostgreSQL
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

# Исправляем опечатки в названиях столбцов CSV.
COLUMN_ALIASES = {
    "product_name_lenght": "product_name_length",
    "product_description_lenght": "product_description_length",
}


def main():
    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.getenv("PGDATABASE"),
    )

    engine = create_engine(database_url)
    total_rows = 0

    try:
        # Все таблицы загружаются в рамках одной транзакции.
        with engine.begin() as connection:
            for filename, table in FILES.items():
                path = DATA_DIR / filename

                print(f"\nЗагружаем {filename}...")

                # Читаем один CSV в DataFrame.
                df = pd.read_csv(path, encoding="utf-8-sig")

                # Приводим названия столбцов к схеме PostgreSQL.
                df.rename(columns=COLUMN_ALIASES, inplace=True)

                # Очищаем старые данные перед повторной загрузкой.
                connection.execute(
                    text(f"TRUNCATE TABLE raw.{table}")
                )

                # Загружаем данные пакетами по 2000 строк.
                df.to_sql(
                    name=table,
                    con=connection,
                    schema="raw",
                    if_exists="append",
                    index=False,
                    method="multi",
                    chunksize=2000,
                )

                rows = len(df)
                total_rows += rows

                print(f"Загружено строк: {rows:,}")

                del df

        print("\nЗагрузка завершена успешно!")
        print(f"Всего загружено строк: {total_rows:,}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
