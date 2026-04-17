from __future__ import annotations

import re
import time
from zoneinfo import ZoneInfo

import pgeocode
import requests
from timezonefinder import TimezoneFinder

from src.models.location import Location

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "Zmanim_Trackerv0.0.1"
NOMINATIM_THROTTLE_SECONDS = 0.8


class LocationResolver:
    def __init__(self) -> None:
        self.tz_finder = TimezoneFinder()
        self.latitude_longitude_regex = re.compile(
            r"^\s*([+-]?\d+(?:\.\d+)?)\s*[, ]\s*([+-]?\d+(?:\.\d+)?)\s*$"
        )
        self.zipcode_regex = re.compile(r"^\s*(\d{5})(?:-\d{4})?\s*$")

    def resolve(self, location_input: str) -> Location:
        location_input = (location_input or "").strip()
        if not location_input:
            raise ValueError("Location input is empty.")

        latlon = self.try_parse_latlon(location_input)
        if latlon:
            lat, lon = latlon
            tz = self.timezone_for(lat, lon)
            return Location(label=f"{lat:.5f}, {lon:.5f}", latitude=lat, longitude=lon, timezone=tz)

        zip_code = self.try_parse_zip(location_input)
        if zip_code:
            loc = self.resolve_zip(zip_code)
            if loc:
                return loc

        lat, lon, label = self.resolve_nominatim(location_input)
        tz = self.timezone_for(lat, lon)
        return Location(label=label, latitude=lat, longitude=lon, timezone=tz)

    def try_parse_latlon(self, s: str) -> tuple[float, float] | None:
        m = self.latitude_longitude_regex.match(s)
        if not m:
            return None

        lat = float(m.group(1))
        lon = float(m.group(2))

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Latitude/longitude out of range.")

        return lat, lon

    def try_parse_zip(self, s: str) -> str | None:
        m = self.zipcode_regex.match(s)
        return m.group(1) if m else None

    def resolve_zip(self, zip_code: str) -> Location:
        nomi = pgeocode.Nominatim("us")
        rec = nomi.query_postal_code(zip_code)
        if rec is not None and getattr(rec, "latitude", None) and getattr(rec, "longitude", None):
            lat = float(rec.latitude)
            lon = float(rec.longitude)
            label = f"US {zip_code}"
            tz = self.timezone_for(lat, lon)
            return Location(label=label, latitude=lat, longitude=lon, timezone=tz)

        lat, lon, label = self.resolve_nominatim(zip_code)
        tz = self.timezone_for(lat, lon)
        return Location(label=label, latitude=lat, longitude=lon, timezone=tz)

    def resolve_nominatim(self, query: str) -> tuple[float, float, str]:
        headers = {"User-Agent": NOMINATIM_USER_AGENT}
        params = {"q": query, "format": "json", "limit": 1}

        time.sleep(NOMINATIM_THROTTLE_SECONDS)

        resp = requests.get(NOMINATIM_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"Could not resolve location: {query}")

        item = data[0]
        lat = float(item["lat"])
        lon = float(item["lon"])
        label = item.get("display_name") or query
        return lat, lon, label

    def timezone_for(self, lat: float, lon: float) -> str:
        tz = self.tz_finder.timezone_at(lat=lat, lng=lon)
        return self.require_iana_timezone(tz)

    @staticmethod
    def require_iana_timezone(tz_name: str | None) -> str:
        if not tz_name:
            return "UTC"

        ZoneInfo(tz_name)
        return tz_name
