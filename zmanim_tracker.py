from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import subprocess
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from timezonefinder import TimezoneFinder
import pgeocode
from zoneinfo import ZoneInfo
from astral import Observer
from astral.sun import dawn, dusk, sunrise, sunset, noon


@dataclass(frozen=True)
class Location:
    label: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True)
class SolarPrimitivesUTC:
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    civil_twilight_begin: datetime
    civil_twilight_end: datetime
    nautical_twilight_begin: datetime
    nautical_twilight_end: datetime
    astronomical_twilight_begin: datetime
    astronomical_twilight_end: datetime


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

    candle_lighting: Optional[datetime]
    shabbat_ends: Optional[datetime]


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
    def dawn_at_depression_local(day: date, lat: float, lon: float, tz_name: str, depression_deg: float) -> datetime:
        # depression_deg is positive (e.g. 18 means sun altitude == -18°)
        return dawn(
            SolarAngleSolver.observer(lat, lon),
            date=day,
            tzinfo=ZoneInfo(tz_name),
            depression=depression_deg,
        )

    @staticmethod
    def dusk_at_depression_local(day: date, lat: float, lon: float, tz_name: str, depression_deg: float) -> datetime:
        return dusk(
            SolarAngleSolver.observer(lat, lon),
            date=day,
            tzinfo=ZoneInfo(tz_name),
            depression=depression_deg,
        )


class LocationResolver:
    def __init__(self):
        self.tz_finder = TimezoneFinder()
        self.latitude_longitude_regex = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*[, ]\s*([+-]?\d+(?:\.\d+)?)\s*$")
        self.zipcode_regex = re.compile(r"^\s*(\d{5})(?:-\d{4})?\s*$")

    def resolve(self, location_input: str):
        location_input = (location_input or "").strip()
        if not location_input:
            raise ValueError("Location input is empty.")

        # 1) lat/lon
        latlon = self.try_parse_latlon(location_input)
        if latlon:
            lat, lon = latlon
            tz = self.timezone_for(lat, lon)
            return Location(label=f"{lat:.5f}, {lon:.5f}", latitude=lat, longitude=lon, timezone=tz)

        # 2) ZIP
        zip_code = self.try_parse_zip(location_input)
        if zip_code:
            loc = self.resolve_zip(zip_code)
            if loc:
                return loc
            # If ZIP lookup failed, fall back to Nominatim by passing the ZIP string.

        # 3) Nominatim free-text
        lat, lon, label = self.resolve_nominatim(location_input)
        tz = self.timezone_for(lat, lon)
        return Location(label=label, latitude=lat, longitude=lon, timezone=tz)

    def try_parse_latlon(self, s: str):
        m = self.latitude_longitude_regex.match(s)
        if not m:
            return None

        lat = float(m.group(1))
        lon = float(m.group(2))

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Latitude/longitude out of range.")

        return lat, lon

    def try_parse_zip(self, s: str):
        m = self.zipcode_regex.match(s)
        return m.group(1) if m else None

    def resolve_zip(self, zip_code: str):
        nomi = pgeocode.Nominatim("us")
        rec = nomi.query_postal_code(zip_code)
        if rec is not None and getattr(rec, "latitude", None) and getattr(rec, "longitude", None):
            lat = float(rec.latitude)
            lon = float(rec.longitude)
            label = f"US {zip_code}"
            tz = self.timezone_for(lat, lon)
            return Location(label=label, latitude=lat, longitude=lon, timezone=tz)

        # Fallback to Nominatim query for ZIP
        lat, lon, label = self.resolve_nominatim(zip_code)
        tz = self.timezone_for(lat, lon)
        return Location(label=label, latitude=lat, longitude=lon, timezone=tz)

    def resolve_nominatim(self, query: str):
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "Zmanim_Trackerv0.0.1"}
        params = {"q": query, "format": "json", "limit": 1}

        # Nominatim usage policy expects throttling; do a small sleep.
        time.sleep(0.8)

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"Could not resolve location: {query}")

        item = data[0]
        lat = float(item["lat"])
        lon = float(item["lon"])
        label = item.get("display_name") or query
        return lat, lon, label

    def timezone_for(self, lat: float, lon: float):
        tz = self.tz_finder.timezone_at(lat=lat, lng=lon)
        tz = self.require_iana_timezone(tz)
        return tz

    @staticmethod
    def require_iana_timezone(tz_name: Optional[str]):
        if not tz_name:
            return "UTC"

        ZoneInfo(tz_name)
        return tz_name


