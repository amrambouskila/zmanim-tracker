from __future__ import annotations

import dataclasses

import pytest

from src.models.location import Location


def test_location_construction() -> None:
    loc = Location(label="Test", latitude=1.0, longitude=2.0, timezone="UTC")
    assert loc.label == "Test"
    assert loc.latitude == 1.0
    assert loc.longitude == 2.0
    assert loc.timezone == "UTC"


def test_location_is_frozen() -> None:
    loc = Location(label="Test", latitude=1.0, longitude=2.0, timezone="UTC")
    with pytest.raises(dataclasses.FrozenInstanceError):
        loc.label = "changed"  # type: ignore[misc]
