from __future__ import annotations

import pandas as pd
import pytest

from src.export.neutralize_csv_formulas import neutralize_csv_formulas


@pytest.mark.parametrize("payload", ['=HYPERLINK("http://x")', "+1+1", "-2", "@SUM(A1)", "\tcmd", "\rcmd"])
def test_formula_prefixed_strings_are_quoted(payload: str) -> None:
    df = pd.DataFrame({"label": [payload]})
    assert neutralize_csv_formulas(df)["label"].iloc[0] == f"'{payload}"


def test_plain_strings_numbers_and_nulls_are_untouched() -> None:
    df = pd.DataFrame({"label": ["Jerusalem", None], "value": [-3.5, 2.0]})
    out = neutralize_csv_formulas(df)
    assert out["label"].iloc[0] == "Jerusalem"
    assert pd.isna(out["label"].iloc[1])
    assert list(out["value"]) == [-3.5, 2.0]


def test_original_frame_is_not_mutated() -> None:
    df = pd.DataFrame({"label": ["=1"]})
    neutralize_csv_formulas(df)
    assert df["label"].iloc[0] == "=1"
