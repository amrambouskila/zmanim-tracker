from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class ZmanimRow:
    day: date
    location_label: str
    timezone: str

    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    chatzos: datetime
    shaah_zmanis: timedelta

    alos_astronomical_edge: datetime
    alos_nautical_edge: datetime
    misheyakir: datetime
    tzais_three_stars: datetime
    tzais_civil_end: datetime

    latest_shema: datetime
    latest_shacharit: datetime

    earliest_mincha: datetime
    mincha_ketana: datetime
    plag_hamincha: datetime

    chatzot_halaila: datetime

    candle_lighting: datetime | None
    shabbat_ends: datetime | None
