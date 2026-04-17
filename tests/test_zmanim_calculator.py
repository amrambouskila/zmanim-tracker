from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from src.engine.zmanim_calculator import ZmanimCalculatorAngleBased
from src.models.location import Location


def _minutes_diff(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 60.0


def test_calculator_default_parameters() -> None:
    c = ZmanimCalculatorAngleBased()
    assert c.alos_astronomical_edge_deg == 16.9
    assert c.alos_nautical_edge_deg == 12.0
    assert c.misheyakir_deg == 10.0
    assert c.tzais_three_stars_deg == 8.5
    assert c.tzais_civil_end_deg == 6.0
    assert c.candle_lighting_offset_min == 18
    assert c.shabbat_end_offset_min == 0
    assert c.shabbat_end_basis == "tzais_three_stars"


def test_calculator_custom_parameters_are_cast() -> None:
    c = ZmanimCalculatorAngleBased(
        alos_astronomical_edge_deg=18,
        candle_lighting_offset_min="40",  # type: ignore[arg-type]
        shabbat_end_offset_min=72,
    )
    assert c.alos_astronomical_edge_deg == 18.0
    assert isinstance(c.candle_lighting_offset_min, int)
    assert c.candle_lighting_offset_min == 40
    assert c.shabbat_end_offset_min == 72


def test_nyc_equinox_reference_zmanim(nyc_location: Location) -> None:
    """NYC vernal equinox 2024-03-20 against MyZmanim.com published values.

    Reference zmanim (EDT):
        sunrise ~ 06:59, sunset ~ 19:09, solar_noon ~ 13:04,
        latest_shema ~ 10:02, latest_shacharit ~ 11:03,
        mincha_gedolah ~ 13:34, plag_hamincha ~ 17:53.
    Tolerance: 2 minutes (solar-calc precision).
    """
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(nyc_location, date(2024, 3, 20))

    assert _minutes_diff(r.sunrise, datetime.fromisoformat("2024-03-20T06:58:42-04:00")) < 2.0
    assert _minutes_diff(r.sunset, datetime.fromisoformat("2024-03-20T19:08:28-04:00")) < 2.0
    assert _minutes_diff(r.solar_noon, datetime.fromisoformat("2024-03-20T13:03:27-04:00")) < 2.0
    assert _minutes_diff(r.chatzos, r.solar_noon) < 0.01

    # Shaah zmanis at equinox is ~60.8 min (12 equal hours of daylight).
    assert abs(r.shaah_zmanis.total_seconds() / 60.0 - 60.81) < 2.0

    assert _minutes_diff(r.latest_shema, datetime.fromisoformat("2024-03-20T10:01:09-04:00")) < 2.0
    assert _minutes_diff(r.latest_shacharit, datetime.fromisoformat("2024-03-20T11:01:58-04:00")) < 2.0


def test_chatzot_halaila_is_midpoint_of_night(nyc_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(nyc_location, date(2024, 3, 20))
    # Between sunset of 2024-03-20 and sunrise of 2024-03-21
    assert r.chatzot_halaila > r.sunset
    # Approximately 06:00 local the following morning (equinox)
    assert r.chatzot_halaila.date() in {date(2024, 3, 20), date(2024, 3, 21)}


def test_mincha_and_plag_ordering(nyc_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(nyc_location, date(2024, 3, 20))
    assert r.earliest_mincha < r.mincha_ketana < r.plag_hamincha < r.sunset


def test_angle_based_times_ordering(nyc_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(nyc_location, date(2024, 3, 20))
    # Earlier depression -> later dawn
    assert r.alos_astronomical_edge < r.alos_nautical_edge < r.misheyakir < r.sunrise
    # Tzais at higher depression is earlier than at lower
    assert r.sunset < r.tzais_civil_end < r.tzais_three_stars


def test_non_shabbat_day_has_no_candle_lighting_or_havdalah(jerusalem_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    # 2024-01-15 is a Monday
    r = c.compute_for_day(jerusalem_location, date(2024, 1, 15))
    assert r.candle_lighting is None
    assert r.shabbat_ends is None


def test_friday_sets_candle_lighting(jerusalem_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(jerusalem_location, date(2024, 1, 19))
    assert r.candle_lighting is not None
    assert r.shabbat_ends is None
    # 18 min before sunset
    assert (r.sunset - r.candle_lighting) == timedelta(minutes=18)


def test_friday_respects_custom_candle_offset(jerusalem_location: Location) -> None:
    c = ZmanimCalculatorAngleBased(candle_lighting_offset_min=40)
    r = c.compute_for_day(jerusalem_location, date(2024, 1, 19))
    assert r.candle_lighting is not None
    assert (r.sunset - r.candle_lighting) == timedelta(minutes=40)


def test_saturday_sets_shabbat_ends_at_three_stars(jerusalem_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(jerusalem_location, date(2024, 1, 20))
    assert r.candle_lighting is None
    assert r.shabbat_ends is not None
    assert r.shabbat_ends == r.tzais_three_stars


def test_saturday_with_civil_end_basis(jerusalem_location: Location) -> None:
    c = ZmanimCalculatorAngleBased(shabbat_end_basis="tzais_civil_end")
    r = c.compute_for_day(jerusalem_location, date(2024, 1, 20))
    assert r.shabbat_ends == r.tzais_civil_end


def test_saturday_applies_shabbat_end_offset(jerusalem_location: Location) -> None:
    c = ZmanimCalculatorAngleBased(shabbat_end_offset_min=18)
    r = c.compute_for_day(jerusalem_location, date(2024, 1, 20))
    assert r.shabbat_ends is not None
    assert (r.shabbat_ends - r.tzais_three_stars) == timedelta(minutes=18)


def test_southern_hemisphere_winter_solstice(sydney_location: Location) -> None:
    c = ZmanimCalculatorAngleBased()
    r = c.compute_for_day(sydney_location, date(2024, 6, 21))
    # Short winter day: sunrise after 07:00, sunset before 17:00
    assert r.sunrise.hour >= 6
    assert r.sunset.hour < 17
    # Shaah zmanis should be shorter than 60 min in Sydney winter
    assert r.shaah_zmanis.total_seconds() / 60.0 < 60.0


@pytest.mark.parametrize(
    "weekday_offset,expected_candle,expected_havdalah",
    [
        (0, False, False),  # Monday
        (1, False, False),  # Tuesday
        (2, False, False),  # Wednesday
        (3, False, False),  # Thursday
        (4, True, False),   # Friday
        (5, False, True),   # Saturday
        (6, False, False),  # Sunday
    ],
)
def test_weekday_shabbat_gating(
    nyc_location: Location,
    weekday_offset: int,
    expected_candle: bool,
    expected_havdalah: bool,
) -> None:
    c = ZmanimCalculatorAngleBased()
    # 2024-03-18 is a Monday; add weekday_offset days to sweep the week.
    d = date(2024, 3, 18) + timedelta(days=weekday_offset)
    r = c.compute_for_day(nyc_location, d)
    assert (r.candle_lighting is not None) is expected_candle
    assert (r.shabbat_ends is not None) is expected_havdalah