class ZmanimCalculatorAngleBased:
    """
    Angle-based zmanim using observable twilight boundaries.
    Supported range: 0°–18° (Sunrise-Sunset API limit).
    """

    def __init__(
        self,
        alos_astronomical_edge_deg: float = 16.9,
        alos_nautical_edge_deg: float = 12.0,
        misheyakir_deg: float = 10.0,
        tzais_three_stars_deg: float = 8.5,
        tzais_civil_end_deg: float = 6.0,
        candle_lighting_offset_min: int = 18,
        shabbat_end_offset_min: int = 0,
        shabbat_end_basis: str = "tzais_three_stars",  # or "tzais_civil_end"
    ):
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

        earliest_mincha = sunrise_local + (shaah_zmanis * 6.5)  # Mincha Gedola
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

        # Friday candle lighting
        if weekday == 4:
            candle_lighting = sunset_local - timedelta(minutes=self.candle_lighting_offset_min)

        # Saturday Shabbat ends
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


class ZmanimDataBuilder:
    def __init__(self, zmanim_calculator: ZmanimCalculatorAngleBased):
        self.zmanim_calculator = zmanim_calculator

    def build(self, loc: Location, start: date, end: date):
        if end < start:
            raise ValueError("End date must be on/after start date.")

        days = []
        cur = start
        while cur <= end:
            days.append(cur)
            cur = cur + timedelta(days=1)

        rows = []
        for d in days:
            row = self.zmanim_calculator.compute_for_day(loc, d)
            rows.append(row)

        df = self.rows_to_df(rows)
        return df

    def format_timestamp(self, dt: datetime) -> str:
        return "" if dt is None else dt.strftime("%Y-%m-%d %H:%M:%S %Z")

    def format_today(self, td: timedelta) -> str:
        total_seconds = int(td.total_seconds())
        sign = "-" if total_seconds < 0 else ""
        total_seconds = abs(total_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"

    def rows_to_df(self, rows):
        records = []
        for r in rows:
            a = {
                "date": r.day.isoformat(),
                "location": r.location_label,
                "timezone": r.timezone,
                "sunrise": self.format_timestamp(r.sunrise),
                "sunset": self.format_timestamp(r.sunset),
                "solar_noon": self.format_timestamp(r.solar_noon),
                "chatzos": self.format_timestamp(r.chatzos),
                "shaah_zmanis": self.format_today(r.shaah_zmanis),

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

            records.append(a)

        return pd.DataFrame.from_records(records)


class ZmanimPlotter:
    @staticmethod
    def time_to_minutes(series: pd.Series):
        dt = pd.to_datetime(series.str.slice(0, 19), errors="coerce")
        return dt.dt.hour * 60 + dt.dt.minute + dt.dt.second / 60.0

    @staticmethod
    def minutes_to_hhmmss_format(m: float):
        if pd.isna(m):
            return ""

        total = int(round(m * 60))  # minutes -> seconds
        hh = (total // 3600) % 24
        mm = (total % 3600) // 60
        ss = total % 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}"

    @staticmethod
    def _time_series_to_minutes_robust(series: pd.Series) -> pd.Series:
        """
        Converts a column containing either:
          - 'YYYY-MM-DD HH:MM:SS TZ' strings, OR
          - datetime-like strings, OR
          - blanks
        into minutes since midnight (float), with NaN where missing/unparseable.
        """
        s = series.fillna("").astype(str).str.strip()

        # First attempt: parse full string (handles many datetime string forms)
        dt = pd.to_datetime(s, errors="coerce")

        # Fallback: if that failed for most rows, slice off timezone and retry
        if dt.notna().sum() == 0:
            dt = pd.to_datetime(s.str.slice(0, 19), errors="coerce")

        return dt.dt.hour * 60 + dt.dt.minute + dt.dt.second / 60.0

    def plot_zmanim(self, df: pd.DataFrame, title: str = "Zmanim (Local Time)"):
        columns = [
            "sunrise",
            "alos_nautical_edge",
            "alos_astronomical_edge",
            "misheyakir",
            "latest_shema",
            "latest_shacharit",
            "earliest_mincha",
            "mincha_ketana",
            "plag_hamincha",
            "solar_noon",
            "sunset",
            "candle_lighting",
            "tzais_three_stars",
            "tzais_civil_end",
            "shabbat_ends",
            "chatzot_halaila",
        ]

        x = pd.to_datetime(df["date"], errors="coerce")

        fig = go.Figure()
        for col in columns:
            y = self.time_to_minutes(df[col])
            hover_times = y.apply(self.minutes_to_hhmmss_format)  # preformatted strings

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines+markers",
                    name=col,
                    customdata=hover_times,
                    hovertemplate="Date: %{x|%Y-%m-%d}<br>Time: %{customdata}<extra>%{fullData.name}</extra>",
                )
            )

        tickvals = list(range(0, 24 * 60, 60))
        ticktext = [self.minutes_to_hhmmss_format(t) for t in tickvals]

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis=dict(
                title="Time of Day",
                range=[0, 1439],
                tickmode="array",
                tickvals=tickvals,
                ticktext=ticktext,
                autorange=False,
            ),
            legend_title="Zman",
        )
        return fig


