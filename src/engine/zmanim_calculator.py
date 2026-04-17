from __future__ import annotations

from datetime import date, timedelta

from src.engine.solar_angle_solver import SolarAngleSolver
from src.models.location import Location
from src.models.zmanim_row import ZmanimRow


class ZmanimCalculatorAngleBased:
    """Angle-based zmanim using observable twilight boundaries (GRA opinion)."""

    def __init__(
        self,
        alos_astronomical_edge_deg: float = 16.9,
        alos_nautical_edge_deg: float = 12.0,
        misheyakir_deg: float = 10.0,
        tzais_three_stars_deg: float = 8.5,
        tzais_civil_end_deg: float = 6.0,
        candle_lighting_offset_min: int = 18,
        shabbat_end_offset_min: int = 0,
        shabbat_end_basis: str = "tzais_three_stars",
    ) -> None:
        self.alos_astronomical_edge_deg = float(alos_astronomical_edge_deg)
        self.alos_nautical_edge_deg = float(alos_nautical_edge_deg)
        self.misheyakir_deg = float(misheyakir_deg)
        self.tzais_three_stars_deg = float(tzais_three_stars_deg)
        self.tzais_civil_end_deg = float(tzais_civil_end_deg)

        self.candle_lighting_offset_min = int(candle_lighting_offset_min)
        self.shabbat_end_offset_min = int(shabbat_end_offset_min)
        self.shabbat_end_basis = shabbat_end_basis

    def compute_for_day(self, loc: Location, day: date) -> ZmanimRow:
        tz = loc.timezone
        lat = loc.latitude
        lon = loc.longitude

        sunrise_local = SolarAngleSolver.sunrise_local(day, lat, lon, tz)
        sunset_local = SolarAngleSolver.sunset_local(day, lat, lon, tz)
        solar_noon_local = SolarAngleSolver.solar_noon_local(day, lat, lon, tz)

        tomorrow = day + timedelta(days=1)
        sunrise_tomorrow_local = SolarAngleSolver.sunrise_local(tomorrow, lat, lon, tz)
        chatzot_halaila = sunset_local + (sunrise_tomorrow_local - sunset_local) / 2

        shaah_zmanis = (sunset_local - sunrise_local) / 12
        latest_shema = sunrise_local + (shaah_zmanis * 3)
        latest_shacharit = sunrise_local + (shaah_zmanis * 4)

        earliest_mincha = sunrise_local + (shaah_zmanis * 6.5)
        mincha_ketana = sunrise_local + (shaah_zmanis * 9.5)
        plag_hamincha = sunrise_local + (shaah_zmanis * 10.75)

        alos_astronomical_edge = SolarAngleSolver.dawn_at_depression_local(
            day, lat, lon, tz, self.alos_astronomical_edge_deg
        )
        alos_nautical_edge = SolarAngleSolver.dawn_at_depression_local(
            day, lat, lon, tz, self.alos_nautical_edge_deg
        )
        tzais_three_stars = SolarAngleSolver.dusk_at_depression_local(
            day, lat, lon, tz, self.tzais_three_stars_deg
        )
        tzais_civil_end = SolarAngleSolver.dusk_at_depression_local(
            day, lat, lon, tz, self.tzais_civil_end_deg
        )
        misheyakir = SolarAngleSolver.dawn_at_depression_local(
            day, lat, lon, tz, self.misheyakir_deg
        )

        weekday = day.weekday()
        candle_lighting = None
        shabbat_ends = None

        if weekday == 4:
            candle_lighting = sunset_local - timedelta(minutes=self.candle_lighting_offset_min)

        if weekday == 5:
            base = tzais_three_stars if self.shabbat_end_basis == "tzais_three_stars" else tzais_civil_end
            shabbat_ends = base + timedelta(minutes=self.shabbat_end_offset_min)

        return ZmanimRow(
            day=day,
            location_label=loc.label,
            timezone=tz,
            sunrise=sunrise_local,
            sunset=sunset_local,
            solar_noon=solar_noon_local,
            chatzos=solar_noon_local,
            shaah_zmanis=shaah_zmanis,
            alos_astronomical_edge=alos_astronomical_edge,
            alos_nautical_edge=alos_nautical_edge,
            misheyakir=misheyakir,
            tzais_three_stars=tzais_three_stars,
            tzais_civil_end=tzais_civil_end,
            latest_shema=latest_shema,
            latest_shacharit=latest_shacharit,
            earliest_mincha=earliest_mincha,
            mincha_ketana=mincha_ketana,
            plag_hamincha=plag_hamincha,
            chatzot_halaila=chatzot_halaila,
            candle_lighting=candle_lighting,
            shabbat_ends=shabbat_ends,
        )
