from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from astral import Observer
from astral.sun import dawn, dusk, noon, sunrise, sunset


class SolarAngleSolver:
    @staticmethod
    def observer(lat: float, lon: float) -> Observer:
        return Observer(latitude=lat, longitude=lon)

    @staticmethod
    def sunrise_local(day: date, lat: float, lon: float, tz_name: str) -> datetime:
        return sunrise(SolarAngleSolver.observer(lat, lon), date=day, tzinfo=ZoneInfo(tz_name))

    @staticmethod
    def sunset_local(day: date, lat: float, lon: float, tz_name: str) -> datetime:
        return sunset(SolarAngleSolver.observer(lat, lon), date=day, tzinfo=ZoneInfo(tz_name))

    @staticmethod
    def solar_noon_local(day: date, lat: float, lon: float, tz_name: str) -> datetime:
        return noon(SolarAngleSolver.observer(lat, lon), date=day, tzinfo=ZoneInfo(tz_name))

    @staticmethod
    def dawn_at_depression_local(
        day: date, lat: float, lon: float, tz_name: str, depression_deg: float
    ) -> datetime:
        return dawn(
            SolarAngleSolver.observer(lat, lon),
            date=day,
            tzinfo=ZoneInfo(tz_name),
            depression=depression_deg,
        )

    @staticmethod
    def dusk_at_depression_local(
        day: date, lat: float, lon: float, tz_name: str, depression_deg: float
    ) -> datetime:
        return dusk(
            SolarAngleSolver.observer(lat, lon),
            date=day,
            tzinfo=ZoneInfo(tz_name),
            depression=depression_deg,
        )
