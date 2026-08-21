import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List


def scale_csv(input_path: str, output_path: str, scale_factor: int, seed: int = 42) -> int:
    np.random.seed(seed)

    df = pd.read_csv(input_path)
    original_rows = len(df)

    if scale_factor == 1:
        df.to_csv(output_path, index=False)
        return original_rows

    target_rows = original_rows * scale_factor

    repeats = int(np.ceil(target_rows / original_rows))
    scaled_df = pd.concat([df] * repeats, ignore_index=True)
    scaled_df = scaled_df.iloc[:target_rows]

    id_pattern = re.compile(r'.*[Ii][Dd]$|.*_id$|.*_Id$')

    for col in df.columns:
        if id_pattern.match(col):
            scaled_df[col] = range(1, target_rows + 1)
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            noise = np.random.uniform(0.99, 1.01, size=target_rows)
            scaled_df[col] = scaled_df[col] * noise
            if pd.api.types.is_integer_dtype(df[col]):
                scaled_df[col] = scaled_df[col].round().astype(int)
            continue

        if pd.api.types.is_object_dtype(df[col]):
            unique_vals = df[col].dropna().unique().tolist()
            if unique_vals:
                scaled_df[col] = np.random.choice(unique_vals, size=target_rows)

    scaled_df.to_csv(output_path, index=False)
    return target_rows


def find_csv_files(task_folder: str) -> List[str]:
    folder = Path(task_folder)
    csv_files = []
    for f in folder.glob("*.csv"):
        if f.name != "output.csv":
            csv_files.append(str(f))
    return sorted(csv_files)


def estimate_input_rows(task_folder: str) -> int:
    csv_files = find_csv_files(task_folder)
    if not csv_files:
        return 0
    df = pd.read_csv(csv_files[0])
    return len(df)