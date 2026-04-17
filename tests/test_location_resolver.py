from __future__ import annotations

from types import SimpleNamespace

import pytest
import responses

from src.location import location_resolver as resolver_module
from src.location.location_resolver import NOMINATIM_URL, LocationResolver
from src.models.location import Location


@pytest.fixture(autouse=True)
def _skip_nominatim_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resolver_module.time, "sleep", lambda _: None)


@pytest.fixture
def resolver() -> LocationResolver:
    return LocationResolver()


class FakePgeocodeHit:
    def __init__(self, lat: float, lon: float) -> None:
        self._ns = SimpleNamespace(latitude=lat, longitude=lon)

    def query_postal_code(self, _zip: str) -> SimpleNamespace:
        return self._ns


class FakePgeocodeMiss:
    def query_postal_code(self, _zip: str) -> SimpleNamespace:
        return SimpleNamespace(latitude=None, longitude=None)


def _patch_pgeocode(monkeypatch: pytest.MonkeyPatch, fake: object) -> None:
    monkeypatch.setattr(resolver_module.pgeocode, "Nominatim", lambda _country: fake)


def test_resolve_empty_string_raises(resolver: LocationResolver) -> None:
    with pytest.raises(ValueError, match="empty"):
        resolver.resolve("")


def test_resolve_whitespace_raises(resolver: LocationResolver) -> None:
    with pytest.raises(ValueError, match="empty"):
        resolver.resolve("   ")


def test_resolve_latlon_with_comma(resolver: LocationResolver) -> None:
    loc = resolver.resolve("40.7128, -74.0060")
    assert isinstance(loc, Location)
    assert loc.latitude == pytest.approx(40.7128)
    assert loc.longitude == pytest.approx(-74.0060)
    assert loc.timezone == "America/New_York"
    assert loc.label == "40.71280, -74.00600"


def test_resolve_latlon_with_space(resolver: LocationResolver) -> None:
    loc = resolver.resolve("31.7683 35.2137")
    assert loc.latitude == pytest.approx(31.7683)
    assert loc.timezone == "Asia/Jerusalem"


def test_resolve_latlon_out_of_range_raises(resolver: LocationResolver) -> None:
    with pytest.raises(ValueError, match="out of range"):
        resolver.resolve("200.0, 0.0")


def test_resolve_zip_with_pgeocode_hit(
    resolver: LocationResolver, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pgeocode(monkeypatch, FakePgeocodeHit(40.7128, -74.0060))
    loc = resolver.resolve("10001")
    assert loc.label == "US 10001"
    assert loc.latitude == pytest.approx(40.7128)
    assert loc.timezone == "America/New_York"


def test_resolve_zip_extended_format(
    resolver: LocationResolver, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pgeocode(monkeypatch, FakePgeocodeHit(40.7128, -74.0060))
    loc = resolver.resolve("10001-1234")
    assert loc.label == "US 10001"


@responses.activate
def test_resolve_zip_falls_back_to_nominatim_on_miss(
    resolver: LocationResolver, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pgeocode(monkeypatch, FakePgeocodeMiss())
    responses.add(
        responses.GET,
        NOMINATIM_URL,
        json=[{"lat": "40.7128", "lon": "-74.0060", "display_name": "New York, USA"}],
        status=200,
    )
    loc = resolver.resolve("99999")
    assert loc.label == "New York, USA"
    assert loc.latitude == pytest.approx(40.7128)


@responses.activate
def test_resolve_freetext_via_nominatim(resolver: LocationResolver) -> None:
    responses.add(
        responses.GET,
        NOMINATIM_URL,
        json=[{"lat": "31.7683", "lon": "35.2137", "display_name": "Jerusalem, Israel"}],
        status=200,
    )
    loc = resolver.resolve("Jerusalem")
    assert loc.label == "Jerusalem, Israel"
    assert loc.timezone == "Asia/Jerusalem"


@responses.activate
def test_resolve_freetext_without_display_name_uses_query(resolver: LocationResolver) -> None:
    responses.add(
        responses.GET,
        NOMINATIM_URL,
        json=[{"lat": "40.7128", "lon": "-74.0060"}],
        status=200,
    )
    loc = resolver.resolve("somewhere")
    assert loc.label == "somewhere"


@responses.activate
def test_resolve_nominatim_empty_response_raises(resolver: LocationResolver) -> None:
    responses.add(responses.GET, NOMINATIM_URL, json=[], status=200)
    with pytest.raises(ValueError, match="Could not resolve"):
        resolver.resolve("thisplacedoesnotexistxyz")


@responses.activate
def test_resolve_nominatim_http_error_raises(resolver: LocationResolver) -> None:
    responses.add(responses.GET, NOMINATIM_URL, json={"error": "bad"}, status=500)
    with pytest.raises(Exception):  # requests.HTTPError
        resolver.resolve("somewhere")


def test_try_parse_latlon_none_for_non_latlon(resolver: LocationResolver) -> None:
    assert resolver.try_parse_latlon("New York") is None


def test_try_parse_zip_none_for_non_zip(resolver: LocationResolver) -> None:
    assert resolver.try_parse_zip("ABCDE") is None


def test_try_parse_zip_matches_valid(resolver: LocationResolver) -> None:
    assert resolver.try_parse_zip("10001") == "10001"


def test_require_iana_timezone_defaults_to_utc() -> None:
    assert LocationResolver.require_iana_timezone(None) == "UTC"
    assert LocationResolver.require_iana_timezone("") == "UTC"


def test_require_iana_timezone_passes_through_valid() -> None:
    assert LocationResolver.require_iana_timezone("America/New_York") == "America/New_York"


def test_timezone_for_returns_iana_string(resolver: LocationResolver) -> None:
    tz = resolver.timezone_for(40.7128, -74.0060)
    assert tz == "America/New_York"


def test_timezone_for_unknown_coordinates_returns_utc(
    resolver: LocationResolver, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(resolver.tz_finder, "timezone_at", lambda **_: None)
    assert resolver.timezone_for(0.0, 0.0) == "UTC"
