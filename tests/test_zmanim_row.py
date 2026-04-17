from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from src.models.zmanim_row import ZmanimRow


def _make_row(
    candle_lighting: datetime | None = None,
    shabbat_ends: datetime | None = None,
) -> ZmanimRow:
    t = datetime(2024, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    return ZmanimRow(
        day=date(2024, 3, 20),
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
        candle_lighting=candle_lighting,
        shabbat_ends=shabbat_ends,
    )


def test_zmanim_row_defaults_to_none_shabbat_fields() -> None:
    row = _make_row()
    assert row.candle_lighting is None
    assert row.shabbat_ends is None
    assert row.location_label == "NYC"


def test_zmanim_row_holds_shabbat_fields() -> None:
    t = datetime(2024, 3, 22, 18, 0, 0, tzinfo=timezone.utc)
    row = _make_row(candle_lighting=t, shabbat_ends=t)
    assert row.candle_lighting == t
    assert row.shabbat_ends == t
