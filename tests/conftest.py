from __future__ import annotations

import os

import pytest

from src.models.location import Location

os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")


@pytest.fixture
def nyc_location() -> Location:
    return Location(
        label="NYC",
        latitude=40.7128,
        longitude=-74.0060,
        timezone="America/New_York",
    )


@pytest.fixture
def jerusalem_location() -> Location:
    return Location(
        label="Jerusalem",
        latitude=31.7683,
        longitude=35.2137,
        timezone="Asia/Jerusalem",
    )


@pytest.fixture
def sydney_location() -> Location:
    return Location(
        label="Sydney",
        latitude=-33.8688,
        longitude=151.2093,
        timezone="Australia/Sydney",
    )
