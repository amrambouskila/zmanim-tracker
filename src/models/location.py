from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    label: str
    latitude: float
    longitude: float
    timezone: str
