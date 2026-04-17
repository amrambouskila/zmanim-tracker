from __future__ import annotations

from datetime import date, datetime

from astral import Observer

from src.engine.solar_angle_solver import SolarAngleSolver


def _minutes_diff(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 60.0


def test_observer_returns_astral_observer() -> None:
    obs = SolarAngleSolver.observer(40.7128, -74.0060)
    assert isinstance(obs, Observer)
    assert obs.latitude == 40.7128
    assert obs.longitude == -74.0060


def test_sunrise_local_nyc_equinox_matches_reference() -> None:
    # MyZmanim.com NYC 2024-03-20 sunrise is 06:59 EDT; astral gives 06:58:42 EDT.
    sr = SolarAngleSolver.sunrise_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    assert sr.tzinfo is not None
    assert sr.date() == date(2024, 3, 20)
    reference_sunrise = datetime.fromisoformat("2024-03-20T06:58:42-04:00")
    assert _minutes_diff(sr, reference_sunrise) < 2.0


def test_sunset_local_nyc_equinox_matches_reference() -> None:
    # MyZmanim.com NYC 2024-03-20 sunset is 19:09 EDT; astral gives 19:08:28 EDT.
    ss = SolarAngleSolver.sunset_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    reference_sunset = datetime.fromisoformat("2024-03-20T19:08:28-04:00")
    assert _minutes_diff(ss, reference_sunset) < 2.0


def test_solar_noon_is_between_sunrise_and_sunset() -> None:
    sr = SolarAngleSolver.sunrise_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    sn = SolarAngleSolver.solar_noon_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    ss = SolarAngleSolver.sunset_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    assert sr < sn < ss


def test_dawn_at_depression_earlier_than_sunrise() -> None:
    sr = SolarAngleSolver.sunrise_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    alos = SolarAngleSolver.dawn_at_depression_local(
        date(2024, 3, 20), 40.7128, -74.0060, "America/New_York", 16.9
    )
    assert alos < sr


def test_dusk_at_depression_later_than_sunset() -> None:
    ss = SolarAngleSolver.sunset_local(date(2024, 3, 20), 40.7128, -74.0060, "America/New_York")
    tzais = SolarAngleSolver.dusk_at_depression_local(
        date(2024, 3, 20), 40.7128, -74.0060, "America/New_York", 8.5
    )
    assert tzais > ss


def test_jerusalem_winter_sunrise_matches_myzmanim() -> None:
    # MyZmanim.com Jerusalem 2024-01-15 sunrise is 06:40 IST; astral gives 06:39:49 IST.
    sr = SolarAngleSolver.sunrise_local(date(2024, 1, 15), 31.7683, 35.2137, "Asia/Jerusalem")
    reference = datetime.fromisoformat("2024-01-15T06:39:49+02:00")
    assert _minutes_diff(sr, reference) < 2.0


def test_southern_hemisphere_winter_solstice_sunrise() -> None:
    sr = SolarAngleSolver.sunrise_local(date(2024, 6, 21), -33.8688, 151.2093, "Australia/Sydney")
    assert sr.tzinfo is not None
    assert sr.date() == date(2024, 6, 21)
