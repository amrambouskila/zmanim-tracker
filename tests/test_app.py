from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from src import app as app_module
from src.app import TODAYS_ZMANIM_DISPLAY_ORDER, ZmanimApp, main
from src.models.location import Location


def _make_mock_streamlit() -> MagicMock:
    mock = MagicMock()
    mock.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
    return mock


@pytest.fixture
def mock_st(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = _make_mock_streamlit()
    monkeypatch.setattr(app_module, "st", mock)
    return mock


@pytest.fixture
def app() -> ZmanimApp:
    instance = ZmanimApp(
        location_resolver=MagicMock(),
        zmanim_plotter=MagicMock(),
    )
    instance.zmanim_data_builder = MagicMock()
    return instance


def test_init_uses_defaults() -> None:
    instance = ZmanimApp()
    assert instance.location_resolver is not None
    assert instance.zmanim_calculator is not None
    assert instance.zmanim_data_builder is not None
    assert instance.zmanim_plotter is not None


def test_init_uses_injected_dependencies() -> None:
    resolver = MagicMock()
    calculator = MagicMock()
    plotter = MagicMock()
    instance = ZmanimApp(
        location_resolver=resolver,
        zmanim_calculator=calculator,
        zmanim_plotter=plotter,
    )
    assert instance.location_resolver is resolver
    assert instance.zmanim_calculator is calculator
    assert instance.zmanim_plotter is plotter


def test_run_without_button_press_shows_info_and_returns(
    app: ZmanimApp, mock_st: MagicMock
) -> None:
    mock_st.button.return_value = False
    app.run()
    mock_st.info.assert_any_call("Set inputs and click Generate.")
    app.location_resolver.resolve.assert_not_called()


def test_run_with_button_press_runs_full_flow(
    app: ZmanimApp, mock_st: MagicMock, nyc_location: Location
) -> None:
    mock_st.button.return_value = True
    mock_st.text_input.return_value = "10001"
    mock_st.date_input.side_effect = [date(2024, 3, 20), date(2024, 3, 21)]
    app.location_resolver.resolve.return_value = nyc_location

    today_str = datetime.now(ZoneInfo(nyc_location.timezone)).date().isoformat()
    df = pd.DataFrame(
        [{"date": today_str, **{k: f"{today_str} 12:00:00 EDT" for k in TODAYS_ZMANIM_DISPLAY_ORDER}}]
    )
    app.zmanim_data_builder.build.return_value = df

    app.run()

    app.location_resolver.resolve.assert_called_once_with("10001")
    app.zmanim_data_builder.build.assert_called_once()
    app.zmanim_plotter.plot_zmanim.assert_called_once_with(df)
    mock_st.dataframe.assert_called_once()
    mock_st.plotly_chart.assert_called_once()
    mock_st.download_button.assert_called_once()


def test_render_todays_zmanim_displays_metrics(
    app: ZmanimApp, mock_st: MagicMock, nyc_location: Location
) -> None:
    today_str = datetime.now(ZoneInfo(nyc_location.timezone)).date().isoformat()
    df = pd.DataFrame(
        [{"date": today_str, **{k: f"{today_str} 12:00:00 EDT" for k in TODAYS_ZMANIM_DISPLAY_ORDER}}]
    )
    app.render_todays_zmanim(df, nyc_location)
    mock_st.subheader.assert_any_call("Today's Zmanim")
    mock_st.columns.assert_any_call(3)


def test_render_todays_zmanim_no_row_for_today(
    app: ZmanimApp, mock_st: MagicMock, nyc_location: Location
) -> None:
    df = pd.DataFrame([{"date": "1999-01-01"}])
    app.render_todays_zmanim(df, nyc_location)
    mock_st.info.assert_called_once()
    assert "No row for today" in mock_st.info.call_args.args[0]


def test_render_todays_zmanim_skips_empty_and_nan_values(
    app: ZmanimApp, mock_st: MagicMock, nyc_location: Location
) -> None:
    today_str = datetime.now(ZoneInfo(nyc_location.timezone)).date().isoformat()
    row = {"date": today_str}
    for k in TODAYS_ZMANIM_DISPLAY_ORDER:
        row[k] = ""  # all empty -> skipped
    df = pd.DataFrame([row])
    app.render_todays_zmanim(df, nyc_location)
    mock_st.info.assert_called_with("No zmanim available to display for today.")


def test_main_constructs_and_runs_app(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_app = MagicMock()
    monkeypatch.setattr(app_module, "ZmanimApp", lambda: fake_app)
    main()
    fake_app.run.assert_called_once()


def test_run_with_button_press_handles_no_today_row(
    app: ZmanimApp, mock_st: MagicMock, nyc_location: Location
) -> None:
    mock_st.button.return_value = True
    mock_st.text_input.return_value = "10001"
    start = date(2024, 1, 1)
    end = start + timedelta(days=1)
    mock_st.date_input.side_effect = [start, end]
    app.location_resolver.resolve.return_value = nyc_location

    df = pd.DataFrame([{"date": "2024-01-01", **{k: "" for k in TODAYS_ZMANIM_DISPLAY_ORDER}}])
    app.zmanim_data_builder.build.return_value = df

    app.run()
    # render_todays_zmanim should hit the "No row for today" branch
    no_row_calls = [c for c in mock_st.info.call_args_list if "No row for today" in str(c)]
    assert no_row_calls
