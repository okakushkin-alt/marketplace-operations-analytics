from pathlib import Path
import pandas as pd

for file in sorted(Path("data/raw").glob("*.csv")):
    rows = 0
    columns = None

    for chunk in pd.read_csv(file, chunksize=100_000):
        rows += len(chunk)
        if columns is None:
            columns = len(chunk.columns)

    print(f"{file.name:45} {rows:>8,} строк | {columns} колонок")
