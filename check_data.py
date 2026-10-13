from pathlib import Path
import pandas as pd

data_dir = Path("data/raw")

for file in sorted(data_dir.glob("*.csv")):
    try:
        df = pd.read_csv(file, nrows=5)
        total_rows = sum(1 for _ in open(file, encoding="utf-8-sig")) - 1

        print(f"\n{'=' * 60}")
        print(f"Файл: {file.name}")
        print(f"Строк данных: {total_rows:,}")
        print(f"Колонки: {list(df.columns)}")
        print(df.head(2).to_string(index=False))
    except Exception as e:
        print(f"\nОШИБКА: {file.name}: {e}")
