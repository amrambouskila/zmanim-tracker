from __future__ import annotations

from datetime import UTC, datetime

from src.models.solar_primitives_utc import SolarPrimitivesUTC


def test_solar_primitives_utc_construction() -> None:
    t = datetime(2024, 3, 20, 12, 0, 0, tzinfo=UTC)
    prim = SolarPrimitivesUTC(
        sunrise=t,
        sunset=t,
        solar_noon=t,
        civil_twilight_begin=t,
        civil_twilight_end=t,
        nautical_twilight_begin=t,
        nautical_twilight_end=t,
        astronomical_twilight_begin=t,
        astronomical_twilight_end=t,
    )
    assert prim.sunrise == t
    assert prim.astronomical_twilight_end == t
