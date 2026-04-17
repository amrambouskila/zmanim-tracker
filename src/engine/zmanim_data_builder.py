from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd

from src.engine.zmanim_calculator import ZmanimCalculatorAngleBased
from src.models.location import Location
from src.models.zmanim_row import ZmanimRow


class ZmanimDataBuilder:
    def __init__(self, zmanim_calculator: ZmanimCalculatorAngleBased) -> None:
        self.zmanim_calculator = zmanim_calculator

    def build(self, loc: Location, start: date, end: date) -> pd.DataFrame:
        if end < start:
            raise ValueError("End date must be on/after start date.")

        days: list[date] = []
        cur = start
        while cur <= end:
            days.append(cur)
            cur = cur + timedelta(days=1)

        rows = [self.zmanim_calculator.compute_for_day(loc, d) for d in days]
        return self.rows_to_df(rows)

    def format_timestamp(self, dt: datetime | None) -> str:
        return "" if dt is None else dt.strftime("%Y-%m-%d %H:%M:%S %Z")

    def format_duration(self, td: timedelta) -> str:
        total_seconds = int(td.total_seconds())
        sign = "-" if total_seconds < 0 else ""
        total_seconds = abs(total_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"

    def rows_to_df(self, rows: list[ZmanimRow]) -> pd.DataFrame:
        records = []
        for r in rows:
            records.append(
                {
                    "date": r.day.isoformat(),
                    "location": r.location_label,
                    "timezone": r.timezone,
                    "sunrise": self.format_timestamp(r.sunrise),
                    "sunset": self.format_timestamp(r.sunset),
                    "solar_noon": self.format_timestamp(r.solar_noon),
                    "chatzos": self.format_timestamp(r.chatzos),
                    "shaah_zmanis": self.format_duration(r.shaah_zmanis),
                    "alos_astronomical_edge": self.format_timestamp(r.alos_astronomical_edge),
                    "alos_nautical_edge": self.format_timestamp(r.alos_nautical_edge),
                    "misheyakir": self.format_timestamp(r.misheyakir),
                    "tzais_three_stars": self.format_timestamp(r.tzais_three_stars),
                    "tzais_civil_end": self.format_timestamp(r.tzais_civil_end),
                    "latest_shema": self.format_timestamp(r.latest_shema),
                    "latest_shacharit": self.format_timestamp(r.latest_shacharit),
                    "earliest_mincha": self.format_timestamp(r.earliest_mincha),
                    "mincha_ketana": self.format_timestamp(r.mincha_ketana),
                    "plag_hamincha": self.format_timestamp(r.plag_hamincha),
                    "chatzot_halaila": self.format_timestamp(r.chatzot_halaila),
                    "candle_lighting": self.format_timestamp(r.candle_lighting),
                    "shabbat_ends": self.format_timestamp(r.shabbat_ends),
                }
            )

        return pd.DataFrame.from_records(records)
