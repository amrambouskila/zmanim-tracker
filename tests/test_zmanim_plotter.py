from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.visualization.zmanim_plotter import ZMANIM_PLOT_COLUMNS, ZmanimPlotter


@pytest.fixture
def plotter() -> ZmanimPlotter:
    return ZmanimPlotter()


def test_time_to_minutes_parses_iso_timestamps(plotter: ZmanimPlotter) -> None:
    s = pd.Series(["2024-03-20 06:30:45 EDT", "2024-03-20 18:15:00 EDT"])
    result = plotter.time_to_minutes(s)
    assert result.iloc[0] == pytest.approx(6 * 60 + 30 + 45 / 60.0)
    assert result.iloc[1] == pytest.approx(18 * 60 + 15)


def test_time_to_minutes_returns_nan_for_unparseable(plotter: ZmanimPlotter) -> None:
    s = pd.Series(["", "not a date"])
    result = plotter.time_to_minutes(s)
    assert result.isna().all()


def test_minutes_to_hhmmss_format_typical(plotter: ZmanimPlotter) -> None:
    assert plotter.minutes_to_hhmmss_format(6 * 60 + 30) == "06:30:00"
    assert plotter.minutes_to_hhmmss_format(0.5) == "00:00:30"


def test_minutes_to_hhmmss_format_returns_empty_for_nan(plotter: ZmanimPlotter) -> None:
    assert plotter.minutes_to_hhmmss_format(float("nan")) == ""
    assert plotter.minutes_to_hhmmss_format(math.nan) == ""


def test_minutes_to_hhmmss_format_wraps_24h(plotter: ZmanimPlotter) -> None:
    # 24*60 minutes wraps to 00:00:00
    assert plotter.minutes_to_hhmmss_format(24 * 60) == "00:00:00"


def test_plot_zmanim_returns_figure_with_one_trace_per_column(plotter: ZmanimPlotter) -> None:
    rows = []
    for d in ["2024-03-20", "2024-03-21"]:
        row = {"date": d}
        for col in ZMANIM_PLOT_COLUMNS:
            row[col] = f"{d} 12:00:00 UTC"
        rows.append(row)
    df = pd.DataFrame(rows)

    fig = plotter.plot_zmanim(df, title="Test Title")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == len(ZMANIM_PLOT_COLUMNS)
    assert fig.layout.title.text == "Test Title"
    assert fig.layout.yaxis.range == (0, 1439)
    assert fig.layout.xaxis.title.text == "Date"
    # Tick array spans 24 hours, hourly
    assert len(fig.layout.yaxis.tickvals) == 24


def test_plot_zmanim_uses_default_title(plotter: ZmanimPlotter) -> None:
    df = pd.DataFrame([{"date": "2024-03-20", **{c: "2024-03-20 12:00:00 UTC" for c in ZMANIM_PLOT_COLUMNS}}])
    fig = plotter.plot_zmanim(df)
    assert fig.layout.title.text == "Zmanim (Local Time)"
