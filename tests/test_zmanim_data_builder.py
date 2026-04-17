from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pandas as pd
import pytest

from src.engine.zmanim_calculator import ZmanimCalculatorAngleBased
from src.engine.zmanim_data_builder import ZmanimDataBuilder
from src.models.location import Location
from src.models.zmanim_row import ZmanimRow


@pytest.fixture
def builder() -> ZmanimDataBuilder:
    return ZmanimDataBuilder(ZmanimCalculatorAngleBased())


def test_build_single_day(builder: ZmanimDataBuilder, nyc_location: Location) -> None:
    df = builder.build(nyc_location, date(2024, 3, 20), date(2024, 3, 20))
    assert len(df) == 1
    assert df.iloc[0]["date"] == "2024-03-20"
    assert df.iloc[0]["location"] == "NYC"
    assert df.iloc[0]["timezone"] == "America/New_York"


def test_build_date_range(builder: ZmanimDataBuilder, nyc_location: Location) -> None:
    df = builder.build(nyc_location, date(2024, 3, 20), date(2024, 3, 22))
    assert len(df) == 3
    assert list(df["date"]) == ["2024-03-20", "2024-03-21", "2024-03-22"]


def test_build_raises_when_end_before_start(
    builder: ZmanimDataBuilder, nyc_location: Location
) -> None:
    with pytest.raises(ValueError, match="End date must be on/after start date"):
        builder.build(nyc_location, date(2024, 3, 22), date(2024, 3, 20))


def test_format_timestamp_handles_none(builder: ZmanimDataBuilder) -> None:
    assert builder.format_timestamp(None) == ""


def test_format_timestamp_formats_datetime(builder: ZmanimDataBuilder) -> None:
    dt = datetime(2024, 3, 20, 12, 34, 56, tzinfo=UTC)
    result = builder.format_timestamp(dt)
    assert result.startswith("2024-03-20 12:34:56")
    assert "UTC" in result


def test_format_duration_positive(builder: ZmanimDataBuilder) -> None:
    assert builder.format_duration(timedelta(hours=1, minutes=2, seconds=3)) == "01:02:03"


def test_format_duration_zero(builder: ZmanimDataBuilder) -> None:
    assert builder.format_duration(timedelta(0)) == "00:00:00"


def test_format_duration_negative(builder: ZmanimDataBuilder) -> None:
    assert builder.format_duration(timedelta(seconds=-125)) == "-00:02:05"


def test_rows_to_df_includes_shabbat_blanks_for_none(builder: ZmanimDataBuilder) -> None:
    t = datetime(2024, 3, 18, 12, 0, 0, tzinfo=UTC)  # Monday
    row = ZmanimRow(
        day=date(2024, 3, 18),
        location_label="NYC",
        timezone="UTC",
        sunrise=t,
        sunset=t,
        solar_noon=t,
        chatzos=t,
        shaah_zmanis=timedelta(minutes=60),
        alos_astronomical_edge=t,
        alos_nautical_edge=t,
        misheyakir=t,
        tzais_three_stars=t,
        tzais_civil_end=t,
        latest_shema=t,
        latest_shacharit=t,
        earliest_mincha=t,
        mincha_ketana=t,
        plag_hamincha=t,
        chatzot_halaila=t,
        candle_lighting=None,
        shabbat_ends=None,
    )
    df = builder.rows_to_df([row])
    assert df.iloc[0]["candle_lighting"] == ""
    assert df.iloc[0]["shabbat_ends"] == ""
    assert df.iloc[0]["shaah_zmanis"] == "01:00:00"


def test_df_has_expected_columns(builder: ZmanimDataBuilder, nyc_location: Location) -> None:
    df = builder.build(nyc_location, date(2024, 3, 22), date(2024, 3, 22))  # Friday
    expected_columns = {
        "date", "location", "timezone",
        "sunrise", "sunset", "solar_noon", "chatzos", "shaah_zmanis",
        "alos_astronomical_edge", "alos_nautical_edge", "misheyakir",
        "tzais_three_stars", "tzais_civil_end",
        "latest_shema", "latest_shacharit",
        "earliest_mincha", "mincha_ketana", "plag_hamincha",
        "chatzot_halaila", "candle_lighting", "shabbat_ends",
    }
    assert expected_columns.issubset(set(df.columns))
    assert isinstance(df, pd.DataFrame)
    # Friday: candle_lighting non-empty
    assert df.iloc[0]["candle_lighting"] != ""
