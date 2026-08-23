from __future__ import annotations

import pandas as pd

FORMULA_TRIGGER_CHARACTERS = ("=", "+", "-", "@", "\t", "\r")


def neutralize_csv_formulas(df: pd.DataFrame) -> pd.DataFrame:
    """Prefix string cells that a spreadsheet would evaluate as a formula so exported CSVs cannot execute."""
    guarded = df.copy()
    for column in guarded.select_dtypes(include=["object", "string"]).columns:
        guarded[column] = guarded[column].map(_neutralize_cell)
    return guarded


def _neutralize_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(FORMULA_TRIGGER_CHARACTERS):
        return f"'{value}"
    return value