class ZmanimApp:
    def __init__(self):
        self.location_resolver = LocationResolver()
        self.zmanim_calculator = ZmanimCalculatorAngleBased()
        self.zmanim_data_builder = ZmanimDataBuilder(self.zmanim_calculator)
        self.zmanim_plotter = ZmanimPlotter()

    def render_todays_zmanim(self, df: pd.DataFrame, loc: Location) -> None:
        st.subheader("Today's Zmanim")

        # "Today" in the location's timezone
        today_local = datetime.now(ZoneInfo(loc.timezone)).date()
        today_str = today_local.isoformat()

        row = df.loc[df["date"] == today_str]
        if row.empty:
            st.info(f"No row for today ({today_str}). Adjust your date range.")
            return

        r = row.iloc[0].to_dict()

        # Pick the fields you want to show
        display_order = [
            "alos_astronomical_edge",
            "alos_nautical_edge",
            "misheyakir",
            "sunrise",
            "latest_shema",
            "latest_shacharit",
            "solar_noon",
            "earliest_mincha",
            "mincha_ketana",
            "plag_hamincha",
            "sunset",
            "tzais_three_stars",
            "tzais_civil_end",
            "chatzot_halaila",
            "shabbat_starts",
            "shabbat_ends",
        ]

        # Build a clean key/value table, skipping missing/blank columns
        items = []
        for k in display_order:
            if k in r:
                v = str(r[k]).strip()
                if v and v != "nan":
                    items.append((k, v))

        if not items:
            st.info("No zmanim available to display for today.")
            return

        # Render in columns for compactness
        cols = st.columns(3)
        for i, (k, v) in enumerate(items):
            cols[i % 3].metric(label=k, value=v)

    def run(self):
        st.set_page_config(page_title="Zmanim Chart", layout="wide")
        st.title("Zmanim Chart")

        with st.sidebar:
            st.header("Inputs")
            location_input = st.text_input("Location (ZIP, city/state, or lat,lon)", value="10001")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", value=date.today())
            with col2:
                end_date = st.date_input("End date", value=date.today() + timedelta(days=14))

            run_btn = st.button("Generate")

        if not run_btn:
            st.info("Set inputs and click Generate.")
            return

        loc = self.location_resolver.resolve(location_input)

        st.subheader("Resolved location")
        st.write(
            {
                "label": loc.label,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "timezone": loc.timezone,
            }
        )

        df = self.zmanim_data_builder.build(loc, start_date, end_date)

        self.render_todays_zmanim(df, loc)

        st.subheader("Zmanim Data")
        st.dataframe(df, use_container_width=True)

        st.subheader("Zmanim Visualization")
        fig = self.zmanim_plotter.plot_zmanim(df)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Download Zmanim")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name="zmanim.csv", mime="text/csv")



def main():
    zmanim_app = ZmanimApp()
    zmanim_app.run()


if __name__ == "__main__":
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        # running as the Streamlit app process
        main()
    else:
        # launcher path
        env = os.environ.copy()
        env["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__], check=True, env=env)
